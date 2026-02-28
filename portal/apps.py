"""
portal/apps.py
App configuration for the Malawi College of Forestry & Wildlife Portal
Authored by Mark
"""

from django.apps import AppConfig

class PortalConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "portal"
    verbose_name = "Forestry & Wildlife Portal"
