#!/usr/bin/env python3
"""
Security utilities for preventing path traversal and other file system attacks.
Follows Python >=3.12 requirements and includes comprehensive path validation.
"""

import os
import re
from pathlib import Path, PurePath
from typing import Union, Optional
from urllib.parse import unquote


class PathTraversalError(Exception):
    """Raised when a path traversal attempt is detected."""
    pass


class SecurePathValidator:
    """Utility class for validating and sanitizing file paths."""
    
    # Dangerous path patterns
    DANGEROUS_PATTERNS = [
        r'\.\./',           # Parent directory traversal
        r'\.\.\.',          # Multiple dots
        r'~/',              # Home directory
        r'/etc/',           # System directories
        r'/proc/',          # Process filesystem
        r'/sys/',           # System filesystem
        r'\\',              # Windows path separators
        r'\x00',            # Null bytes
        r'[<>:"|?*]',       # Invalid filename characters
    ]
    
    # Compiled regex patterns for performance
    _compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in DANGEROUS_PATTERNS]
    
    @classmethod
    def is_safe_path(cls, path: Union[str, Path], allowed_base: Optional[Union[str, Path]] = None) -> bool:
        """
        Check if a path is safe from traversal attacks.
        
        Args:
            path: The path to validate
            allowed_base: Optional base directory to restrict access to
            
        Returns:
            True if path is safe, False otherwise
        """
        if not path:
            return False
            
        # Convert to string and decode URL encoding
        path_str = str(path)
        path_str = unquote(path_str)
        
        # Check for dangerous patterns
        for pattern in cls._compiled_patterns:
            if pattern.search(path_str):
                return False
        
        # Additional checks for resolved path
        try:
            resolved_path = Path(path_str).resolve()
            
            # Check if path stays within allowed base
            if allowed_base:
                base_path = Path(allowed_base).resolve()
                try:
                    resolved_path.relative_to(base_path)
                except ValueError:
                    return False
            
            # Check for suspicious absolute paths
            if resolved_path.is_absolute():
                dangerous_roots = ['/etc', '/proc', '/sys', '/dev', '/root']
                for root in dangerous_roots:
                    if str(resolved_path).startswith(root):
                        return False
                        
        except (OSError, ValueError):
            return False
            
        return True
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """
        Sanitize a filename by removing dangerous characters.
        
        Args:
            filename: The filename to sanitize
            
        Returns:
            Sanitized filename
        """
        if not filename:
            raise ValueError("Filename cannot be empty")
        
        # Remove path separators and dangerous characters
        sanitized = re.sub(r'[<>:"|?*\\/]', '_', filename)
        sanitized = re.sub(r'\.\.+', '.', sanitized)  # Multiple dots
        sanitized = sanitized.strip('. ')  # Leading/trailing dots and spaces
        
        # Ensure filename isn't empty after sanitization
        if not sanitized:
            raise ValueError("Filename becomes empty after sanitization")
            
        # Limit length
        if len(sanitized) > 255:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:255-len(ext)] + ext
            
        return sanitized
    
    @classmethod
    def secure_join(cls, base: Union[str, Path], *paths: str) -> Path:
        """
        Securely join paths, ensuring the result stays within the base directory.
        
        Args:
            base: Base directory path
            *paths: Path components to join
            
        Returns:
            Secure joined path
            
        Raises:
            PathTraversalError: If path traversal is detected
        """
        base_path = Path(base).resolve()
        
        # Sanitize and join all path components
        sanitized_parts = []
        for path_part in paths:
            if not cls.is_safe_path(path_part):
                raise PathTraversalError(f"Unsafe path component: {path_part}")
            sanitized_parts.append(cls.sanitize_filename(str(path_part)))
        
        # Join paths
        result_path = base_path
        for part in sanitized_parts:
            result_path = result_path / part
        
        # Resolve and validate final path
        try:
            resolved_result = result_path.resolve()
            resolved_result.relative_to(base_path)
        except ValueError:
            raise PathTraversalError(f"Path traversal detected: {result_path}")
        
        return resolved_result


def secure_open(filepath: Union[str, Path], mode: str = 'r', 
                allowed_base: Optional[Union[str, Path]] = None, **kwargs):
    """
    Securely open a file with path traversal protection.
    
    Args:
        filepath: Path to the file
        mode: File open mode
        allowed_base: Optional base directory to restrict access to
        **kwargs: Additional arguments for open()
        
    Returns:
        File object
        
    Raises:
        PathTraversalError: If path traversal is detected
        FileNotFoundError: If file doesn't exist (for read modes)
    """
    if not SecurePathValidator.is_safe_path(filepath, allowed_base):
        raise PathTraversalError(f"Unsafe file path: {filepath}")
    
    # Additional validation for write modes
    if 'w' in mode or 'a' in mode:
        parent_dir = Path(filepath).parent
        if not SecurePathValidator.is_safe_path(parent_dir, allowed_base):
            raise PathTraversalError(f"Unsafe parent directory: {parent_dir}")
    
    return open(filepath, mode, **kwargs)


def secure_file_operation(operation: str, filepath: Union[str, Path], 
                         allowed_base: Optional[Union[str, Path]] = None, **kwargs):
    """
    Perform secure file operations with path validation.
    
    Args:
        operation: Operation to perform ('remove', 'chmod', 'stat', etc.)
        filepath: Path to the file
        allowed_base: Optional base directory to restrict access to
        **kwargs: Additional arguments for the operation
        
    Returns:
        Result of the operation
        
    Raises:
        PathTraversalError: If path traversal is detected
    """
    if not SecurePathValidator.is_safe_path(filepath, allowed_base):
        raise PathTraversalError(f"Unsafe file path: {filepath}")
    
    # Map operations to functions
    operations = {
        'remove': os.remove,
        'unlink': os.unlink,
        'chmod': os.chmod,
        'stat': os.stat,
        'exists': os.path.exists,
        'isfile': os.path.isfile,
        'isdir': os.path.isdir,
    }
    
    if operation not in operations:
        raise ValueError(f"Unsupported operation: {operation}")
    
    return operations[operation](filepath, **kwargs)


# Example usage and testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test secure path validation")
    parser.add_argument("path", help="Path to test")
    parser.add_argument("--base", help="Base directory for validation")
    
    args = parser.parse_args()
    
    try:
        is_safe = SecurePathValidator.is_safe_path(args.path, args.base)
        print(f"Path '{args.path}' is {'SAFE' if is_safe else 'UNSAFE'}")
        
        if is_safe and args.base:
            secure_path = SecurePathValidator.secure_join(args.base, args.path)
            print(f"Secure joined path: {secure_path}")
            
    except Exception as e:
        print(f"Error: {e}")