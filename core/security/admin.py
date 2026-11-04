from django.contrib import admin

from core.security.models import Permission, Role, RolePermission, UserRole

admin.site.register([Permission, Role, RolePermission, UserRole])
