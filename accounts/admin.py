from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import TeacherStudentLink, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User

    list_display = ("username", "name", "email", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("username", "name", "email")
    ordering = ("username",)

    fieldsets = UserAdmin.fieldsets + (
        ("Custom Fields", {"fields": ("name", "role")}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Custom Fields", {"fields": ("name", "role", "email")}),
    )


@admin.register(TeacherStudentLink)
class TeacherStudentLinkAdmin(admin.ModelAdmin):
    list_display = ("teacher", "student")
    search_fields = (
        "teacher__name",
        "teacher__username",
        "teacher__email",
        "student__name",
        "student__username",
        "student__email",
    )
    autocomplete_fields = ("teacher", "student")