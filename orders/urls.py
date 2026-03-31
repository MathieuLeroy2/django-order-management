from django.urls import path
from .views import dashboard, order_list, order_detail

app_name = "orders"

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("orders/", order_list, name="order_list"),
    path("orders/<int:order_id>/", order_detail, name="order_detail"),
]