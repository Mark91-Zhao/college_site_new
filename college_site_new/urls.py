"""
Main URL Configuration
Using Django Built-in Authentication System
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # Django Built-in Authentication (login, logout, password reset, etc.)
    path("accounts/", include("django.contrib.auth.urls")),

    # Portal Application
    path("", include("portal.urls")),
]