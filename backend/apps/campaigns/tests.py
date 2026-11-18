from django.test import TestCase
from datetime import date

from apps.core.models import User, Label, Membership, Release
from .models import Campaign

from rest_framework import status
from rest_framework.test import APITestCase


class CampaignPermissionsTest(APITestCase):

    def test_anonymous_user_cannot_list_campaigns(self):
        response = self.client.get("/api/campaigns/")

        self.assertIn(
            response.status_code,
            [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ],
        )


class CampaignIsolationTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="campaign_user",
            password="test123",
        )

        self.other_label = Label.objects.create(
            name="Other Campaign Label",
        )

        self.other_release = Release.objects.create(
            label=self.other_label,
            title="Other Release",
            artist="Other Artist",
            catalog_number="OTHER-001",
        )

        self.other_campaign = Campaign.objects.create(
            release=self.other_release,
            name="Private Campaign",
            channel="instagram",
            start_date=date(2026, 11, 18),
        )

        self.client.force_authenticate(user=self.user)

    def test_cannot_read_another_labels_campaign(self):
        response = self.client.get(
            f"/api/campaigns/{self.other_campaign.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )


    def test_cannot_update_another_labels_campaign(self):
        response = self.client.patch(
            f"/api/campaigns/{self.other_campaign.id}/",
            {"name": "Unauthorized Change"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.other_campaign.refresh_from_db()

        self.assertEqual(
            self.other_campaign.name,
            "Private Campaign",
        )

    def test_cannot_create_campaign_for_another_labels_release(self):
        response = self.client.post(
            "/api/campaigns/",
            {
                "release": self.other_release.id,
                "name": "Unauthorized Campaign",
                "channel": "instagram",
                "start_date": "2026-11-18",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertFalse(
            Campaign.objects.filter(
                release=self.other_release,
                name="Unauthorized Campaign",
            ).exists()
        )