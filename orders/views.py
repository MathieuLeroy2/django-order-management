from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import OrderCreateForm, OrderDecisionForm, OrderEditForm
from .models import Order


def get_visible_orders_for_user(user):
    if user.role == "admin":
        return Order.objects.select_related("user", "decided_by").all()

    if user.role == "teacher":
        return Order.objects.select_related("user", "decided_by").filter(
            Q(user=user) | Q(order_type=Order.ORDER_TYPE_STUDENT)
        ).distinct()

    return Order.objects.select_related("user", "decided_by").filter(user=user)


def user_can_view_order(user, order):
    if user.role == "admin":
        return True

    if user.role == "teacher":
        if order.user_id == user.id:
            return True
        if order.order_type == Order.ORDER_TYPE_STUDENT:
            return True
        return False

    return order.user_id == user.id


def user_can_edit_order(user, order):
    if user.role == "admin":
        return True

    if order.user_id != user.id:
        return False

    if order.status == Order.STATUS_APPROVED:
        return False

    return True


def user_can_decide_order(user, order):
    if user.role == "admin":
        return True

    if user.role != "teacher":
        return False

    if order.order_type == Order.ORDER_TYPE_STUDENT:
        return True

    if order.order_type == Order.ORDER_TYPE_TEACHER and order.user_id == user.id:
        return True

    return False


@login_required
def dashboard(request):
    context = {
        "user": request.user,
    }
    return render(request, "orders/dashboard.html", context)


@login_required
def order_list(request):
    if request.method == "POST" and "update_order_id" in request.POST:
        order = get_object_or_404(
            Order.objects.select_related("user", "decided_by"),
            pk=request.POST.get("update_order_id"),
        )

        if not user_can_decide_order(request.user, order):
            raise Http404("You do not have permission to update this order status.")

        form = OrderDecisionForm(request.POST)
        if form.is_valid():
            order.status = form.cleaned_data["decision"]
            order.decision_reason = form.cleaned_data["decision_reason"]
            order.decided_by = request.user
            order.decided_at = timezone.now()
            order.save()
            messages.success(request, f"Order {order.id} was updated successfully.")
            return redirect("orders:order_list")
        else:
            messages.error(request, "Could not update the order. Please check the form.")

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
        "can_edit": user_can_edit_order(request.user, order),
        "can_decide": user_can_decide_order(request.user, order),
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
            else:
                order.order_type = Order.ORDER_TYPE_TEACHER

            order.save()

            messages.success(request, f"Order {order.id} was created successfully.")
            return redirect("orders:order_list")
    else:
        form = OrderCreateForm(user=request.user)

    context = {
        "form": form,
        "page_title": "Create Order",
        "submit_label": "Create order",
    }
    return render(request, "orders/order_form.html", context)


@login_required
def order_edit(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related("user", "decided_by"),
        pk=order_id,
    )

    if not user_can_view_order(request.user, order):
        raise Http404("You do not have permission to view this order.")

    if not user_can_edit_order(request.user, order):
        raise Http404("You do not have permission to edit this order.")

    if request.method == "POST":
        form = OrderEditForm(request.POST, instance=order, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Order {order.id} was updated successfully.")
            return redirect("orders:order_list")
    else:
        form = OrderEditForm(instance=order, user=request.user)

    context = {
        "form": form,
        "order": order,
        "page_title": f"Edit Order {order.id}",
        "submit_label": "Save changes",
    }
    return render(request, "orders/order_form.html", context)


@login_required
def order_decide(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related("user", "decided_by"),
        pk=order_id,
    )

    if not user_can_decide_order(request.user, order):
        raise Http404("You do not have permission to decide this order.")

    if request.method == "POST":
        form = OrderDecisionForm(request.POST)
        if form.is_valid():
            order.status = form.cleaned_data["decision"]
            order.decision_reason = form.cleaned_data["decision_reason"]
            order.decided_by = request.user
            order.decided_at = timezone.now()
            order.save()

            messages.success(request, f"Order {order.id} was updated successfully.")
            return redirect("orders:order_detail", order_id=order.id)
    else:
        form = OrderDecisionForm(
            initial={
                "decision": order.status if order.status in [
                    Order.STATUS_SUBMITTED,
                    Order.STATUS_APPROVED,
                    Order.STATUS_REJECTED,
                    Order.STATUS_REWORK,
                ] else Order.STATUS_SUBMITTED,
                "decision_reason": order.decision_reason,
            }
        )

    context = {
        "form": form,
        "order": order,
    }
    return render(request, "orders/order_decision_form.html", context)