from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date

from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError

from .models import Transaction
from .serializer import TransactionSerializer
from apps.core.models import Membership, Release


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

        if date_from:
            date_from = parse_date(date_from)
            if date_from is None:
                raise ValidationError(
                    {
                        "date_from": "Invalid date format. Use YYYY-MM-DD."
                     }
                )
        

        if date_to:
            date_to = parse_date(date_to)
            if date_to is None:
                raise ValidationError({
                    "date_to": "Invalid date format. Use YYYY-MM-DD."
                })

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
        transactions = Transaction.objects.filter( release=release)
        income = transactions.filter(transaction_type='income').aggregate(total=Sum('amount'))['total']
        expense = transactions.filter(transaction_type='expense').aggregate(total=Sum('amount'))['total']

        income = income or 0
        expense = expense or 0

        balance = income - expense

        return Response({
            'release': release.id,
            'title': release.title,
            'income': income, 
            'expense': expense,
            'balance': balance,
        })
