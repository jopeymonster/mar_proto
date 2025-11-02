# -*- coding: utf-8 -*-
# main.py

import argparse
import os
import sys
from datetime import date, timedelta
from typing import cast
import auth
import accounts


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
    parser.add_argument(
        "--all-accounts",
        action="store_true",
        help="Retrieve all active ad accounts."
    )
    parser.add_argument(
        "--account-group",
        metavar="NAME",
        help="Get all accounts within the accounts_info.json indicated dictionary group."
    )
    parser.add_argument(
        "--accounts-file",
        metavar="PATH",
        help="Optional path to accounts_info.json. Default is package '/config' directory."
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
    client = auth.get_client(cast(auth.AuthDict,creds))
    try:
        me = client.get_auth("me", {"fields": "id,name"})
    except Exception as e:
        print(f"\nAuthentication failed:\n{e}")
    print("\nAuthenticated successfully!")
    print(f"User ID: {me['id']}")
    print(f"Name: {me['name']}")

    if args.all_accounts:
        print("\nFetching all available ad accounts...")
        ad_accounts = client.get_ad_accounts()
        active_accts = [aa for aa in ad_accounts if aa.get("account_status") == 1]
        selected_accounts = [f"act_{sa['account_id']}" for sa in active_accts if sa.get("account_id")]
        print(f"Found {len(active_accts)} ad accounts:\n")
        for acct in ad_accounts:
            print(f" - {acct.get('name', 'N/A')} ({acct.get('id')}) [status: {acct.get('account_status')}]")

    elif args.account_group:
        group = accounts.load_account_group(args.account_group, args.accounts_file)
        selected_accounts = accounts.normalize_group_ids(group)
        print(f"\nDiscovered {len(selected_accounts)} accounts from group '{args.account_group}':")
        for acct_name, raw_id in group.items():
            prefixed = raw_id if raw_id.startswith("act_") else f"act_{raw_id}"
            print(f" - {acct_name}: {prefixed}")
    else:
        sys.exit(
            "Error - specify either:\n"
            "  '--all-accounts' or '--account-group <name>'\n"
            "Use <name> as it is found within the accounts_info.json."
            )
            
    # get_insights test block
    test_input = input("Run insights report? (Y or N): ").lower().strip()
    if test_input == "y":
        if selected_accounts:
            print("\nTesting insights retrieval for first selected account...")
            first_account = selected_accounts[0]
            print(f"Requesting insights for: {first_account}")

            # Compute last 7 days
            today = date.today()
            seven_days_ago = today - timedelta(days=7)
            time_range = {"since": seven_days_ago.strftime("%Y-%m-%d"), "until": today.strftime("%Y-%m-%d")}

            try:
                insights = client.get_insights(
                    account_id=first_account,
                    time_range=time_range,
                    level="campaign",
                    fields=["campaign_id", "campaign_name", "impressions", "clicks", "spend"],
                )

                data = insights.get("data", [])
                print(f"Returned {len(data)} rows.")
                if data:
                    print(f"Sample:\n{data[0]}")
            except Exception as e:
                print(f"\nError fetching insights: {e}")
        else:
            print("Insight test skipped.")
            return
    else:
        sys.exit("User exited or error occured with insights report.")

if __name__ == "__main__":
    main()
