# -*- coding: utf-8 -*-
# ads_report.py

import sys
from typing import List, Dict
import common
import accounts
from meta_client import MetaAPIClient


def get_account_insights(
        client: MetaAPIClient,
        account_ids: List[str],
        group_map: Dict[str, str],
        time_range: Dict[str, str],
        level: str = "campaign",
        fields: List[str] | None = None,
) -> List[Dict[str, str]]:
    """Retrieve data for multiple ad accounts and merge results"""
    all_rows: List[Dict[str, str]] = []

    for acct_id in account_ids:
        acct_name = accounts.get_account_name_from_actid(acct_id, group_map)
        print(f"\nRetrieving insights for {acct_name} ({acct_id}) ...")

        try:
            response = client.get_insights(
                account_id=acct_id,
                time_range=time_range,
                level=level,
                fields=fields,
            )
            data = response.get("data", [])

            if not data:
                print(f" x - No data returned for {acct_name} ({acct_id}).")
                continue

            # append and normalize
            for row in data:
                row["account_id"] = acct_id
                row["account_name"] = acct_name
                row["mac"] = common.extract_mac(row.get("campaign_name","")) or ""
            all_rows.extend(data)
            print(f" + - Added {len(data)} rows from {acct_name} ({acct_id}).")

        except Exception as e:
            print(f"XX - Error fetching {acct_name} ({acct_id}): {e}")

    return all_rows

def run_insights_report(
        client: MetaAPIClient, 
        selected_accounts: List[str],
        group_name: str,
        accounts_file: str | None
) -> None:
    """Main reporting flow for insights."""
    if not selected_accounts:
        sys.exit("No accounts selected for insights retrieval.")

    # group match to accounts
    groups_map = accounts.load_account_group(group_name, accounts_file)

    # date range
    _, start_date, end_date, _ = common.get_timerange()
    time_range = {"since": str(start_date), "until": str(end_date)}

    print(f"\nTime Range: {time_range['since']} through {time_range['until']}\n")

    # metrics
    fields = [
        "account_name",
        "campaign_id",
        "campaign_name",
        "impressions",
        "clicks",
        "spend",
    ]

    # get data
    rows = get_account_insights(
        client, 
        selected_accounts,
        groups_map,
        time_range,
        level="campaign",
        fields=fields)

    if not rows:
        print("No results found.")
        return

    # normalize + output
    headers = list(rows[0].keys())
    table_data = [[row.get(h, "") for h in headers] for row in rows]

    common.data_handling_options(table_data, headers)