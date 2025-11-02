# -*- coding: utf-8 -*-
# accounts.py

import json
import sys
from pathlib import Path
from typing import Dict, List

import common
from meta_client import MetaAPIClient

def default_accounts_path() -> Path:
    return common.DEFAULT_CONFIG_DIR / "accounts_info.json"


def load_accounts_file(path: str | None) -> Dict[str, Dict[str, str]]:
    """Load accounts.json from a provided path or from the default package config dir."""
    file_path = Path(path) if path else default_accounts_path()
    if not file_path.exists():
        sys.exit(f"Error: accounts.json file not found at: {file_path}")
    try:
        data = json.loads(file_path.read_text())
    except Exception as e:
        sys.exit(f"Error reading accounts file: {e}")
    if not isinstance(data, dict) or not data:
        sys.exit("Error: accounts.json must be a non-empty object of groups.")
    return data


def load_account_group(group_name: str, path: str | None) -> Dict[str, str]:
    """Return the dict of label -> account_id for the given group"""
    all_groups = load_accounts_file(path)
    group = all_groups.get(group_name)
    if not isinstance(group, dict) or not group:
        sys.exit(f"Error: account group '{group_name}' not found or empty.")
    return group


def normalize_act_id(account_id: str) -> str:
    """Ensure account id is in act_<id> fomrat for requests"""
    actid = account_id.strip()
    return actid if actid.startswith("act_") else f"act_{actid}"


def normalize_group_ids(group: Dict[str, str]) -> List[str]:
    """Returns a list of normalized act_<id> strings from group map"""
    return [normalize_act_id(v) for v in group.values()]