 
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import LabelViewSet, ReleaseViewSet, ReleaseFormatViewSet, TrackViewSet, ContactViewSet, OrderViewSet, OrderItemViewSet

router = DefaultRouter()
router.register(r'labels', LabelViewSet, basename='label')
router.register(r'releases', ReleaseViewSet, basename='release')
router.register(r'release-formats', ReleaseFormatViewSet,  basename='release-format')
router.register(r'tracks', TrackViewSet, basename='track')
router.register(r'contacts', ContactViewSet, basename='contact')
router.register(r'orders', OrderViewSet, basename='orders')
router.register(r'order-items', OrderItemViewSet, basename='order-item')

urlpatterns = [
    path('', include(router.urls)),
]
