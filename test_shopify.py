
import os

import requests
from dotenv import load_dotenv

load_dotenv()

shop = os.environ["SHOPIFY_SHOP_DOMAIN"].strip()
client_id = os.environ["SHOPIFY_CLIENT_ID"]
client_secret = os.environ["SHOPIFY_CLIENT_SECRET"]

if not shop.endswith(".myshopify.com"):
    raise ValueError("Nieprawidłowa domena sklepu Shopify")

token_url = f"https://{shop}/admin/oauth/access_token"
graphql_url = f"https://{shop}/admin/api/2026-10/graphql.json"


query = """
query {
  orders(first: 10) {
    nodes {
      name
      customerJourneySummary {
        firstVisit {
          occurredAt
          source
          sourceDescription
          referrerUrl
          utmParameters {
            source
            medium
            campaign
            content
            term
          }
        }
        lastVisit {
          occurredAt
          source
          sourceDescription
          referrerUrl
          utmParameters {
            source
            medium
            campaign
            content
            term
          }
        }
      }
    }
  }
}
"""

 
try:
    # 1. Uzyskanie tokenu
    response = requests.post(
        token_url,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=20,
    )

    response.raise_for_status()
    token_data = response.json()

    access_token = token_data["access_token"]

    print("Połączenie z Shopify: OK")
    print("Uprawnienia:", token_data.get("scope"))
    print("Ważność tokenu:", token_data.get("expires_in"), "sekund")

    # 2. Zapytanie GraphQL
    graphql_response = requests.post(
        graphql_url,
        headers={
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json",
        },
        json={"query": query},
        timeout=20,
    )

    graphql_response.raise_for_status()
    result = graphql_response.json()

    if result.get("errors"):
        print("Błędy GraphQL:", result["errors"])

    elif result.get("data", {}).get("orders") is None:
        print("Brak danych zamówień.")
        print("Odpowiedź API:", result)

    else:
        orders = result["data"]["orders"]["nodes"]

        print("\nLiczba pobranych zamówień:", len(orders))

        
        for order in orders:
            print("\nZamówienie:", order["name"])

            journey = order.get("customerJourneySummary")

            if journey is None:
                print("Brak danych o źródle zamówienia.")
                continue

            for visit_type in ("firstVisit", "lastVisit"):
                visit = journey.get(visit_type)

                print(f"\n{visit_type}:")

                if visit is None:
                    print("Brak danych.")
                    continue

                print("Źródło:", visit.get("source"))
                print("Opis:", visit.get("sourceDescription"))
                print("Referrer:", visit.get("referrerUrl"))
                print("UTM:", visit.get("utmParameters"))

             
except requests.RequestException as exc:
    print("Błąd HTTP lub połączenia:", type(exc).__name__)
    if exc.response is not None:
        print("Status HTTP:", exc.response.status_code)
