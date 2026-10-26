from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import TransactionViewSet, EconomicsSumamryView, ReleaseEconomicsSummaryView


router = DefaultRouter()
router.register(
    r"transactions",
    TransactionViewSet,
    basename="transaction",
)


urlpatterns = [
    path("", include(router.urls)),
    path('economics/summary/', EconomicsSumamryView.as_view(), name='economic-summary'),
    path('economics/releases/<int:release_id>/summary/', ReleaseEconomicsSummaryView.as_view(), name="release-economics-summary",),

]
