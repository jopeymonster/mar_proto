# -*- coding: utf-8 -*-
# meta_client.py

from typing import Optional, Any
import requests

class MetaAPIClient:
    BASE_URL = "https://graph.facebook.com/v24.0"

    def __init__(self, access_token: str, appsecret_proof: str):
        self.access_token = access_token
        self.appsecret_proof = appsecret_proof

    def get(
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
