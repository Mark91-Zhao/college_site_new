"""
urls.py
Root URL configuration for Malawi College of Forestry & Wildlife Portal
Authored by Mark
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # ---------------------------
    # Admin (only once here)
    # ---------------------------
    path("admin/", admin.site.urls),

    # ---------------------------
    # Portal app routes
    # ---------------------------
    path("", include("portal.urls")),  # delegate all portal routes
]
