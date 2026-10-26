from django.db import models

from apps.core.models import Label, Release, Order
from apps.campaigns.models import Campaign


class TransactionType(models.TextChoices):
    INCOME = "income", "Income"
    EXPENSE = "expense", "Expense"


class TransactionCategory(models.TextChoices):
    RELEASE = "release", "Release"
    MANUFACTURING = "manufacturing", "Manufacturing"
    SHIPPING = "shipping", "Shipping"
    PROMOTION = "promotion", "Promotion"
    SALES = "sales", "Sales"
    DISTRIBUTION = "distribution", "Distribution"
    EQUIPMENT = "equipment", "Equipment"
    OTHER = "other", "Other"


class Transaction(models.Model):
    label = models.ForeignKey(
        Label,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    release = models.ForeignKey(Release, on_delete=models.SET_NULL, related_name="transactions", null=True, blank=True)
    campaign = models.ForeignKey(Campaign, on_delete=models.SET_NULL, related_name='transactions', null=True, blank=True)
    order = models.OneToOneField(Order, on_delete=models.SET_NULL, related_name='transactions', null=True, blank=True)
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    currency = models.CharField(
        max_length=4,
        default="EUR",
    )
    date = models.DateField()
    description = models.CharField(
        max_length=255,
        blank=True,
    )
    category = models.CharField(
        max_length=30,
        choices=TransactionCategory.choices,
        default=TransactionCategory.OTHER,
    )

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount} {self.currency}"
