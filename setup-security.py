#!/usr/bin/env python3
"""
Setup script for security tools and pre-commit hooks.
Follows Python >=3.12 requirements and uses argparse for consistency.
"""

import argparse
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return success status."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def install_security_tools() -> bool:
    """Install required security tools."""
    tools = [
        "bandit[toml]",
        "safety",
        "semgrep",
        "pre-commit",
        "detect-secrets"
    ]
    
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade"] + tools
    return run_command(cmd, "Installing security tools")

def setup_pre_commit() -> bool:
    """Setup pre-commit hooks."""
    commands = [
        (["pre-commit", "install"], "Installing pre-commit hooks"),
        (["pre-commit", "install", "--hook-type", "commit-msg"], "Installing commit-msg hooks"),
        (["pre-commit", "install", "--hook-type", "pre-push"], "Installing pre-push hooks")
    ]
    
    for cmd, desc in commands:
        if not run_command(cmd, desc):
            return False
    return True

def initialize_secrets_baseline() -> bool:
    """Initialize secrets detection baseline."""
    baseline_file = Path(".secrets.baseline")
    if not baseline_file.exists():
        cmd = ["detect-secrets", "scan", "--baseline", ".secrets.baseline"]
        return run_command(cmd, "Creating secrets baseline")
    else:
        print("✅ Secrets baseline already exists")
        return True

def run_initial_scan() -> bool:
    """Run initial security scan."""
    commands = [
        (["bandit", "-r", ".", "--format", "screen"], "Running Bandit security scan"),
        (["safety", "check"], "Running Safety dependency check"),
        (["semgrep", "--config=auto", "."], "Running Semgrep static analysis")
    ]
    
    success = True
    for cmd, desc in commands:
        if not run_command(cmd, desc):
            success = False
            print(f"⚠️  {desc} found issues - check output above")
    
    return success

def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(
        description="Setup security tools and pre-commit hooks for Python projects"
    )
    parser.add_argument(
        "--skip-install", 
        action="store_true", 
        help="Skip installing security tools"
    )
    parser.add_argument(
        "--skip-scan", 
        action="store_true", 
        help="Skip initial security scan"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    print("🛡️  Setting up security tools for Python project...")
    
    success = True
    
    if not args.skip_install:
        success &= install_security_tools()
    
    success &= setup_pre_commit()
    success &= initialize_secrets_baseline()
    
    if not args.skip_scan:
        print("\n🔍 Running initial security scans...")
        scan_success = run_initial_scan()
        if not scan_success:
            print("\n⚠️  Security scans found issues. Review the output above.")
    
    if success:
        print("\n✅ Security setup completed successfully!")
        print("\nNext steps:")
        print("1. Review any security scan findings above")
        print("2. Commit your changes: git add . && git commit -m 'Add security tools'")
        print("3. Pre-commit hooks will now run automatically on each commit")
    else:
        print("\n❌ Setup completed with some errors. Please review the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()