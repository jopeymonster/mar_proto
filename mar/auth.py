# -*- coding: utf-8 -*-
# auth.py

import hashlib
import hmac
import json
import os
import sys
import time
from pathlib import Path
import requests

from typing import TypedDict, Union

from meta_client import MetaAPIClient
import common

class AuthDict(TypedDict):
    app_id: str
    app_secret: str
    access_token: str
    appsecret_proof: str | None
    cache_path: str | None


def load_auth_credentials(path: str) -> AuthDict:
    with open(path, "r") as f:
        data = json.load(f)
    auth_dict = data.get("auth_dict", {})
    required = ["app_id", "app_secret", "access_token"]
    for key in required:
        if not auth_dict.get(key):
            sys.exit(f"Error: Missing '{key}' in {path}")
    return auth_dict

def token_cache_path(cache_path: str | None) -> Path:
    """Resolve a user-supplied cache path to an absolute path under the package config dir.
    If None, use DEFAULT_CACHE_PATH."""
    if not cache_path:
        return common.DEFAULT_CACHE_PATH
    p = Path(cache_path)
    if p.is_absolute():
        return p
    # relative paths = relative to the package config dir
    return common.DEFAULT_CONFIG_DIR / p

def generate_appsecret_proof(app_secret: str, access_token: str) -> str:
    """Compute appsecret_proof for secure server-side calls."""
    return hmac.new(
        app_secret.encode("utf-8"),
        msg=access_token.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()


def validate_token(app_id: str, app_secret: str, access_token: str, cache_path: Union[str, Path]) -> dict:
    """Validate a Meta Graph API token and cache the response locally in package /config/ directory."""
    cache_path = Path(cache_path)

    # cache validity (if less than 12h old)
    if cache_path.exists():
        try:
            cached = json.loads(cache_path.read_text())
            ts = cached.get("timestamp", 0)
            if (time.time() - ts) < 43200 and cached.get("is_valid") is True:
                return cached
        except Exception:
            pass # fallback to live validation

    # validate live token
    app_access_token = f"{app_id}|{app_secret}"
    url = "https://graph.facebook.com/v24.0/debug_token"
    params = {
        "input_token": access_token,
        "access_token": app_access_token,
    }

    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json().get("data", {})
    except Exception as e:
        sys.exit(f"Error validating token: {e}")

    # check validation result
    data["timestamp"] = time.time()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(data, indent=2))
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)

    # if invalid, abort early
    if not data.get("is_valid"):
        sys.exit(
            "\nAccess token is invalid or expired. \n"
            "Please regenerate a new token via Meta Business Manager.\n"
        )

    return data


def get_client(creds: AuthDict) -> MetaAPIClient:
    app_id = creds.get("app_id")
    app_secret = creds.get("app_secret")
    access_token = creds.get("access_token")
    proof = creds.get("appsecret_proof")
    cache_path_raw = creds.get("cache_path") # override if needed

    if not all(isinstance(x, str) and x for x in (app_id, app_secret, access_token)):
        sys.exit("Error: Missing one or more required credentials (app_id, app_secret, access_token).")

    cache_path = token_cache_path(cache_path_raw)

    validation_data = validate_token(app_id, app_secret, access_token, cache_path)
    print(f"\nValidated token for user_id: {validation_data.get('user_id')}" 
          f"({validation_data.get('application')})")

    if not proof:
        proof = generate_appsecret_proof(app_secret, access_token)

    return MetaAPIClient(access_token=access_token, appsecret_proof=proof)

