from django import forms
from .models import Order


class OrderBaseForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "store",
            "article_number",
            "quantity",
            "short_description",
            "url",
            "total_price_excl_vat",
            "delivery_time_days",
            "student_remarks",
            "teacher_remarks",
        ]
        widgets = {
            "short_description": forms.TextInput(attrs={"maxlength": 255}),
            "student_remarks": forms.Textarea(attrs={"rows": 4}),
            "teacher_remarks": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user


class OrderCreateForm(OrderBaseForm):
    pass


class OrderEditForm(OrderBaseForm):
    pass


class OrderDecisionForm(forms.Form):
    decision = forms.ChoiceField(
        choices=[
            (Order.STATUS_SUBMITTED, "Submitted"),
            (Order.STATUS_APPROVED, "Approved"),
            (Order.STATUS_REJECTED, "Rejected"),
            (Order.STATUS_REWORK, "Needs rework"),
        ]
    )
    decision_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )

    def clean(self):
        cleaned_data = super().clean()
        decision = cleaned_data.get("decision")
        decision_reason = (cleaned_data.get("decision_reason") or "").strip()

        if decision in [Order.STATUS_REJECTED, Order.STATUS_REWORK] and not decision_reason:
            raise forms.ValidationError(
                "A reason is required when rejecting an order or requesting rework."
            )

        return cleaned_data