
from decimal import Decimal

from django.db import transaction
from django.utils.dateparse import parse_datetime

from apps.core.models import Order, OrderItem
from apps.campaigns.models import Campaign
from apps.economics.models import (
    Transaction,
    TransactionType,
    TransactionCategory,
)
from apps.integrations.models import ShopifyConnection
from apps.integrations.shopify_client import ShopifyClient


def import_shopify_order(connection_id, external_id):
    connection = ShopifyConnection.objects.select_related(
        "sales_channel__label"
    ).get(id=connection_id)

    client = ShopifyClient(connection.shop_domain)

    query = """
    query GetOrder($id: ID!) {
        order(id: $id) {
            id
            name
            createdAt
            currencyCode
            displayFinancialStatus
            totalPriceSet {
                shopMoney {
                    amount
                    currencyCode
                }
            }
            customerJourneySummary {
                lastVisit {
                    source
                    utmParameters {
                        source
                        medium
                        campaign
                    }
                }
            }
            lineItems(first: 20) {
                nodes {
                    id
                    name
                    quantity
                    variant {
                        id
                    }
                    originalUnitPriceSet {
                        shopMoney {
                            amount
                            currencyCode
                        }
                    }
                }
            }
        }
    }
    """

    result = client.execute_query(
        query,
        variables={"id": external_id},
    )

    shopify_order = result["order"]

    if shopify_order is None:
        raise ValueError("Order not found in Shopify")

    created_at = parse_datetime(shopify_order["createdAt"])

    if created_at is None:
        raise ValueError("Invalid order date from Shopify")

    order_date = created_at.date()

    # Find a matching marketing campaign
    journey = shopify_order.get("customerJourneySummary") or {}
    last_visit = journey.get("lastVisit") or {}
    utm = last_visit.get("utmParameters") or {}
    utm_campaign = utm.get("campaign")

    matched_campaign = None

    if utm_campaign:
        matched_campaign = (
            Campaign.objects.filter(
                release__label=connection.sales_channel.label,
                utm_campaign=utm_campaign,
            )
            .order_by("id")
            .first()
        )

    with transaction.atomic():
        order, created = Order.objects.get_or_create(
            sales_channel=connection.sales_channel,
            external_id=shopify_order["id"],
            defaults={
                "label": connection.sales_channel.label,
                "order_date": order_date,
                "currency": shopify_order["currencyCode"],
                "notes": (
                    f"Imported from Shopify: "
                    f"{shopify_order['name']}"
                ),
            },
        )

        for item_data in shopify_order["lineItems"]["nodes"]:
            variant = item_data["variant"]

            OrderItem.objects.update_or_create(
                order=order,
                external_line_item_id=item_data["id"],
                defaults={
                    "product_name": item_data["name"],
                    "external_variant_id": (
                        variant["id"] if variant else ""
                    ),
                    "quantity": item_data["quantity"],
                    "unit_price": Decimal(
                        item_data["originalUnitPriceSet"]
                        ["shopMoney"]["amount"]
                    ),
                },
            )

        if shopify_order["displayFinancialStatus"] == "PAID":
            total = shopify_order["totalPriceSet"]["shopMoney"]

            Transaction.objects.update_or_create(
                order=order,
                defaults={
                    "label": connection.sales_channel.label,
                    "campaign": matched_campaign,
                    "transaction_type": TransactionType.INCOME,
                    "category": TransactionCategory.SALES,
                    "amount": Decimal(total["amount"]),
                    "currency": total["currencyCode"],
                    "date": order_date,
                    "description": (
                        f"Shopify order {shopify_order['name']}"
                    ),
                },
            )

    return order, created
