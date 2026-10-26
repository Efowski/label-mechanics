from django.contrib import admin

from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "label",
        "transaction_type",
        "category",
        "amount",
        "currency",
    )
    list_filter = (
        "transaction_type",
        "category",
        "currency",
    )
    search_fields = (
        "description",
        "label__name",
    )
