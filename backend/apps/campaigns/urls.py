from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import CampaignViewSet, CampaignMetricViewset, CoverageViewset

router = DefaultRouter()

router.register(r'campaigns', CampaignViewSet, basename='campaigns')
router.register(r'campaign-metrics', CampaignMetricViewset, basename='campaign-metrics')
router.register(r'coverage', CoverageViewset, basename='coverage')

urlpatterns = router.urls
