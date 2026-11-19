from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date

from decimal import Decimal



from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError

from .models import Transaction, TransactionType, TransactionCategory
from .serializer import TransactionSerializer
from apps.core.models import Membership, Release, OrderItem, OrderStatus


def parse_report_date(value, field_name):
    if not value:
        return None

    try:
        parsed = parse_date(value)
    except ValueError:
        parsed = None

    if parsed is None:
        raise ValidationError({
            field_name: "Invalid date format. Use YYYY-MM-DD."
        })

    return parsed


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Transaction.objects.filter(
            label__memberships__user=self.request.user
        ).distinct()

        label = self.request.query_params.get("label")
        release = self.request.query_params.get("release")
        transaction_type = self.request.query_params.get("transaction_type")
        category = self.request.query_params.get("category")
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")

        # validation date
        date_from = parse_report_date(date_from, "date_from")
        date_to = parse_report_date(date_to, "date_to")

        if date_from and date_to and date_from > date_to:
            raise ValidationError({
                "date": "date_from cannot be later than date_to."
            })


        if label:
            queryset = queryset.filter(label_id=label)

        if release:
            queryset = queryset.filter(release_id=release)


        if date_from:
            queryset = queryset.filter(date__gte=date_from)


        if date_to:
            queryset = queryset.filter(date__lte=date_to)


        if transaction_type:
            queryset = queryset.filter(
                transaction_type=transaction_type
            )

        if category:
            queryset = queryset.filter(category=category)

        return queryset


class EconomicsSumamryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        label_id = request.query_params.get('label')
        if not label_id:
            return Response({"detail": "Label parameter is required."}, status=status.HTTP_400_BAD_REQUEST,)


        if not Membership.objects.filter(user=request.user, label_id=label_id).exists():
            return Response({"detail": "You do not have access to this label."}, status=status.HTTP_403_FORBIDDEN)

        transaction = Transaction.objects.filter(label_id=label_id)
        income = transaction.filter(transaction_type='income').aggregate(total=Sum('amount'))['total']
        expense = transaction.filter(transaction_type='expense').aggregate(total=Sum('amount'))['total']

        income = income or 0
        expense = expense or 0
        balance = income - expense

        return Response({
            'income': income, 
            'expense': expense, 
            'balance': balance,
        })

class ReleaseEconomicsSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, release_id):
        release = get_object_or_404(Release.objects.filter(label__memberships__user=request.user), id=release_id)
        transactions = Transaction.objects.filter(
            label=release.label,
            release=release,
        )

        transaction_totals = (
            transactions
            .values("currency", "transaction_type")
            .annotate(total=Sum("amount"))
        )

        transaction_summary = {}

        for row in transaction_totals:
            currency = row["currency"]

            if currency not in transaction_summary:
                transaction_summary[currency] = {
                    "income": Decimal("0.00"),
                    "expenses": Decimal("0.00"),
                }

            if row["transaction_type"] == TransactionType.INCOME:
                transaction_summary[currency]["income"] = row["total"]

            elif row["transaction_type"] == TransactionType.EXPENSE:
                transaction_summary[currency]["expenses"] = row["total"]

        for values in transaction_summary.values():
            values["balance"] = values["income"] - values["expenses"]

        transaction_summary = {
            currency: {
                key: f"{value:.2f}"
                for key, value in values.items()
            }
            for currency, values in transaction_summary.items()
        }

        sales_queryset = (
            OrderItem.objects
            .filter(
                release_format__release=release,
                order__label=release.label,
                order__status__in=[
                    OrderStatus.PAID,
                    OrderStatus.SHIPPED,
                    OrderStatus.COMPLETED,
                ],
            )
            .annotate(
                line_total=ExpressionWrapper(
                    F("quantity") * F("unit_price"),
                    output_field=DecimalField(
                        max_digits=14,
                        decimal_places=2,
                    ),
                )
            )
            .values("order__currency")
            .annotate(total=Sum("line_total"))
        )

        sales = {
            row["order__currency"]: f'{row["total"]:.2f}'
            for row in sales_queryset
        }

        production_costs = {}
        formats_data = []

        for release_format in release.formats.all():
            currency = release_format.cost_currency
            cost = release_format.cost

            production_costs[currency] = (
                production_costs.get(currency, Decimal("0.00")) + cost
            )

            quantity = release_format.quantity_produced

            unit_cost = (
                cost / quantity
                if quantity > 0
                else None
            )

            formats_data.append({
                "format_id": release_format.id,
                "quantity_produced": quantity,
                "production_cost": f"{cost:.2f}",
                "currency": currency,
                "unit_cost": (
                    f"{unit_cost:.2f}"
                    if unit_cost is not None
                    else None
                ),
            })

        production_costs = {
            currency: f"{amount:.2f}"
            for currency, amount in production_costs.items()
        }

        additional_expenses_queryset = (
            Transaction.objects
            .filter(
                label=release.label,
                release=release,
                transaction_type=TransactionType.EXPENSE,
            )
            .exclude(
                category=TransactionCategory.MANUFACTURING
            )
            .values("currency")
            .annotate(total=Sum("amount"))
        )

        additional_expenses = {
            row["currency"]: f'{row["total"]:.2f}'
            for row in additional_expenses_queryset
        }

        other_income_queryset = (
        transactions
        .filter(
            transaction_type=TransactionType.INCOME,
            order__isnull=True,
        )
        .values("currency")
        .annotate(total=Sum("amount"))
    )

        other_income = {
            row["currency"]: f'{row["total"]:.2f}'
            for row in other_income_queryset
        }


        currencies = (
            set(sales)
            | set(production_costs)
            | set(additional_expenses)
            | set(other_income)
        )

        profitability = {}

        for currency in sorted(currencies):
            sales_revenue = Decimal(sales.get(currency, "0.00"))
            other_revenue = Decimal(other_income.get(currency, "0.00"))

            revenue = sales_revenue + other_revenue

            production = Decimal(
                production_costs.get(currency, "0.00")
            )

            additional = Decimal(
                additional_expenses.get(currency, "0.00")
            )

            total_cost = production + additional
            profit = revenue - total_cost

            roi = (
                (profit / total_cost) * Decimal("100")
                if total_cost > 0
                else None
            )

            profitability[currency] = {
                "revenue": f"{revenue:.2f}",
                "total_costs": f"{total_cost:.2f}",
                "profit": f"{profit:.2f}",
                "roi": f"{roi:.2f}" if roi is not None else None,
            }

        return Response({
            "release": release.id,
            "title": release.title,
            "transactions": transaction_summary,
            "sales": sales,
            "other_income": other_income,
            "production_costs": production_costs,
            "formats": formats_data,
            "additional_expenses": additional_expenses,
            "profitability": profitability,
        })

    



class FinancialSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        label_id = request.query_params.get("label")

        if not label_id:
            raise ValidationError({
                "label": "Label parameter is required."
            })

        if not Membership.objects.filter(
            user=request.user,
            label_id=label_id,
        ).exists():
            return Response(
                {"detail": "You do not have access to this label."},
                status=status.HTTP_403_FORBIDDEN,
            )

        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")

        date_from = parse_report_date(date_from, "date_from")
        date_to = parse_report_date(date_to, "date_to")

        if date_from and date_to and date_from > date_to:
            raise ValidationError({
                "date": "date_from cannot be later than date_to."
            })

        transactions = Transaction.objects.filter(label_id=label_id)

        if date_from:
            transactions = transactions.filter(date__gte=date_from)

        if date_to:
            transactions = transactions.filter(date__lte=date_to)

        totals = (transactions
            .values("currency", "transaction_type")
            .annotate(total=Sum("amount"))
            .order_by("currency", "transaction_type")
        )

        currencies = {}

        for row in totals:
            currency = row["currency"]

            if currency not in currencies:
                currencies[currency] = {
                    "income": Decimal("0.00"),
                    "expenses": Decimal("0.00"),
                    "balance": Decimal("0.00"),
                }

            if row["transaction_type"] == "income":
                currencies[currency]["income"] = row["total"]

            elif row["transaction_type"] == "expense":
                currencies[currency]["expenses"] = row["total"]

        for values in currencies.values():
            values["balance"] = (
                values["income"] - values["expenses"]
            )

        return Response({
            "label": int(label_id),
            "currencies": {
                currency: {
                    key: f"{value:.2f}"
                    for key, value in values.items()
                }
                for currency, values in currencies.items()
            },
        })


    