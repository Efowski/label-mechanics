from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import User, Label, Membership, UserRole


class LabelPermissionTests(TestCase):

    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner",
            password="testpass123",
        )

        self.member = User.objects.create_user(
            username="member",
            password="testpass123",
        )

        self.marketing = User.objects.create_user(
            username="marketing",
            password="testpass123",
        )

        self.label = Label.objects.create(
            name="Test Records",
        )

        Membership.objects.create(
            user=self.owner,
            label=self.label,
            role=UserRole.LABEL_OWNER,
        )

        Membership.objects.create(
            user=self.member,
            label=self.label,
            role=UserRole.LABEL_MEMBER,
        )

        Membership.objects.create(
            user=self.marketing,
            label=self.label,
            role=UserRole.LABEL_MARKETING,
        )

        self.client = APIClient()
        self.url = reverse(
            "label-detail",
            args=[self.label.id],
        )

    def test_owner_can_update_label(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.patch(
            self.url,
            {"name": "Updated Records"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

    def test_member_cannot_update_label(self):
        self.client.force_authenticate(user=self.member)

        response = self.client.patch(
            self.url,
            {"name": "Updated Records"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_marketing_cannot_update_label(self):
        self.client.force_authenticate(user=self.marketing)

        response = self.client.patch(
            self.url,
            {"name": "Updated Records"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_member_can_read_label(self):
        self.client.force_authenticate(user=self.member)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

    def test_owner_cannot_delete_label(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, 403)

    def test_unrelated_user_cannot_access_label(self):
        outsider = User.objects.create_user(
            username="outsider",
            password="testpass123",
        )

        self.client.force_authenticate(user=outsider)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 404)
        