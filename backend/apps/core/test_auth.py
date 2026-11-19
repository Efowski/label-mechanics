import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse


User = get_user_model()


class AuthenticationAPITest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="TestPassword123!",
        )

        self.client = Client(enforce_csrf_checks=True)

    def test_csrf_endpoint(self):
        response = self.client.get(reverse("auth-csrf"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("csrftoken", response.cookies)

    def test_login_and_current_user(self):
        csrf_response = self.client.get(reverse("auth-csrf"))
        csrf_token = csrf_response.cookies["csrftoken"].value

        response = self.client.post(
            reverse("auth-login"),
            data=json.dumps({
                "username": "testuser",
                "password": "TestPassword123!",
            }),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], "testuser")

        me_response = self.client.get(reverse("auth-me"))

        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(me_response.json()["username"], "testuser")

    def test_login_without_csrf_is_rejected(self):
        response = self.client.post(
            reverse("auth-login"),
            data=json.dumps({
                "username": "testuser",
                "password": "TestPassword123!",
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)

    def test_invalid_credentials(self):
        csrf_response = self.client.get(reverse("auth-csrf"))
        csrf_token = csrf_response.cookies["csrftoken"].value

        response = self.client.post(
            reverse("auth-login"),
            data=json.dumps({
                "username": "testuser",
                "password": "wrong-password",
            }),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, 400)

    def test_logout(self):
        self.client.force_login(self.user)

        csrf_response = self.client.get(reverse("auth-csrf"))
        csrf_token = csrf_response.cookies["csrftoken"].value

        response = self.client.post(
            reverse("auth-logout"),
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, 200)

        me_response = self.client.get(reverse("auth-me"))

        self.assertEqual(me_response.status_code, 403)