"""
urls.py
Root URL configuration for Malawi College of Forestry & Wildlife Portal
Authored by Mark
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # ---------------------------
    # Admin site
    # ---------------------------
    path("admin/", admin.site.urls),

    # ---------------------------
    # Django's built-in authentication system
    # Provides: login, logout, password reset, password change, etc.
    # ---------------------------
    path("accounts/", include("django.contrib.auth.urls")),

    # ---------------------------
    # Portal app routes
    # ---------------------------
    path("", include("portal.urls")),  # delegate all portal routes
]
