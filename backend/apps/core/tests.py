from datetime import date
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User, Label, Membership, Release, ReleaseFormat, Order, OrderItem
from apps.economics.models import Transaction


class ReleaseTenantIsolationTest(APITestCase):

    def setUp(self):
        self.user_a = User.objects.create_user(
            username="user_a",
            password="test123",
        )
        self.user_b = User.objects.create_user(
            username="user_b",
            password="test123",
        )

        self.label_a = Label.objects.create(
            name="Label A",
        )
        self.label_b = Label.objects.create(
            name="Label B",
        )

        Membership.objects.create(
            user=self.user_a,
            label=self.label_a,
        )
        Membership.objects.create(
            user=self.user_b,
            label=self.label_b,
        )

        self.release_a = Release.objects.create(
            label=self.label_a,
            title="Release A",
            artist="Artist A",
            catalog_number="LABELA001",
        )
        self.release_b = Release.objects.create(
            label=self.label_b,
            title="Release B",
            artist="Artist B",
            catalog_number="LABELB001",
        )

    def test_user_can_only_see_releases_from_own_label(self):
        self.client.force_authenticate(user=self.user_a)

        url = reverse("release-list")
        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["id"],
            self.release_a.id,
        )


class OrderPaymentTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="user",
            password="test123",
        )

        self.label = Label.objects.create(
            name="Test Label",
        )

        Membership.objects.create(
            user=self.user,
            label=self.label,
        )

        self.empty_order = Order.objects.create(
            label=self.label,
            order_date=date(2026, 10, 27),
            status="pending",
        )


        self.release = Release.objects.create(
        label=self.label,
        title="Test Release",
        artist="Test Artist",
        catalog_number="TEST001",
        )

        self.release_format = ReleaseFormat.objects.create(
            release=self.release,
            format_type="vinyl",
            catalog_number="TEST001-LP",
            quantity_produced=10,
            price="20.00",
            stock_quantity=10,
        )

        self.order = Order.objects.create(
            label=self.label,
            order_date=date(2026, 10, 27),
            status="pending",
        )

        OrderItem.objects.create(
            order=self.order,
            release_format=self.release_format,
            quantity=2,
            unit_price="20.00",
        )

    def test_empty_order_cannot_be_paid(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(
            "orders-detail",
            args=[self.empty_order.id],
        )

        response = self.client.patch(
            url,
            {"status": "paid"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.empty_order.refresh_from_db()

        self.assertEqual(
            self.empty_order.status,
            "pending",
        )


    def test_paid_order_reduces_stock(self):
        self.client.force_authenticate(user=self.user)
        url = reverse( "orders-detail", args=[self.order.id],)
        response = self.client.patch(url,{"status": "paid"}, format="json",)
        self.assertEqual(response.status_code,status.HTTP_200_OK,
    )

        self.release_format.refresh_from_db()
        self.assertEqual(self.release_format.stock_quantity, 8,)


    def test_paid_order_creates_transaction(self):
        self.client.force_authenticate(user=self.user)
        url = reverse( "orders-detail", args=[self.order.id],)
        response = self.client.patch(url,{"status": "paid"}, format="json")
        self.assertEqual(
        response.status_code,
        status.HTTP_200_OK,
        )

        transaction = Transaction.objects.get(
            order=self.order,
        )

        self.assertEqual(
            transaction.amount,
            Decimal("40.00"),
        )

        self.assertEqual(
            transaction.transaction_type,
            "income",
        )


    def test_paying_order_twice_does_not_duplicate_effects(self):
            
        self.client.force_authenticate(user=self.user)

        url = reverse(
            "orders-detail",
            args=[self.order.id],
        )

        # First payment
        first_response = self.client.patch(
            url,
            {"status": "paid"},
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_200_OK,
        )

        # Move order back to pending
        pending_response = self.client.patch(
            url,
            {"status": "pending"},
            format="json",
        )

        self.assertEqual(
            pending_response.status_code,
            status.HTTP_200_OK,
        )

        # Try to pay the same order again
        second_response = self.client.patch(
            url,
            {"status": "paid"},
            format="json",
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_200_OK,
        )

        self.release_format.refresh_from_db()

        self.assertEqual(
            self.release_format.stock_quantity,
            8,
        )

        self.assertEqual(
            Transaction.objects.filter(order=self.order).count(),
            1,
        )