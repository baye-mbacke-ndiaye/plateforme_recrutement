from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("offres/", include("offres.urls")),
    path("", include("offres.urls")),
]
