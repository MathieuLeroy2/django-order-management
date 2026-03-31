from django.urls import path
from .views import dashboard, order_list, order_detail, order_create, order_edit

app_name = "orders"

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("orders/", order_list, name="order_list"),
    path("orders/create/", order_create, name="order_create"),
    path("orders/<int:order_id>/", order_detail, name="order_detail"),
    path("orders/<int:order_id>/edit/", order_edit, name="order_edit"),
]