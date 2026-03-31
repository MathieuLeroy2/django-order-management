from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from .models import Order


def get_visible_orders_for_user(user):
    if user.role == "admin":
        return Order.objects.select_related("user", "decided_by").all()

    if user.role == "teacher":
        return Order.objects.select_related("user", "decided_by").filter(user=user)

    return Order.objects.select_related("user", "decided_by").filter(user=user)


def user_can_view_order(user, order):
    if user.role == "admin":
        return True

    return order.user_id == user.id


@login_required
def dashboard(request):
    context = {
        "user": request.user,
    }
    return render(request, "orders/dashboard.html", context)


@login_required
def order_list(request):
    orders = get_visible_orders_for_user(request.user)

    context = {
        "orders": orders,
    }
    return render(request, "orders/order_list.html", context)


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related("user", "decided_by"),
        pk=order_id,
    )

    if not user_can_view_order(request.user, order):
        raise Http404("You do not have permission to view this order.")

    context = {
        "order": order,
    }
    return render(request, "orders/order_detail.html", context)