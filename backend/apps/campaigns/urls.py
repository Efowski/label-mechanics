from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import CampaignViewSet

router = DefaultRouter()

router.register(r'campaigns', CampaignViewSet, basename='campaigns')

urlpatterns = router.urls
