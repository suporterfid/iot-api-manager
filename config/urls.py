from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.readers.urls")),
    path("smartreader/", include("apps.smartreader.urls")),
    path(
        "accounts/", include("django.contrib.auth.urls")
    ),  # This line includes built-in auth URLs
]
