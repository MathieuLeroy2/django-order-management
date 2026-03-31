from django.urls import path
from .views import dashboard

app_name = "orders"

urlpatterns = [
    path("", dashboard, name="dashboard"),
]