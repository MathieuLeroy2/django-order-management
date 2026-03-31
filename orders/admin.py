from django.contrib import admin
from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "short_description",
        "user",
        "order_type",
        "status",
        "store",
        "quantity",
        "created_at",
        "decided_by",
        "decided_at",
    )
    list_filter = ("status", "order_type", "created_at", "store")
    search_fields = (
        "short_description",
        "store",
        "article_number",
        "purchase_request_number",
        "user__email",
        "user__name",
    )
    autocomplete_fields = ("user", "decided_by")
    readonly_fields = ("created_at",)