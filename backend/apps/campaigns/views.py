from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .serializer import CampaignSerializer, CampaignMetricSerializer
from .models import Campaign, CampaignMetric


class CampaignViewSet(viewsets.ModelViewSet):

    serializer_class = CampaignSerializer

    def get_queryset(self):
        return Campaign.objects.filter(release__label__memberships__user=self.request.user).distinct()


    
    
class CampaignMetricViewset(viewsets.ModelViewSet):
    serializer_class = CampaignMetricSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CampaignMetric.objects.filter(campaign__release__label__memberships__user=self.request.user).distinct()