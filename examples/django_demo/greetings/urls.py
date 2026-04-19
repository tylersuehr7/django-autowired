"""Greetings app URL routes."""

from django.urls import path

from greetings.views import greet

urlpatterns = [
    path("greet/<str:name>/", greet, name="greet"),
]
