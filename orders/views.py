from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from .forms import OrderCreateForm
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


@login_required
def order_create(request):
    if request.method == "POST":
        form = OrderCreateForm(request.POST, user=request.user)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.status = Order.STATUS_SUBMITTED

            if request.user.role == "student":
                order.order_type = Order.ORDER_TYPE_STUDENT
            elif request.user.role == "teacher":
                order.order_type = Order.ORDER_TYPE_TEACHER
            else:
                order.order_type = Order.ORDER_TYPE_TEACHER

            order.save()

            messages.success(request, f"Order {order.id} was created successfully.")
            return redirect("orders:order_detail", order_id=order.id)
    else:
        form = OrderCreateForm(user=request.user)

    context = {
        "form": form,
    }
    return render(request, "orders/order_form.html", context)