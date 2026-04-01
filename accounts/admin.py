from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import TeacherStudentLink, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ("email", "username", "name", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("email", "username", "name")
    ordering = ("email",)

    fieldsets = (
        *UserAdmin.fieldsets,
        ("Custom Fields", {"fields": ("name", "role")}),
    )

    add_fieldsets = (
        *UserAdmin.add_fieldsets,
        ("Custom Fields", {"fields": ("email", "name", "role")}),
    )


@admin.register(TeacherStudentLink)
class TeacherStudentLinkAdmin(admin.ModelAdmin):
    list_display = ("teacher", "student")
    search_fields = (
        "teacher__name",
        "teacher__email",
        "student__name",
        "student__email",
    )
    autocomplete_fields = ("teacher", "student")