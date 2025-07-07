#!/usr/bin/env python3
"""
MCP Server Configuration Synchronizer

This script reads hardcoded JSON MCP server configuration files,
combines all unique MCP servers, and replaces all original files
with the unified configuration.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

# from dotenv import load_dotenv
import logging

# Load environment variables
# load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Hardcoded list of MCP configuration files
MCP_CONFIG_FILES = [
    "~/.aws/amazonq/mcp.json",
    "~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json",
    "~/Library/Application Support/Claude/claude_desktop_config.json",
    # Add more paths as needed
]


class MCPServerSync:
    """Handles synchronization of MCP server configurations across tools."""

    def __init__(self, backup: bool = True):
        """
        Initialize the MCP Server Synchronizer.

        Args:
            backup: Whether to create backups before modifying files
        """
        self.backup = backup
        self.mcp_servers: Dict[str, Dict[str, Any]] = {}
        self.config_files: List[Path] = []
        self.existing_files: List[Path] = []

    def discover_config_files(self) -> List[Path]:
        """
        Check which hardcoded configuration files exist.

        Returns:
            List of Path objects for existing JSON configuration files
        """
        existing_files = []

        for file_path in MCP_CONFIG_FILES:
            expanded_path = Path(file_path).expanduser()
            if expanded_path.exists() and expanded_path.is_file():
                existing_files.append(expanded_path)
                logger.debug(f"Found existing config: {expanded_path}")
            else:
                logger.debug(f"Config file not found: {expanded_path}")

        self.existing_files = existing_files
        self.config_files = MCP_CONFIG_FILES  # Keep all paths for potential creation

        logger.info(
            f"Found {len(existing_files)} existing configuration files out of {len(MCP_CONFIG_FILES)} total"
        )

        return existing_files

    def parse_config_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse a JSON configuration file.

        Args:
            file_path: Path to the JSON configuration file

        Returns:
            Parsed JSON configuration as dictionary
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                logger.debug(f"Successfully parsed: {file_path}")
                return config
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return {}

    def extract_mcp_servers(
        self, config: Dict[str, Any], source_file: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extract MCP server configurations from a parsed config.

        Args:
            config: Parsed configuration dictionary
            source_file: Source file name for logging

        Returns:
            Dictionary of MCP server configurations
        """
        servers = {}

        # Look for mcpServers key specifically
        if "mcpServers" in config and isinstance(config["mcpServers"], dict):
            servers.update(config["mcpServers"])
            logger.debug(f"Found {len(config['mcpServers'])} servers in {source_file}")
        else:
            logger.debug(f"No mcpServers found in {source_file}")

        return servers

    def combine_mcp_servers(self) -> None:
        """
        Combine MCP servers from all existing configuration files.
        """
        all_servers = {}
        server_sources = {}

        for config_file in self.existing_files:
            config = self.parse_config_file(config_file)
            if not config:
                continue

            servers = self.extract_mcp_servers(config, config_file.name)

            for server_name, server_config in servers.items():
                if server_name in all_servers:
                    # Check if configurations are identical
                    if all_servers[server_name] != server_config:
                        logger.warning(
                            f"Conflicting configuration for server '{server_name}' "
                            f"between {server_sources[server_name]} and {config_file.name}"
                        )
                        # Use the more complete configuration (more keys)
                        if len(server_config) > len(all_servers[server_name]):
                            all_servers[server_name] = server_config
                            server_sources[server_name] = config_file.name
                            logger.info(
                                f"Updated '{server_name}' with config from {config_file.name}"
                            )
                    else:
                        logger.debug(
                            f"Duplicate server '{server_name}' found in {config_file.name} (identical config)"
                        )
                else:
                    all_servers[server_name] = server_config
                    server_sources[server_name] = config_file.name

        self.mcp_servers = all_servers
        logger.info(f"Combined {len(self.mcp_servers)} unique MCP servers")

        # Log server summary
        for server_name, source in server_sources.items():
            logger.debug(f"Server '{server_name}' from {source}")

    def generate_unified_config(self) -> Dict[str, Any]:
        """
        Generate a unified configuration with all MCP servers.

        Returns:
            Unified configuration dictionary
        """
        unified_config = {
            "mcpServers": self.mcp_servers,
            # "version": "1.0.0",
            # "generatedBy": "mcp-server-sync",
            # "generatedAt": None,  # Will be set when writing
        }

        return unified_config

    def create_backup(self, file_path: Path) -> Path:
        """
        Create a backup of the configuration file.

        Args:
            file_path: Path to the file to backup

        Returns:
            Path to the backup file
        """
        backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
        backup_path.write_text(file_path.read_text(encoding="utf-8"), encoding="utf-8")
        logger.debug(f"Created backup: {backup_path}")
        return backup_path

    def write_unified_config(
        self, file_path: Path, unified_config: Dict[str, Any]
    ) -> bool:
        """
        Write the unified configuration to a file.

        Args:
            file_path: Path to write the configuration
            unified_config: Unified configuration dictionary

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Add timestamp
            from datetime import datetime

            # unified_config["generatedAt"] = datetime.utcnow().isoformat() + "Z"

            # Create backup if file exists and backup is enabled
            if self.backup and file_path.exists():
                self.create_backup(file_path)

            # Write unified configuration
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(unified_config, f, indent=2, ensure_ascii=False)

            logger.info(f"Successfully wrote unified config to: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error writing unified config to {file_path}: {e}")
            return False

    def replace_all_configs(self) -> Dict[str, bool]:
        """
        Replace all configuration files with the unified configuration.

        Returns:
            Dictionary mapping file paths to write success status
        """
        if not self.mcp_servers:
            logger.error("No MCP servers found to write")
            return {}

        unified_config = self.generate_unified_config()
        results = {}

        # Write to all configured file paths (both existing and new)
        for file_path_str in MCP_CONFIG_FILES:
            file_path = Path(file_path_str).expanduser()
            success = self.write_unified_config(file_path, unified_config.copy())
            results[str(file_path)] = success

        successful_writes = sum(results.values())
        logger.info(
            f"Successfully wrote unified config to {successful_writes}/{len(results)} files"
        )

        return results

    def remove_mcp_server(self, server_key: str) -> bool:
        """
        Remove an MCP server from all configuration files.

        Args:
            server_key: The server key/name to remove

        Returns:
            True if server was found and removed, False otherwise
        """
        if server_key not in self.mcp_servers:
            logger.warning(f"Server '{server_key}' not found in current configuration")
            return False

        # Remove from combined servers
        del self.mcp_servers[server_key]
        logger.info(f"Removed server '{server_key}' from configuration")

        # Update all config files
        unified_config = self.generate_unified_config()
        results = {}

        for file_path_str in MCP_CONFIG_FILES:
            file_path = Path(file_path_str).expanduser()
            if file_path.exists():
                success = self.write_unified_config(file_path, unified_config.copy())
                results[str(file_path)] = success

        successful_writes = sum(results.values())
        total_files = len(
            [f for f in results.keys()]
        )  # Only count files that were processed
        logger.info(
            f"Successfully updated {successful_writes}/{total_files} files after removal"
        )

        return True

    def list_all_servers(self) -> None:
        """List all MCP servers found in configuration files."""
        print("\n" + "=" * 60)
        print("ALL MCP SERVERS")
        print("=" * 60)

        if not self.mcp_servers:
            print("\nNo MCP servers found in any configuration files.")
            return

        print(f"\nFound {len(self.mcp_servers)} MCP servers:")
        print("-" * 40)

        for server_name, server_config in sorted(self.mcp_servers.items()):
            print(f"\n🔧 Server: {server_name}")
            if isinstance(server_config, dict):
                # Show key configuration details
                if "command" in server_config:
                    print(f"   Command: {server_config['command']}")
                if "args" in server_config and isinstance(server_config["args"], list):
                    print(f"   Args: {' '.join(server_config['args'])}")
                if "env" in server_config and isinstance(server_config["env"], dict):
                    env_vars = list(server_config["env"].keys())
                    print(f"   Environment Variables: {', '.join(env_vars)}")

                # Show all other keys
                other_keys = [
                    k
                    for k in server_config.keys()
                    if k not in ["command", "args", "env"]
                ]
                if other_keys:
                    for key in other_keys:
                        value = server_config[key]
                        if isinstance(value, (str, int, bool)):
                            print(f"   {key.capitalize()}: {value}")
                        elif isinstance(value, list):
                            print(
                                f"   {key.capitalize()}: [{', '.join(map(str, value))}]"
                            )
                        elif isinstance(value, dict):
                            print(f"   {key.capitalize()}: {{{len(value)} items}}")
                        else:
                            print(f"   {key.capitalize()}: {type(value).__name__}")

        print("\n" + "=" * 60)
        print(f"Total: {len(self.mcp_servers)} servers")
        print("=" * 60)

    def print_summary(self) -> None:
        """Print a summary of discovered MCP servers and file operations."""
        print("\n" + "=" * 60)
        print("MCP SERVER SYNCHRONIZATION SUMMARY")
        print("=" * 60)

        print(f"\nConfigured File Paths: {len(MCP_CONFIG_FILES)}")
        for file_path in MCP_CONFIG_FILES:
            expanded_path = Path(file_path).expanduser()
            status = "✓ EXISTS" if expanded_path.exists() else "✗ MISSING"
            print(f"  {status} {file_path}")

        print(f"\nExisting Files Found: {len(self.existing_files)}")
        for config_file in self.existing_files:
            print(f"  - {config_file}")

        print(f"\nCombined MCP Servers: {len(self.mcp_servers)}")
        for server_name, server_config in self.mcp_servers.items():
            print(f"\n  Server: {server_name}")
            if isinstance(server_config, dict):
                for key, value in server_config.items():
                    if isinstance(value, (str, int, bool)):
                        print(f"    {key}: {value}")
                    elif isinstance(value, list):
                        print(f"    {key}: [{', '.join(map(str, value))}]")
                    elif isinstance(value, dict):
                        print(f"    {key}: {{{len(value)} items}}")
                    else:
                        print(f"    {key}: {type(value).__name__}")

        print("\n" + "=" * 60)


def main():
    """Main function to handle command line arguments and execute synchronization."""
    parser = argparse.ArgumentParser(
        description="Synchronize MCP server configurations across hardcoded tool configuration files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
This script reads from hardcoded JSON configuration files, combines all unique
MCP servers, and replaces all original files with the unified configuration.

Configured files:
  {MCP_CONFIG_FILES}

Examples:
  %(prog)s                           # Sync all MCP servers
  %(prog)s --list-all               # List all MCP servers
  %(prog)s --remove server-name     # Remove a specific server
  %(prog)s --no-backup              # Skip creating backups
  %(prog)s --verbose --dry-run      # Preview changes
        """,
    )

    # Action arguments (mutually exclusive)
    action_group = parser.add_mutually_exclusive_group()

    action_group.add_argument(
        "--list-all",
        action="store_true",
        help="List all MCP servers found in configuration files",
    )

    action_group.add_argument(
        "--remove",
        metavar="SERVER_KEY",
        help="Remove the specified MCP server from all configuration files",
    )

    # Option arguments
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating backup files before modification",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes (not applicable to --list-all)",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Initialize synchronizer
        syncer = MCPServerSync(backup=not args.no_backup)

        # Discover existing configuration files
        existing_files = syncer.discover_config_files()

        if not existing_files:
            logger.warning("No existing configuration files found")
            if not args.list_all:
                logger.info(
                    "Will create new configuration files with any MCP servers found"
                )

        # Combine MCP servers from existing configs
        syncer.combine_mcp_servers()

        # Handle list-all action
        if args.list_all:
            syncer.list_all_servers()
            return

        # Handle remove action
        if args.remove:
            if not syncer.mcp_servers:
                logger.error("No MCP servers found in any existing configuration files")
                sys.exit(1)

            if args.dry_run:
                if args.remove in syncer.mcp_servers:
                    print(
                        f"\n[DRY RUN] Would remove server '{args.remove}' from all configuration files"
                    )
                    print(f"Server '{args.remove}' is currently configured with:")
                    server_config = syncer.mcp_servers[args.remove]
                    for key, value in server_config.items():
                        print(f"  {key}: {value}")
                    print(
                        f"After removal, {len(syncer.mcp_servers) - 1} servers would remain"
                    )
                else:
                    print(
                        f"\n[DRY RUN] Server '{args.remove}' not found in current configuration"
                    )
                return

            # Store count before removal for accurate reporting
            servers_before = len(syncer.mcp_servers)
            success = syncer.remove_mcp_server(args.remove)
            servers_after = len(syncer.mcp_servers)

            if success:
                print(
                    f"\n✅ Successfully removed server '{args.remove}' from all configuration files"
                )
                print(f"   Servers before removal: {servers_before}")
                print(f"   Servers after removal: {servers_after}")
            else:
                print(
                    f"\n❌ Failed to remove server '{args.remove}' - server not found"
                )
                sys.exit(1)
            return

        # Default sync action
        if not syncer.mcp_servers:
            logger.error("No MCP servers found in any existing configuration files")
            logger.info("Nothing to synchronize")
            sys.exit(1)

        # Print summary
        syncer.print_summary()

        if args.dry_run:
            print("\n[DRY RUN] No files were modified")
            print(f"Would write unified config to {len(MCP_CONFIG_FILES)} files")
            return

        # Replace all configurations with unified config
        results = syncer.replace_all_configs()

        # Print results
        failed_writes = [path for path, success in results.items() if not success]
        if failed_writes:
            print(f"\nFailed to write {len(failed_writes)} files:")
            for path in failed_writes:
                print(f"  - {path}")
            sys.exit(1)
        else:
            print(
                f"\n✅ Successfully wrote unified MCP configuration to all {len(results)} files"
            )
            print(f"   Combined {len(syncer.mcp_servers)} unique MCP servers")

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
