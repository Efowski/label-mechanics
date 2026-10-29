from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import CampaignViewSet, CampaignMetricViewset

router = DefaultRouter()

router.register(r'campaigns', CampaignViewSet, basename='campaigns')
router.register(r'campaign-metrics', CampaignMetricViewset, basename='campaign-metrics')

urlpatterns = router.urls
