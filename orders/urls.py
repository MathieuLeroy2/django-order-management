from django.urls import path
from .views import dashboard, order_list

app_name = "orders"

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("orders/", order_list, name="order_list"),
]