from datetime import date
from decimal import Decimal

 
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.models import User, Label, Membership, Release, Order, ReleaseFormat, OrderItem, OrderStatus
from apps.campaigns.models import Campaign, CampaignMetric, Coverage
from .models import Transaction, TransactionType

 
class TransactionCampaignValidationTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username='user', password='test123')
        self.label_a = Label.objects.create(name='Label A')
        self.label_b = Label.objects.create(name='Label B')

        Membership.objects.create(user=self.user, label=self.label_a)

        self.release_a = Release.objects.create(label=self.label_a, title='Release A', artist='Artist A', catalog_number='LABELA001')
        self.release_a2 = Release.objects.create(label=self.label_a, title="Release A2",artist="Artist A",catalog_number="LABELA002",
)
        self.release_b = Release.objects.create(label=self.label_b, title='Release B', artist='Artist B', catalog_number='LABELB001')
        
        self.campaign_a = Campaign.objects.create(release=self.release_a,name="Campaign A",channel="Instagram",start_date=date(2026, 10, 1),
)
        self.campaign_b = Campaign.objects.create(release=self.release_b, name='Campaign B', channel='Instagram', start_date=date(2026, 10, 1),)


    def test_transaction_cannot_use_campaign_from_another_label(self):
        self.client.force_authenticate(user=self.user)

        url = reverse("transaction-list")

        response = self.client.post(
            url,
            {
                "label": self.label_a.id,
                "campaign": self.campaign_b.id,
                "transaction_type": "expense",
                "amount": str(Decimal("50.00")),
                "currency": "EUR",
                "date": "2026-10-27",
                "category": "promotion",
                "description": "Instagram campaign",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "campaign",
            response.data,
        )

    def test_transaction_campaign_must_match_release(self):
        self.client.force_authenticate(user=self.user)

        url = reverse("transaction-list")

        response = self.client.post(
            url,
            {
                "label": self.label_a.id,
                "release": self.release_a2.id,
                "campaign": self.campaign_a.id,
                "transaction_type": "expense",
                "amount": str(Decimal("50.00")),
                "currency": "EUR",
                "date": "2026-10-27",
                "category": "promotion",
                "description": "Instagram campaign",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "campaign",
            response.data,
        )

    def test_transaction_can_use_campaign_from_same_release(self):
        self.client.force_authenticate(user=self.user)

        url = reverse("transaction-list")

        response = self.client.post(
            url,
            {
                "label": self.label_a.id,
                "release": self.release_a.id,
                "campaign": self.campaign_a.id,
                "transaction_type": "expense",
                "amount": str(Decimal("50.00")),
                "currency": "EUR",
                "date": "2026-10-27",
                "category": "promotion",
                "description": "Instagram campaign",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["campaign"],
            self.campaign_a.id,
        )

    def test_campaign_total_cost_groups_expenses_by_currency(self):
        self.client.force_authenticate(user=self.user)

        Transaction.objects.create(
            label=self.label_a,
            release=self.release_a,
            campaign=self.campaign_a,
            transaction_type="expense",
            amount=Decimal("50.00"),
            currency="EUR",
            date=date(2026, 10, 27),
            category="promotion",
        )

        Transaction.objects.create(
            label=self.label_a,
            release=self.release_a,
            campaign=self.campaign_a,
            transaction_type="expense",
            amount=Decimal("25.00"),
            currency="EUR",
            date=date(2026, 10, 27),
            category="promotion",
        )

        Transaction.objects.create(
            label=self.label_a,
            release=self.release_a,
            campaign=self.campaign_a,
            transaction_type="expense",
            amount=Decimal("100.00"),
            currency="PLN",
            date=date(2026, 10, 27),
            category="promotion",
        )

        url = reverse("campaigns-detail", args=[self.campaign_a.id])

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["total_cost"],
            {
                "EUR": Decimal("75.00"),
                "PLN": Decimal("100.00"),
            },
        )

    def test_release_total_cost_and_breakdown(self):
        self.client.force_authenticate(user=self.user)

        Transaction.objects.create(
            label=self.label_a,
            release = self.release_a,
            transaction_type="expense",
            amount=Decimal("226.00"),
            currency="EUR",
            date=date(2026, 3, 7),
            category="manufacturing",
        
            )
        Transaction.objects.create(
            label=self.label_a,
            release=self.release_a,
            campaign=self.campaign_a,
            transaction_type="expense",
            amount=Decimal("20.00"),
            currency="EUR",
            date=date(2026, 5, 1),
            category="promotion",
            )
        url = reverse("release-detail", args=[self.release_a.id])
        response = self.client.get(url)

        self.assertEqual(
        response.status_code,
        status.HTTP_200_OK,
    )

        self.assertEqual(
            response.data["total_cost"],
            {
                "EUR": Decimal("246.00"),
            },
        )

        self.assertEqual(
            response.data["cost_breakdown"],
            {
                "manufacturing": {
                    "EUR": Decimal("226.00"),
                },
                "promotion": {
                    "EUR": Decimal("20.00"),
                },
            },
        )
    def test_campaign_returns_metrics(self):
        self.client.force_authenticate(user=self.user)

        CampaignMetric.objects.create(
            campaign=self.campaign_a,
            metric_type="views",
            value=Decimal("350.00"),
        )

        CampaignMetric.objects.create(
            campaign=self.campaign_a,
            metric_type="reach",
            value=Decimal("201.00"),
        )

        CampaignMetric.objects.create(
            campaign=self.campaign_a,
            metric_type="clicks",
            value=Decimal("12.00"),
        )

        url = reverse(
            "campaigns-detail",
            args=[self.campaign_a.id],
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data["metrics"]),
            3,
        )


    def test_campaign_metric_cannot_use_campaign_from_another_label(self):
        self.client.force_authenticate(user=self.user)

        url = reverse("campaign-metrics-list")

        data = {
            "campaign": self.campaign_b.id,
            "metric_type": "views",
            "value": "350.00",
        }

        response = self.client.post(
            url,
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "campaign",
            response.data,
        )

    def test_campaign_returns_coverage(self):
        self.client.force_authenticate(user=self.user)

        Coverage.objects.create(campaign=self.campaign_a, coverage_type='online_review', publication='Magazine', title='Title',
                                url='https://example.com/review/', published_at=date(2026, 5, 10),)


        url = reverse(
        "campaigns-detail",
        args=[self.campaign_a.id],
    )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data["coverage"]),
            1,
        )

    def test_coverage_cannot_use_campaign_from_another_label(self):
        self.client.force_authenticate(user=self.user)

        url = reverse("coverage-list")

        data = {
            "campaign": self.campaign_b.id,
            "coverage_type": "online_review",
            "publication": "Test Magazine",
            "title": "Test review",
            "url": "https://example.com/review/",
            "published_at": "2026-05-10",
        }

        response = self.client.post(
            url,
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "campaign",
            response.data,
        )

    def test_social_campaign_returns_results_summary(self):
        self.client.force_authenticate(user=self.user)

        self.campaign_a.campaign_type = Campaign.CampaignType.SOCIAL
        self.campaign_a.save()

        CampaignMetric.objects.create(
            campaign=self.campaign_a,
            metric_type=CampaignMetric.MetricType.VIEWS,
            value=Decimal("350.00"),
        )

        CampaignMetric.objects.create(
            campaign=self.campaign_a,
            metric_type=CampaignMetric.MetricType.REACH,
            value=Decimal("201.00"),
        )

        CampaignMetric.objects.create(
            campaign=self.campaign_a,
            metric_type=CampaignMetric.MetricType.CLICKS,
            value=Decimal("12.00"),
        )

        url = reverse("campaigns-detail", args=[self.campaign_a.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["results_summary"]["clicks_per_100_views"],
            Decimal("3.43"),
        )   

    def test_outreach_campaign_returns_results_summary(self):
        self.client.force_authenticate(user=self.user)

        self.campaign_a.campaign_type = Campaign.CampaignType.OUTREACH
        self.campaign_a.save()

        CampaignMetric.objects.create(
            campaign=self.campaign_a,
            metric_type=CampaignMetric.MetricType.PROMOS_SENT,
            value=Decimal("5.00"),
        )

        Coverage.objects.create(
            campaign=self.campaign_a,
            coverage_type=Coverage.CoverageType.ONLINE_REVIEW,
            publication="Test Magazine",
            title="Test review",
            url="https://example.com/review/",
            published_at=date(2026, 5, 10),
        )

        url = reverse("campaigns-detail", args=[self.campaign_a.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["results_summary"]["promos_sent"],
            Decimal("5.00"),
        )
        self.assertEqual(
            response.data["results_summary"]["coverage_count"],
            1,
        )
        self.assertEqual(
            response.data["results_summary"]["coverage_rate"],
            Decimal("20.00"),
        )


class TransactionPartialUpdateTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create(username='patch_user', password='test123')
        self.label = Label.objects.create(name='Patch Label')
        Membership.objects.create(user=self.user, label=self.label)
        self.release = Release.objects.create(label=self.label, title='Title A', artist='Test Artist', catalog_number='TEST-PATCH-001')

        self.transaction = Transaction.objects.create(label=self.label, transaction_type='expense', amount=Decimal('50.00'),  currency="EUR", date=date(2026, 11, 18), category='Promotion')

    def test_patch_release_without_label(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(f"/api/transactions/{self.transaction.id}/", {"release": self.release.id}, format='json')
        self.assertEqual(response.status_code, 200)
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.release, self.release,)


    def test_cannot_assign_order_from_another_label(self):
        other_label = Label.objects.create(
                        name="Other Label",
                    )
        
        other_order = Order.objects.create(
                        label=other_label,
                        order_date=date(2026, 11, 18),
                    )
        
        self.client.force_authenticate(user=self.user)
        
        response = self.client.patch(
                        f"/api/transactions/{self.transaction.id}/",
                        {"order": other_order.id},
                        format="json",
                    )
        
        self.assertEqual(
                        response.status_code,
                        status.HTTP_400_BAD_REQUEST,
                    )
        
        self.assertIn("order", response.data)
        
        self.transaction.refresh_from_db()
        
        self.assertIsNone(self.transaction.order)


    def test_cannot_change_label_with_existing_release(self):
        other_label = Label.objects.create(
            name="Second Label",
        )

        Membership.objects.create(
            user=self.user,
            label=other_label,
        )

        self.transaction.release = self.release
        self.transaction.save()

        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            f"/api/transactions/{self.transaction.id}/",
            {"label": other_label.id},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn("release", response.data)

        self.transaction.refresh_from_db()

        self.assertEqual(self.transaction.label, self.label)
        self.assertEqual(self.transaction.release, self.release)


    def test_user_cannot_update_another_labels_transaction(self):
        outsider = User.objects.create_user(
            username="outsider",
            password="test123",
        )

        self.client.force_authenticate(user=outsider)

        response = self.client.patch(
            f"/api/transactions/{self.transaction.id}/",
            {"amount": "999.00"},
            format="json",
        )

        self.assertIn(
            response.status_code,
            [
                status.HTTP_403_FORBIDDEN,
                status.HTTP_404_NOT_FOUND,
            ],
        )

        self.transaction.refresh_from_db()

        self.assertEqual(
            self.transaction.amount,
            Decimal("50.00"),
        )


class FinancialSummaryTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create(username='reportuser', password='test123')
        self.label = Label.objects.create(name='Test Label', currency='PLN')

        Membership.objects.create(user=self.user, label=self.label)
        self.client.force_authenticate(user=self.user)


    def test_financial_summary_calculates_balance(self):
        Transaction.objects.create(
            label=self.label,
            transaction_type="income",
            amount=Decimal("1000.00"),
            currency="PLN",
            date=date(2026, 11, 18),
        )

        Transaction.objects.create(
            label=self.label,
            transaction_type="expense",
            amount=Decimal("400.00"),
            currency="PLN",
            date=date(2026, 11, 18),
        )

        url = reverse("financial-summary")

        response = self.client.get(
            url,
            {"label": self.label.id},
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["currencies"]["PLN"]["income"],
            "1000.00",
        )

        self.assertEqual(
            response.data["currencies"]["PLN"]["expenses"],
            "400.00",
        )

        self.assertEqual(
            response.data["currencies"]["PLN"]["balance"],
            "600.00",
        )    


    def test_cannot_access_another_labels_financial_summary(self):
            other_user = User.objects.create_user(
                username="other_report_user",
                password="testpass123",
            )
    
            other_label = Label.objects.create(
                name="Other Records",
                currency="EUR",
            )
    
            Membership.objects.create(
                user=other_user,
                label=other_label,
            )
    
            Transaction.objects.create(
                label=other_label,
                transaction_type="income",
                amount=Decimal("5000.00"),
                currency="EUR",
                date=date(2026, 11, 18),
            )
    
            url = reverse("financial-summary")
    
            response = self.client.get(
                url,
                {"label": other_label.id},
            )
    
            self.assertEqual(
                response.status_code,
                status.HTTP_403_FORBIDDEN,
            )


    def test_financial_summary_separates_currencies(self):
        transactions = [
            ("income", "1000.00", "PLN"),
            ("expense", "300.00", "PLN"),
            ("income", "500.00", "EUR"),
            ("expense", "150.00", "EUR"),
        ]

        for transaction_type, amount, currency in transactions:
            Transaction.objects.create(
                label=self.label,
                transaction_type=transaction_type,
                amount=Decimal(amount),
                currency=currency,
                date=date(2026, 11, 18),
            )

        response = self.client.get(
            reverse("financial-summary"),
            {"label": self.label.id},
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        currencies = response.data["currencies"]

        self.assertEqual(set(currencies.keys()), {"PLN", "EUR"})

        self.assertEqual(currencies["PLN"]["income"], "1000.00")
        self.assertEqual(currencies["PLN"]["expenses"], "300.00")
        self.assertEqual(currencies["PLN"]["balance"], "700.00")

        self.assertEqual(currencies["EUR"]["income"], "500.00")
        self.assertEqual(currencies["EUR"]["expenses"], "150.00")
        self.assertEqual(currencies["EUR"]["balance"], "350.00")


    def test_financial_summary_filters_by_date(self):
        transactions = [
            ("income", "1000.00", date(2026, 10, 10)),
            ("expense", "300.00", date(2026, 10, 15)),
            ("income", "2000.00", date(2026, 11, 5)),
            ("expense", "500.00", date(2026, 11, 10)),
        ]

        for transaction_type, amount, transaction_date in transactions:
            Transaction.objects.create(
                label=self.label,
                transaction_type=transaction_type,
                amount=Decimal(amount),
                currency="PLN",
                date=transaction_date,
            )

        response = self.client.get(
            reverse("financial-summary"),
            {
                "label": self.label.id,
                "date_from": "2026-10-01",
                "date_to": "2026-10-31",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        pln = response.data["currencies"]["PLN"]

        self.assertEqual(pln["income"], "1000.00")
        self.assertEqual(pln["expenses"], "300.00")
        self.assertEqual(pln["balance"], "700.00")

    def test_financial_summary_excludes_other_labels_transactions(self):
        other_label = Label.objects.create(
            name="Other Records",
            currency="PLN",
        )

        Transaction.objects.create(
            label=self.label,
            transaction_type="income",
            amount=Decimal("1000.00"),
            currency="PLN",
            date=date(2026, 11, 18),
        )

        Transaction.objects.create(
            label=other_label,
            transaction_type="income",
            amount=Decimal("9000.00"),
            currency="PLN",
            date=date(2026, 11, 18),
        )

        response = self.client.get(
            reverse("financial-summary"),
            {"label": self.label.id},
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        pln = response.data["currencies"]["PLN"]

        self.assertEqual(pln["income"], "1000.00")
        self.assertEqual(pln["expenses"], "0.00")
        self.assertEqual(pln["balance"], "1000.00")



    def test_financial_summary_rejects_invalid_dates(self):
        url = reverse("financial-summary")

        invalid_cases = [
            {
                "date_from": "invalid-date",
            },
            {
                "date_to": "2026-13-40",
            },
            {
                "date_from": "2026-11-30",
                "date_to": "2026-11-01",
            },
        ]

        for params in invalid_cases:
            with self.subTest(params=params):
                response = self.client.get(
                    url,
                    {
                        "label": self.label.id,
                        **params,
                    },
                )

                self.assertEqual(
                    response.status_code,
                    status.HTTP_400_BAD_REQUEST,
                )


    def test_transactions_reject_invalid_date(self):
        response = self.client.get(
            reverse("transaction-list"),
            {
                "label": self.label.id,
                "date_to": "2026-13-40",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn("date_to", response.data)


class ReleaseSalesSummaryTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create(username='release_report_user', password='test123')
        self.label = Label.objects.create(name='Release Test Record', currency='PLN')
        Membership.objects.create(user=self.user, label=self.label)
        self.client.force_authenticate(user=self.user)

    def test_release_summary_counts_only_its_sales(self):
            release_a = Release.objects.create(
                label=self.label,
                title="Album A",
                artist="Artist A",
                catalog_number="TEST-001",
            )

            release_b = Release.objects.create(
                label=self.label,
                title="Album B",
                artist="Artist B",
                catalog_number="TEST-002",
            )

            format_a = ReleaseFormat.objects.create(
                release=release_a,
                format_type="lp",
                catalog_number="TEST-001-LP",
                price=Decimal("100.00"),
                stock_quantity=10,
            )

            format_b = ReleaseFormat.objects.create(
                release=release_b,
                format_type="cd",
                catalog_number="TEST-002-CD",
                price=Decimal("50.00"),
                stock_quantity=10,
            )

            order = Order.objects.create(
                label=self.label,
                order_date=date(2026, 11, 19),
                status="paid",
                currency="PLN",
            )

            OrderItem.objects.create(
                order=order,
                release_format=format_a,
                quantity=2,
                unit_price=Decimal("100.00"),
            )

            OrderItem.objects.create(
                order=order,
                release_format=format_b,
                quantity=1,
                unit_price=Decimal("50.00"),
            )

            response = self.client.get(
                reverse(
                    "release-economics-summary",
                    kwargs={"release_id": release_a.id},
                )
            )

            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
            )

            self.assertEqual(
                response.data["sales"]["PLN"],
                "200.00",
            )    

    def test_release_summary_counts_only_eligible_order_statuses(self):
            release = Release.objects.create(
                label=self.label,
                title="Status Test Album",
                artist="Test Artist",
                catalog_number="STATUS-001",
            )
    
            release_format = ReleaseFormat.objects.create(
                release=release,
                format_type="lp",
                catalog_number="STATUS-001-LP",
                price=Decimal("100.00"),
                stock_quantity=20,
            )
    
            statuses = [
                ("draft", "100.00"),
                ("pending", "100.00"),
                ("paid", "100.00"),
                ("shipped", "100.00"),
                ("completed", "100.00"),
                ("cancelled", "100.00"),
            ]
    
            for order_status, price in statuses:
                order = Order.objects.create(
                    label=self.label,
                    order_date=date(2026, 11, 19),
                    status=order_status,
                    currency="PLN",
                )
    
                OrderItem.objects.create(
                    order=order,
                    release_format=release_format,
                    quantity=1,
                    unit_price=Decimal(price),
                )
    
            response = self.client.get(
                reverse(
                    "release-economics-summary",
                    kwargs={"release_id": release.id},
                )
            )
    
            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
            )
    
            self.assertEqual(
                response.data["sales"]["PLN"],
                "300.00",
            )


    def test_release_production_costs(self):
        release = Release.objects.create(
            label=self.label,
            title="Production Test",
            artist="Test Artist",
            catalog_number="PROD-001",
        )

        ReleaseFormat.objects.create(
            release=release,
            format_type="lp",
            catalog_number="PROD-LP",
            quantity_produced=300,
            cost=Decimal("4500.00"),
            cost_currency="PLN",
        )

        ReleaseFormat.objects.create(
            release=release,
            format_type="cd",
            catalog_number="PROD-CD",
            quantity_produced=500,
            cost=Decimal("2000.00"),
            cost_currency="PLN",
        )

        response = self.client.get(
            reverse(
                "release-economics-summary",
                kwargs={"release_id": release.id},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["production_costs"]["PLN"],
            "6500.00",
        )

        self.assertEqual(
            response.data["formats"][0]["unit_cost"],
            "15.00",
        )

        self.assertEqual(
            response.data["formats"][1]["unit_cost"],
            "4.00",
        )


    def test_unit_cost_with_zero_quantity(self):
        release = Release.objects.create(
            label=self.label,
            title="Zero Quantity Test",
            artist="Test Artist",
            catalog_number="ZERO-001",
        )

        ReleaseFormat.objects.create(
            release=release,
            format_type="lp",
            catalog_number="ZERO-LP",
            quantity_produced=0,
            cost=Decimal("1000.00"),
            cost_currency="EUR",
        )

        response = self.client.get(
            reverse(
                "release-economics-summary",
                kwargs={"release_id": release.id},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["formats"][0]["unit_cost"],
            None,
        )


    def test_additional_expenses_exclude_manufacturing(self):
        release = Release.objects.create(
            label=self.label,
            title="Expenses Test",
            artist="Test Artist",
            catalog_number="EXP-001",
        )

        expenses = [
            ("manufacturing", "4500.00"),
            ("promotion", "1500.00"),
            ("release", "1000.00"),
        ]

        for category, amount in expenses:
            Transaction.objects.create(
                label=self.label,
                release=release,
                transaction_type=TransactionType.EXPENSE,
                category=category,
                amount=Decimal(amount),
                currency="PLN",
                date=date(2026, 11, 19),
            )

        response = self.client.get(
            reverse(
                "release-economics-summary",
                kwargs={"release_id": release.id},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["additional_expenses"]["PLN"],
            "2500.00",
        )

    def test_release_profitability(self):
        release = Release.objects.create(
            label=self.label,
            title="Profitability Test",
            artist="Test Artist",
            catalog_number="PROFIT-001",
        )

        release_format = ReleaseFormat.objects.create(
            release=release,
            format_type="lp",
            catalog_number="PROFIT-LP",
            quantity_produced=100,
            cost=Decimal("500.00"),
            cost_currency="PLN",
        )

        order = Order.objects.create(
            label=self.label,
            order_date=date(2026, 11, 19),
            status="paid",
            currency="PLN",
        )

        OrderItem.objects.create(
            order=order,
            release_format=release_format,
            quantity=10,
            unit_price=Decimal("100.00"),
        )

        Transaction.objects.create(
            label=self.label,
            release=release,
            transaction_type=TransactionType.EXPENSE,
            category="promotion",
            amount=Decimal("300.00"),
            currency="PLN",
            date=date(2026, 11, 19),
        )

        response = self.client.get(
            reverse(
                "release-economics-summary",
                kwargs={"release_id": release.id},
            )
        )

        self.assertEqual(response.status_code, 200)

        result = response.data["profitability"]["PLN"]

        self.assertEqual(result["revenue"], "1000.00")
        self.assertEqual(result["total_costs"], "800.00")
        self.assertEqual(result["profit"], "200.00")
        self.assertEqual(result["roi"], "25.00")


    def test_release_profitability_without_costs(self):
        release = Release.objects.create(
            label=self.label,
            title="No Costs Test",
            artist="Test Artist",
            catalog_number="NOCOST-001",
        )

        response = self.client.get(
            reverse(
                "release-economics-summary",
                kwargs={"release_id": release.id},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profitability"], {})


    def test_other_income_excludes_order_transactions(self):
        release = Release.objects.create(
            label=self.label,
            title="Other Income Test",
            artist="Test Artist",
            catalog_number="OTHER-001",
        )

        release_format = ReleaseFormat.objects.create(
            release=release,
            format_type="lp",
            catalog_number="OTHER-LP",
        )

        order = Order.objects.create(
            label=self.label,
            order_date=date(2026, 11, 19),
            status=OrderStatus.PAID,
            currency="PLN",
        )

        OrderItem.objects.create(
            order=order,
            release_format=release_format,
            quantity=2,
            unit_price=Decimal("100.00"),
        )

        Transaction.objects.create(
            label=self.label,
            release=release,
            order=order,
            transaction_type=TransactionType.INCOME,
            category="sales",
            amount=Decimal("200.00"),
            currency="PLN",
            date=date(2026, 11, 19),
        )

        Transaction.objects.create(
            label=self.label,
            release=release,
            transaction_type=TransactionType.INCOME,
            category="other",
            amount=Decimal("50.00"),
            currency="PLN",
            date=date(2026, 11, 19),
        )

        response = self.client.get(
            reverse(
                "release-economics-summary",
                kwargs={"release_id": release.id},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["other_income"]["PLN"], "50.00")
        self.assertEqual(
            response.data["profitability"]["PLN"]["revenue"],
            "250.00",
        )


    def test_profitability_separates_currencies(self):
        release = Release.objects.create(
            label=self.label,
            title="Currency Test",
            artist="Test Artist",
            catalog_number="CUR-001",
        )

        for currency, amount in [
            ("PLN", "100.00"),
            ("EUR", "50.00"),
        ]:
            Transaction.objects.create(
                label=self.label,
                release=release,
                transaction_type=TransactionType.INCOME,
                category="other",
                amount=Decimal(amount),
                currency=currency,
                date=date(2026, 11, 19),
            )

        response = self.client.get(
            reverse(
                "release-economics-summary",
                kwargs={"release_id": release.id},
            )
        )

        self.assertEqual(response.status_code, 200)

        profitability = response.data["profitability"]

        self.assertEqual(profitability["PLN"]["revenue"], "100.00")
        self.assertEqual(profitability["EUR"]["revenue"], "50.00")
        self.assertIsNone(profitability["PLN"]["roi"])
        self.assertIsNone(profitability["EUR"]["roi"])

        self.assertEqual(
            response.data["transactions"]["PLN"]["income"],
            "100.00",
        )
        self.assertEqual(
            response.data["transactions"]["EUR"]["income"],
            "50.00",
        )    


    def test_release_summary_excludes_other_label_transactions(self):
        release = Release.objects.create(
            label=self.label,
            title="Isolation Test",
            artist="Test Artist",
            catalog_number="ISO-001",
        )

        other_label = Label.objects.create(
            name="Other Label",
            currency="PLN",
        )

        Transaction.objects.create(
            label=other_label,
            release=release,
            transaction_type=TransactionType.INCOME,
            amount=Decimal("999.00"),
            currency="PLN",
            date=date(2026, 11, 19),
        )

        response = self.client.get(
            reverse(
                "release-economics-summary",
                kwargs={"release_id": release.id},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["other_income"], {})
        self.assertEqual(response.data["transactions"], {})