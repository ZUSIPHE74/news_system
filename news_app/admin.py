from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Publisher, Article, Newsletter
from .signals import create_groups_and_permissions


class UserAdmin(BaseUserAdmin):
    """
    Custom admin for User model to display role and publisher information.
    """

    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "Role & Publisher",
            {
                "fields": (
                    "role",
                    "publisher",
                    "subscribed_publishers",
                    "subscribed_journalists",
                )
            },
        ),
    )


admin.site.register(User, UserAdmin)
admin.site.register(Publisher)
admin.site.register(Article)
admin.site.register(Newsletter)


def setup_groups(modeladmin, request, queryset):
    """
    Admin action to manually trigger group and permission creation.
    """
    create_groups_and_permissions()


setup_groups.short_description = "Setup groups and permissions"
