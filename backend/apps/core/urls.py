 
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import LabelViewSet, ReleaseViewSet, ReleaseFormatViewSet, TrackViewSet, ContactViewSet, OrderViewSet, OrderItemViewSet
from .auth_views import (csrf_view, login_view, logout_view, CurrentUserView,)


router = DefaultRouter()
router.register(r'labels', LabelViewSet, basename='label')
router.register(r'releases', ReleaseViewSet, basename='release')
router.register(r'release-formats', ReleaseFormatViewSet,  basename='release-format')
router.register(r'tracks', TrackViewSet, basename='track')
router.register(r'contacts', ContactViewSet, basename='contact')
router.register(r'orders', OrderViewSet, basename='orders')
router.register(r'order-items', OrderItemViewSet, basename='order-item')

urlpatterns = [
    path("auth/csrf/", csrf_view, name="auth-csrf"),
    path("auth/login/", login_view, name="auth-login"),
    path("auth/logout/", logout_view, name="auth-logout"),
    path("auth/me/", CurrentUserView.as_view(), name="auth-me"),
    path('', include(router.urls)),

]
