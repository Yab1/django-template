from django.conf import settings
from django.contrib import admin

from core.cookbook.models import Recipe

if settings.COOKBOOK_ENABLED:
    admin.site.register([Recipe])
