from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Order


def get_visible_orders_for_user(user):
    if user.role == "admin":
        return Order.objects.select_related("user", "decided_by").all()

    if user.role == "teacher":
        return Order.objects.select_related("user", "decided_by").filter(user=user)

    return Order.objects.select_related("user", "decided_by").filter(user=user)


@login_required
def dashboard(request):
    user = request.user

    context = {
        "user": user,
    }
    return render(request, "orders/dashboard.html", context)


@login_required
def order_list(request):
    orders = get_visible_orders_for_user(request.user)

    context = {
        "orders": orders,
    }
    return render(request, "orders/order_list.html", context)