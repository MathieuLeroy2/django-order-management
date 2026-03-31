from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import OrderCreateForm, OrderDecisionForm, OrderEditForm
from .models import Order
from django.urls import reverse


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

    if order.status in [Order.STATUS_APPROVED, Order.STATUS_REJECTED]:
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

            query_string = request.POST.get("return_query", "").strip()
            redirect_url = reverse("orders:order_list")

            if query_string:
                redirect_url = f"{redirect_url}?{query_string}"

            return redirect(redirect_url)
        else:
            messages.error(request, "Could not update the order. Please check the form.")

    orders = get_visible_orders_for_user(request.user)

    search = request.GET.get("search", "").strip()
    status_filter = request.GET.get("status", "").strip()
    store_filter = request.GET.get("store", "").strip()
    ordernumber_filter = request.GET.get("ordernumber", "").strip()
    ordernumber_presence_filter = request.GET.get("ordernumber_presence_filter", "").strip()
    finance_order_date_filter = request.GET.get("finance_order_date_filter", "").strip()
    shipped_date_filter = request.GET.get("shipped_date_filter", "").strip()
    received_date_filter = request.GET.get("received_date_filter", "").strip()
    primary_sort = request.GET.get("primary_sort", "store").strip()
    secondary_sort = request.GET.get("secondary_sort", "-created_at").strip()

    if search:
        orders = orders.filter(
            Q(short_description__icontains=search)
            | Q(store__icontains=search)
            | Q(article_number__icontains=search)
            | Q(ordernumber__icontains=search)
            | Q(student_remarks__icontains=search)
            | Q(teacher_remarks__icontains=search)
            | Q(decision_reason__icontains=search)
            | Q(user__name__icontains=search)
            | Q(user__email__icontains=search)
            | Q(purchase_request_number__icontains=search)
        )

    if status_filter:
        orders = orders.filter(status=status_filter)

    if store_filter:
        orders = orders.filter(store__icontains=store_filter)

    if ordernumber_filter:
        orders = orders.filter(ordernumber=ordernumber_filter)

    if ordernumber_presence_filter == "empty":
        orders = orders.filter(ordernumber="")
    elif ordernumber_presence_filter == "filled":
        orders = orders.exclude(ordernumber="")

    if finance_order_date_filter == "empty":
        orders = orders.filter(finance_order_date__isnull=True)
    elif finance_order_date_filter == "filled":
        orders = orders.filter(finance_order_date__isnull=False)

    if shipped_date_filter == "empty":
        orders = orders.filter(shipped_date__isnull=True)
    elif shipped_date_filter == "filled":
        orders = orders.filter(shipped_date__isnull=False)

    if received_date_filter == "empty":
        orders = orders.filter(received_date__isnull=True)
    elif received_date_filter == "filled":
        orders = orders.filter(received_date__isnull=False)

    allowed_sort_fields = {
        "created_at": "created_at",
        "-created_at": "-created_at",
        "status": "status",
        "-status": "-status",
        "store": "store",
        "-store": "-store",
        "ordernumber": "ordernumber",
        "-ordernumber": "-ordernumber",
        "quantity": "quantity",
        "-quantity": "-quantity",
        "total_price_excl_vat": "total_price_excl_vat",
        "-total_price_excl_vat": "-total_price_excl_vat",
        "finance_order_date": "finance_order_date",
        "-finance_order_date": "-finance_order_date",
        "shipped_date": "shipped_date",
        "-shipped_date": "-shipped_date",
        "received_date": "received_date",
        "-received_date": "-received_date",
        "user__name": "user__name",
        "-user__name": "-user__name",
    }

    primary_sort_value = allowed_sort_fields.get(primary_sort, "store")
    secondary_sort_value = allowed_sort_fields.get(secondary_sort, "-created_at")

    if primary_sort_value == secondary_sort_value:
        orders = orders.order_by(primary_sort_value)
    else:
        orders = orders.order_by(primary_sort_value, secondary_sort_value)

    context = {
        "orders": orders,
        "search": search,
        "status_filter": status_filter,
        "store_filter": store_filter,
        "ordernumber_filter": ordernumber_filter,
        "ordernumber_presence_filter": ordernumber_presence_filter,
        "finance_order_date_filter": finance_order_date_filter,
        "shipped_date_filter": shipped_date_filter,
        "received_date_filter": received_date_filter,
        "primary_sort": primary_sort,
        "secondary_sort": secondary_sort,
        "status_choices": Order.STATUS_CHOICES,
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