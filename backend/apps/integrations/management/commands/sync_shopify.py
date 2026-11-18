
from django.core.management.base import BaseCommand, CommandError

from apps.integrations.models import ShopifyConnection
from apps.integrations.shopify_sync import sync_shopify_orders


class Command(BaseCommand):
    help = "Synchronize Shopify orders with Label Mechanics"

    def add_arguments(self, parser):
        parser.add_argument(
            "--shop",
            type=str,
            help="Shopify shop domain (optional)",
        )

    def handle(self, *args, **options):
        shop_domain = options["shop"]

        connections = ShopifyConnection.objects.filter(
            is_active=True
        )

        if shop_domain:
            connections = connections.filter(
                shop_domain=shop_domain
            )

        if not connections.exists():
            raise CommandError(
                "No active Shopify connections found."
            )

        total_imported = 0
        total_updated = 0
        total_failed = 0

        for connection in connections:
            self.stdout.write(
                f"Synchronizing {connection.shop_domain}..."
            )

            try:
                result = sync_shopify_orders(connection.id)
            except Exception as exc:
                raise CommandError(
                    f"Synchronization failed for "
                    f"{connection.shop_domain}: {exc}"
                ) from exc

            imported = result["imported"]
            updated = result["updated"]
            failed = result["failed"]

            total_imported += imported
            total_updated += updated
            total_failed += len(failed)

            self.stdout.write(
                f"Imported: {imported}, "
                f"Updated: {updated}, "
                f"Failed: {len(failed)}"
            )

            for failure in failed:
                self.stderr.write(
                    f"  {failure['order']}: {failure['error']}"
                )

        self.stdout.write(
            f"Total: {total_imported} imported, "
            f"{total_updated} updated, "
            f"{total_failed} failed."
        )

        if total_failed:
            raise CommandError(
                "Synchronization completed with errors."
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Shopify synchronization completed."
            )
        )
