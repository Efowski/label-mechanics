from django.shortcuts import render
from rest_framework import viewsets
from .serializer import CampaignSerializer
from .models import Campaign


class CampaignViewSet(viewsets.ModelViewSet):

    serializer_class = CampaignSerializer

    def get_queryset(self):
        return Campaign.objects.filter(release__label__memberships__user=self.request.user).distinct()


    
    
