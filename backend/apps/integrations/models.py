from django.db import models


class ShopifyConnection(models.Model):
    sales_channel = models.OneToOneField('economics.SalesChannel', on_delete=models.CASCADE, related_name='shopify_connection')
    shop_domain = models.CharField(max_length=250, unique=True)
    is_active = models.BooleanField(default=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.shop_domain
