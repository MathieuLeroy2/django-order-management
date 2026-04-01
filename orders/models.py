from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Order(models.Model):
    ORDER_TYPE_STUDENT = "student_order"
    ORDER_TYPE_TEACHER = "teacher_order"

    ORDER_TYPE_CHOICES = [
        (ORDER_TYPE_STUDENT, "Student order"),
        (ORDER_TYPE_TEACHER, "Teacher order"),
    ]

    STATUS_DRAFT = "draft"
    STATUS_SUBMITTED = "submitted"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_REWORK = "rework"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_SUBMITTED, "Submitted"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_REWORK, "Needs rework"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES)
    store = models.CharField(max_length=255)
    article_number = models.CharField(max_length=100, blank=True)
    ordernumber = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        help_text="ERP order number",
    )
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    decision_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    short_description = models.CharField(max_length=255)
    url = models.URLField(blank=True)
    total_price_excl_vat = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    delivery_time_days = models.PositiveIntegerField(null=True, blank=True)
    purchase_request_number = models.CharField(max_length=100, blank=True)
    finance_order_date = models.DateField(null=True, blank=True)
    shipped_date = models.DateField(null=True, blank=True)
    received_date = models.DateField(null=True, blank=True)
    student_remarks = models.TextField(blank=True)
    teacher_remarks = models.TextField(blank=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="decided_orders",
    )
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.short_description} ({self.get_status_display()})"
    
    def get_store_list_type(self):
        return StoreRule.get_list_type_for_store(self.store)

    def is_store_blacklisted(self):
        return self.get_store_list_type() == StoreRule.LIST_TYPE_BLACKLIST

    def clean(self):
        if self.status in [self.STATUS_REJECTED, self.STATUS_REWORK] and not self.decision_reason:
            raise ValidationError(
                {
                    "decision_reason": "A reason is required when rejecting an order or requesting rework."
                }
            )


class StoreRule(models.Model):
    LIST_TYPE_WHITELIST = "whitelist"
    LIST_TYPE_BLACKLIST = "blacklist"

    LIST_TYPE_CHOICES = [
        (LIST_TYPE_WHITELIST, "Whitelist"),
        (LIST_TYPE_BLACKLIST, "Blacklist"),
    ]

    store_name = models.CharField(max_length=255, unique=True)
    list_type = models.CharField(max_length=20, choices=LIST_TYPE_CHOICES)

    class Meta:
        ordering = ["store_name"]

    def __str__(self):
        return f"{self.store_name} ({self.get_list_type_display()})"

    @classmethod
    def get_list_type_for_store(cls, store_name):
        normalized_name = (store_name or "").strip()
        if not normalized_name:
            return None

        rule = cls.objects.filter(store_name__iexact=normalized_name).first()
        if not rule:
            return None

        return rule.list_type

class AppSettings(models.Model):
    soft_spending_limit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Leave empty to disable the soft spending warning.",
    )

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Application settings"