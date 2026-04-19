"""Root URL configuration for the demo."""

from django.urls import include, path

urlpatterns = [
    path("", include("greetings.urls")),
]
