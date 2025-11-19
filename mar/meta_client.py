# -*- coding: utf-8 -*-
# meta_client.py

import json
from typing import Optional, Any
import requests

class MetaAPIClient:
    BASE_URL = "https://graph.facebook.com/v24.0"

    def __init__(self, access_token: str, appsecret_proof: str):
        self.access_token = access_token
        self.appsecret_proof = appsecret_proof

    def get_auth(
        self,
        endpoint: str,
        params: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Perform a GET request with auth."""
        if params is None:
            params = {}

        params.update({
            "access_token": self.access_token,
            "appsecret_proof": self.appsecret_proof,
        })

        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        response: requests.Response = requests.get(url, params=params)
        response.raise_for_status()

        return response.json()

    def get_ad_accounts(self, fields: list[str] | None = None, limit: int = 50) -> list[dict]:
        """Return all ad accounts accessible to the token."""
        endpoint = "me/adaccounts"
        params: dict[str, Any] = {
            "access_token": self.access_token,
            "appsecret_proof": self.appsecret_proof,
            "limit": limit,
            "fields": ",".join(fields) if fields else "id,account_id,name,account_status",
        }

        results: list[dict[str, Any]] = []
        next_url: str | None = f"{self.BASE_URL}/{endpoint}"

        while next_url:
            response: requests.Response = requests.get(next_url, params=params)
            response.raise_for_status()
            data = response.json()

            accounts = data.get("data", [])
            results.extend(accounts)

            # pagination
            paging = data.get("paging", {})
            next_url = paging.get("next")

            # include token params on the first request only
            params = {}

        return results
    
    def get_insights(
        self,
        account_id: str,
        fields: list[str] | None = None,
        date_preset: str | None = None,
        time_range: dict[str, str] | None = None,
        level: str = "campaign",
        limit: int = 100,
        time_increment: str | None = None,
    ) -> dict:
        """Retrieve all insights for a given ad account."""
        endpoint = f"{account_id}/insights"

        base_params: dict[str, Any] = {
            "access_token": self.access_token,
            "appsecret_proof": self.appsecret_proof,
            "level": level,
            "limit": limit,
        }

        # date filters
        if date_preset:
            base_params["date_preset"] = date_preset  # 'last_7d', 'this_month'
        elif time_range:
            # normalize date formats to YYYY-MM-DD (Meta requires ISO format)
            fixed_range = {
                "since": str(time_range.get("since")).replace("-", ""),
                "until": str(time_range.get("until")).replace("-", "")
            }
            # reformat if YYYYMMDD
            for key, val in fixed_range.items():
                if len(val) == 8 and "-" not in val:
                    fixed_range[key] = f"{val[0:4]}-{val[4:6]}-{val[6:8]}"
            base_params["time_range"] = json.dumps(fixed_range)
        else:
            base_params["date_preset"] = "last_7d"

        # metrics fields (default)
        if fields:
            base_params["fields"] = ",".join(fields)
        else:
            base_params["fields"] = "account_id,campaign_id,campaign_name,impressions,clicks,spend"

        if time_increment:
            base_params["time_increment"] = time_increment

        url = f"{self.BASE_URL}/{endpoint}"
        insights_data: list[dict[str, Any]] = []
        while url:
            response = requests.get(url, params=base_params)
            response.raise_for_status()
            response_data = response.json()

            insights_data.extend(response_data.get("data", []))
            paging = response_data.get("paging", {})
            url = paging.get("next") # MetaAPI includes next-page URL

        return {"data": insights_data}