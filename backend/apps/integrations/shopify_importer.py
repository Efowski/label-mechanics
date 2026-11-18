
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
            refunds(first: 50) {
                id
                createdAt
                totalRefundedSet {
                    shopMoney {
                        amount
                        currencyCode
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
    label = connection.sales_channel.label

    # Match marketing campaign by UTM
    journey = shopify_order.get("customerJourneySummary") or {}
    last_visit = journey.get("lastVisit") or {}
    utm = last_visit.get("utmParameters") or {}
    utm_campaign = utm.get("campaign")

    matched_campaign = None

    if utm_campaign:
        campaigns = Campaign.objects.filter(
            release__label=label,
            utm_campaign=utm_campaign,
        )[:2]

        # Do not attribute ambiguous UTM campaigns
        if len(campaigns) == 1:
            matched_campaign = campaigns[0]

    # Only a simplified financial status is supported for now
    financial_status = shopify_order["displayFinancialStatus"]
    supported_statuses = {"PAID", "PARTIALLY_REFUNDED", "REFUNDED"}

    if financial_status not in supported_statuses:
        raise ValueError(
            f"Unsupported Shopify financial status: {financial_status}"
        )

    refunds = shopify_order.get("refunds") or []

    with transaction.atomic():
        order, created = Order.objects.get_or_create(
            sales_channel=connection.sales_channel,
            external_id=shopify_order["id"],
            defaults={
                "label": label,
                "order_date": order_date,
                "currency": shopify_order["currencyCode"],
                "notes": (
                    f"Imported from Shopify: "
                    f"{shopify_order['name']}"
                ),
            },
        )

        # Synchronize order items
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

        # Original sale
        total = shopify_order["totalPriceSet"]["shopMoney"]

        sale_external_id = f"{shopify_order['id']}:sale"

        # Migrate the existing sale record if it has no external ID
        legacy_sales = Transaction.objects.filter(
            order=order,
            transaction_type=TransactionType.INCOME,
            source="",
            external_id__isnull=True,
        )

        if legacy_sales.count() == 1:
            legacy_sale = legacy_sales.first()
            legacy_sale.source = "shopify"
            legacy_sale.external_id = sale_external_id
            legacy_sale.save(
                update_fields=["source", "external_id"]
            )

        Transaction.objects.update_or_create(
            order=order,
            source="shopify",
            external_id=sale_external_id,
            defaults={
                "label": label,
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

        # Refunds are separate financial transactions
        for refund_data in refunds:
            refunded = refund_data["totalRefundedSet"]["shopMoney"]

            refunded_at = parse_datetime(
                refund_data["createdAt"]
            )

            if refunded_at is None:
                raise ValueError("Invalid Shopify refund date")

            Transaction.objects.update_or_create(
                order=order,
                source="shopify",
                external_id=refund_data["id"],
                defaults={
                    "label": label,
                    "campaign": matched_campaign,
                    "transaction_type": TransactionType.EXPENSE,
                    "category": TransactionCategory.SALES,
                    "amount": Decimal(refunded["amount"]),
                    "currency": refunded["currencyCode"],
                    "date": refunded_at.date(),
                    "description": (
                        f"Shopify refund for "
                        f"{shopify_order['name']}"
                    ),
                },
            )

    return order, created
