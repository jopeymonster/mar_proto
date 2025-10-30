# -*- coding: utf-8 -*-
# auth.py

import hashlib
import hmac
import json
import os
import sys
import time
import requests
from meta_client import MetaAPIClient
from typing import TypedDict


class AuthDict(TypedDict):
    app_id: str
    app_secret: str
    access_token: str
    appsecret_proof: str | None
    cache_path: str | None


def generate_appsecret_proof(app_secret: str, access_token: str) -> str:
    """Compute appsecret_proof for secure server-side calls."""
    return hmac.new(
        app_secret.encode("utf-8"),
        msg=access_token.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()


def validate_token(app_id: str, app_secret: str, access_token: str, cache_path: str) -> dict:
    """Validate a Meta Graph API token and cache the response locally."""
    # Check cache validity (if less than 12h old)
    if os.path.exists(cache_path):
        with open(cache_path, "r") as f:
            cached = json.load(f)
        ts = cached.get("timestamp", 0)
        if (time.time() - ts) < 43200 and cached.get("is_valid") is True:
            return cached

    # Validate live token
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
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(data, f, indent=2)

    # if invalid, abort early
    if not data.get("is_valid"):
        sys.exit(
            "Access token is invalid or expired. "
            "Please regenerate a new token via Meta Business Manager."
        )

    return data


def load_auth_credentials(path: str) -> AuthDict:
    with open(path, "r") as f:
        data = json.load(f)
    auth_dict = data.get("auth_dict", {})
    required = ["app_id", "app_secret", "access_token"]
    for key in required:
        if not auth_dict.get(key):
            sys.exit(f"Error: Missing '{key}' in {path}")
    return auth_dict


def get_client(creds: AuthDict) -> MetaAPIClient:
    app_id = creds.get("app_id")
    app_secret = creds.get("app_secret")
    access_token = creds.get("access_token")
    proof = creds.get("appsecret_proof")
    cache_path = creds.get("cache_path")

    if not all(isinstance(x, str) and x for x in (app_id, app_secret, access_token)):
        sys.exit("Error: Missing one or more required credentials (app_id, app_secret, access_token).")

    safe_cache_path = cache_path or "config/token_validation.json"

    validation_data = validate_token(app_id, app_secret, access_token, safe_cache_path)
    print(f"\nValidated token for user_id: {validation_data.get('user_id')} ({validation_data.get('application')})")

    if not proof:
        proof = generate_appsecret_proof(app_secret, access_token)

    return MetaAPIClient(access_token=access_token, appsecret_proof=proof)

