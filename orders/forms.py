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