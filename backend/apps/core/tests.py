from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
 
from .models import User, Label, Membership, Release


class ReleaseTenantIsolationTest(APITestCase):

    def setUp(self):
        self.user_a = User.objects.create_user(username='user_a', password='test123')
        self.user_b = User.objects.create_user(username='user_b', password='test123')
        self.client.force_authenticate(user=self.user_a)

        self.label_a = Label.objects.create(name='Label_a')
        self.label_b = Label.objects.create(name='Label_b')

        Membership.objects.create(user=self.user_a, label=self.label_a)
        Membership.objects.create(user=self.user_b, label=self.label_b)


        self.release_a = Release.objects.create(label=self.label_a, title='Release A', artist='Artist A', catalog_number='LABELA001')
        self.release_b = Release.objects.create(label=self.label_b, title='Release B', artist='Artist B', catalog_number='LABELB001')

    def test_user_can_only_see_releases_from_own_label(self):
        url = reverse('release-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.release_a.id)