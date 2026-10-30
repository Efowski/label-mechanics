from datetime import date
from decimal import Decimal

 
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.models import User, Label, Membership, Release
from apps.campaigns.models import Campaign, CampaignMetric, Coverage
from .models import Transaction

 
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