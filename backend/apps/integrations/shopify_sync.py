
from datetime import timedelta

from django.utils import timezone

from apps.integrations.models import ShopifyConnection
from apps.integrations.shopify_client import ShopifyClient
from apps.integrations.shopify_importer import import_shopify_order


def sync_shopify_orders(connection_id):
    connection = ShopifyConnection.objects.get(
        id=connection_id,
        is_active=True,
    )

    client = ShopifyClient(connection.shop_domain)

    query = """
    query GetOrders($cursor: String, $search: String) {
        orders(
            first: 50
            after: $cursor
            sortKey: UPDATED_AT
            query: $search
        ) {
            nodes {
                id
                name
                updatedAt
            }
            pageInfo {
                hasNextPage
                endCursor
            }
        }
    }
    """

    # Save the starting time, not the finishing time,
    # to avoid missing changes during synchronization.
    sync_started_at = timezone.now()

    search = None

    if connection.last_synced_at:
        # Overlap synchronization windows by 5 minutes.
        since = connection.last_synced_at - timedelta(
            minutes=5
        )

        since_string = since.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

        search = f"updated_at:>'{since_string}'"

    cursor = None
    imported = 0
    updated = 0
    failed = []

    while True:
        result = client.execute_query(
            query,
            variables={
                "cursor": cursor,
                "search": search,
            },
        )

        orders = result["orders"]

        for shopify_order in orders["nodes"]:
            try:
                order, created = import_shopify_order(
                    connection_id=connection.id,
                    external_id=shopify_order["id"],
                )

                if created:
                    imported += 1
                else:
                    updated += 1

            except Exception as exc:
                failed.append({
                    "order": shopify_order["name"],
                    "error": str(exc),
                })

        page_info = orders["pageInfo"]

        if not page_info["hasNextPage"]:
            break

        cursor = page_info["endCursor"]

        if not cursor:
            raise RuntimeError(
                "Shopify pagination cursor is missing"
            )

    if not failed:
        connection.last_synced_at = sync_started_at
        connection.save(
            update_fields=["last_synced_at"]
        )

    return {
        "imported": imported,
        "updated": updated,
        "failed": failed,
    }
