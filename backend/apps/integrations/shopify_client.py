
import requests
from django.conf import settings


class ShopifyClient:
    API_VERSION = "2026-10"

    def __init__(self, shop_domain):
        self.shop_domain = shop_domain

    def get_access_token(self):
        url = (
            f"https://{self.shop_domain}"
            "/admin/oauth/access_token"
        )

        response = requests.post(
            url,
            data={
                "grant_type": "client_credentials",
                "client_id": settings.SHOPIFY_CLIENT_ID,
                "client_secret": settings.SHOPIFY_CLIENT_SECRET,
            },
            timeout=30,
        )
        response.raise_for_status()

        return response.json()["access_token"]

    def execute_query(self, query, variables=None):
        token = self.get_access_token()

        url = (
            f"https://{self.shop_domain}"
            f"/admin/api/{self.API_VERSION}/graphql.json"
        )

        response = requests.post(
            url,
            headers={
                "X-Shopify-Access-Token": token,
            },
            json={
                "query": query,
                "variables": variables or {},
            },
            timeout=30,
        )
        response.raise_for_status()

        result = response.json()

        if result.get("errors"):
            raise RuntimeError(result["errors"])

        return result["data"]
