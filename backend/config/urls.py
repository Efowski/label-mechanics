 
from django.contrib import admin
from django.urls import path, include
 
 
urlpatterns = [
    path('admin', admin.site.urls),
    path('api/', include('apps.core.urls')),
    path('api/', include('apps.economics.urls')),
    path("api/", include("apps.campaigns.urls")),
    path("api-auth/", include("rest_framework.urls")),
]
