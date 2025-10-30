# -*- coding: utf-8 -*-
# main.py

import argparse
import os
import sys
from typing import cast
import auth
from auth import AuthDict


def parse_args() -> argparse.Namespace:
    """Handle CLI arguments."""
    parser = argparse.ArgumentParser(
        prog="Meta Ads Reporter",
        description="Authenticate and connect to Meta Graph API reporting endpoints.",
    )
    parser.add_argument(
        "--config",
        metavar="PATH",
        help="Path to JSON config file containing auth credentials.",
    )
    return parser.parse_args()


def resolve_config_path(cli_path: str | None) -> str:
    """Resolve config file path from CLI or prompt."""
    if cli_path and os.path.exists(cli_path):
        return cli_path
    if cli_path:
        sys.exit(f"Error: Provided config path not found: {cli_path}")

    manual_path = input("Enter the path to your config JSON file (or type 'exit'): ").strip()
    if manual_path.lower() == "exit":
        sys.exit("Exited by user.")
    if manual_path and os.path.exists(manual_path):
        return manual_path

    sys.exit(
        "No valid configuration file provided. "
        "Use --config <path> or see README for setup instructions."
    )


def main():
    print("=== Meta Ads Reporter ===")
    args = parse_args()
    config_path = resolve_config_path(args.config)
    creds = auth.load_auth_credentials(config_path)

    client = auth.get_client(cast(AuthDict,creds))

    try:
        me = client.get("me", {"fields": "id,name"})
        print("\nAuthenticated successfully!")
        print(f"User ID: {me['id']}")
        print(f"Name: {me['name']}")
    except Exception as e:
        print(f"\nAuthentication failed:\n{e}")


if __name__ == "__main__":
    main()
