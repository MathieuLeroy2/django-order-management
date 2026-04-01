from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import TeacherStudentLink
from .forms import (
    AdminInlineOrderUpdateForm,
    AdminOrderEditForm,
    OrderCreateForm,
    OrderDecisionForm,
    OrderEditForm,
)
from .models import AppSettings, Order, StoreRule

User = get_user_model()


def get_linked_student_ids_for_teacher(teacher):
    if teacher.role != User.ROLE_TEACHER:
        return []

    cached_ids = getattr(teacher, "_linked_student_ids_cache", None)
    if cached_ids is not None:
        return cached_ids

    linked_ids = list(
        TeacherStudentLink.objects.filter(teacher=teacher).values_list("student_id", flat=True)
    )
    teacher._linked_student_ids_cache = linked_ids
    return linked_ids


def get_filterable_users_for_user(user):
    if user.role == User.ROLE_ADMIN:
        return User.objects.all().order_by("name")

    if user.role == User.ROLE_TEACHER:
        linked_ids = get_linked_student_ids_for_teacher(user)
        return User.objects.filter(
            Q(id=user.id) | Q(id__in=linked_ids)
        ).distinct().order_by("name")

    return User.objects.filter(id=user.id).order_by("name")


def get_visible_orders_for_user(user):
    base_qs = Order.objects.select_related("user", "decided_by")

    if user.role == User.ROLE_ADMIN:
        return base_qs.all()

    if user.role == User.ROLE_TEACHER:
        linked_ids = get_linked_student_ids_for_teacher(user)
        return base_qs.filter(
            Q(user=user)
            | Q(user_id__in=linked_ids, order_type=Order.ORDER_TYPE_STUDENT)
        ).distinct()

    return base_qs.filter(user=user)


def user_can_view_order(user, order):
    if user.role == User.ROLE_ADMIN:
        return True

    if order.user_id == user.id:
        return True

    if user.role == User.ROLE_TEACHER:
        linked_ids = get_linked_student_ids_for_teacher(user)
        return (
            order.order_type == Order.ORDER_TYPE_STUDENT
            and order.user_id in linked_ids
        )

    return False


def user_can_edit_order(user, order):
    if user.role == User.ROLE_ADMIN:
        return True

    if order.user_id != user.id:
        return False

    if order.status in [Order.STATUS_APPROVED, Order.STATUS_REJECTED]:
        return False

    return True


def user_can_decide_order(user, order):
    if user.role == User.ROLE_ADMIN:
        return True

    if user.role != User.ROLE_TEACHER:
        return False

    # Once an order is approved or rejected, only admins may still change it
    if order.status in [Order.STATUS_APPROVED, Order.STATUS_REJECTED]:
        return False

    if order.order_type == Order.ORDER_TYPE_TEACHER and order.user_id == user.id:
        return True

    if order.order_type == Order.ORDER_TYPE_STUDENT:
        linked_ids = get_linked_student_ids_for_teacher(user)
        return order.user_id in linked_ids

    return False

def get_store_rule_status(store_name):
    return StoreRule.get_list_type_for_store(store_name) or "unlisted"

@login_required
def dashboard(request):
    context = {
        "user": request.user,
    }
    return render(request, "orders/dashboard.html", context)

@login_required
def store_overview(request):
    whitelisted_stores = StoreRule.objects.filter(
        list_type=StoreRule.LIST_TYPE_WHITELIST
    ).order_by("store_name")

    blacklisted_stores = StoreRule.objects.filter(
        list_type=StoreRule.LIST_TYPE_BLACKLIST
    ).order_by("store_name")

    context = {
        "whitelisted_stores": whitelisted_stores,
        "blacklisted_stores": blacklisted_stores,
    }
    return render(request, "orders/store_overview.html", context)

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
            new_status = form.cleaned_data["decision"]

            if new_status == Order.STATUS_SUBMITTED and order.is_store_blacklisted():
                messages.error(
                    request,
                    f"Order {order.id} uses a blacklisted store and cannot be submitted."
                )
            else:
                order.status = new_status
                order.decision_reason = form.cleaned_data["decision_reason"]
                order.decided_by = request.user
                order.decided_at = timezone.now()
                order.save()
                messages.success(request, f"Order {order.id} was updated successfully.")

            return_query = request.POST.get("return_query", "").strip()
            if return_query:
                return redirect(f"{request.path}?{return_query}")
            return redirect("orders:order_list")
        else:
            messages.error(request, "Could not update the order. Please check the form.")

    if request.method == "POST" and "inline_edit_order_id" in request.POST:
        order = get_object_or_404(
            Order.objects.select_related("user", "decided_by"),
            pk=request.POST.get("inline_edit_order_id"),
        )

        if request.user.role != User.ROLE_ADMIN:
            raise Http404("You do not have permission to inline edit this order.")

        form = AdminInlineOrderUpdateForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, f"Order {order.id} inline fields were updated successfully.")

            return_query = request.POST.get("return_query", "").strip()
            if return_query:
                return redirect(f"{request.path}?{return_query}")
            return redirect("orders:order_list")
        else:
            messages.error(request, f"Could not save inline changes for order {order.id}.")

    orders = get_visible_orders_for_user(request.user)

    search = request.GET.get("search", "").strip()
    status_filter = request.GET.get("status", "").strip()
    store_filter = request.GET.get("store", "").strip()
    ordernumber_filter = request.GET.get("ordernumber", "").strip()
    user_filter = request.GET.get("user_id", "").strip()
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

    if user_filter:
        orders = orders.filter(user_id=user_filter)

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

    settings_obj = AppSettings.get_solo()
    filterable_users = get_filterable_users_for_user(request.user)

    visible_total = orders.aggregate(total=Sum("total_price_excl_vat"))["total"] or Decimal("0.00")

    totals_by_user_id = {
        row["user_id"]: (row["total"] or Decimal("0.00"))
        for row in orders.values("user_id").annotate(total=Sum("total_price_excl_vat"))
    }

    spending_rows = []
    for visible_user in filterable_users:
        requested_total = totals_by_user_id.get(visible_user.id, Decimal("0.00"))
        is_over_limit = (
            settings_obj.soft_spending_limit is not None
            and requested_total > settings_obj.soft_spending_limit
        )

        spending_rows.append(
            {
                "user": visible_user,
                "requested_total": requested_total,
                "is_over_limit": is_over_limit,
            }
        )

    orders = list(orders)
    for order in orders:
        order.can_edit = user_can_edit_order(request.user, order)
        order.can_decide = user_can_decide_order(request.user, order)
        order.can_inline_admin_edit = request.user.role == User.ROLE_ADMIN
        order.store_rule_status = get_store_rule_status(order.store)

    context = {
        "orders": orders,
        "search": search,
        "status_filter": status_filter,
        "store_filter": store_filter,
        "ordernumber_filter": ordernumber_filter,
        "user_filter": user_filter,
        "finance_order_date_filter": finance_order_date_filter,
        "shipped_date_filter": shipped_date_filter,
        "received_date_filter": received_date_filter,
        "primary_sort": primary_sort,
        "secondary_sort": secondary_sort,
        "status_choices": Order.STATUS_CHOICES,
        "user_choices": filterable_users,
        "visible_total": visible_total,
        "soft_spending_limit": settings_obj.soft_spending_limit,
        "spending_rows": spending_rows,
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

            if request.user.role == User.ROLE_STUDENT:
                order.order_type = Order.ORDER_TYPE_STUDENT
            else:
                order.order_type = Order.ORDER_TYPE_TEACHER

            if order.is_store_blacklisted():
                form.add_error("store", "This store is blacklisted. Orders for blacklisted stores cannot be submitted.")
            else:
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

    form_class = AdminOrderEditForm if request.user.role == User.ROLE_ADMIN else OrderEditForm

    if request.method == "POST":
        form = form_class(request.POST, instance=order, user=request.user)
        if form.is_valid():
            updated_order = form.save(commit=False)

            if updated_order.status == Order.STATUS_SUBMITTED and updated_order.is_store_blacklisted():
                form.add_error("store", "This store is blacklisted. Orders for blacklisted stores cannot be submitted.")
            else:
                updated_order.save()
                messages.success(request, f"Order {order.id} was updated successfully.")
                return redirect("orders:order_list")
    else:
        form = form_class(instance=order, user=request.user)

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
            new_status = form.cleaned_data["decision"]

            if new_status == Order.STATUS_SUBMITTED and order.is_store_blacklisted():
                form.add_error("decision", "This store is blacklisted. Orders for blacklisted stores cannot be submitted.")
            else:
                order.status = new_status
                order.decision_reason = form.cleaned_data["decision_reason"]
                order.decided_by = request.user
                order.decided_at = timezone.now()
                order.save()
                messages.success(request, f"Order {order.id} was updated successfully.")
                return redirect("orders:order_detail", order_id=order.id)
    else:
        form = OrderDecisionForm(
            initial={
                "decision": order.status
                if order.status in [
                    Order.STATUS_SUBMITTED,
                    Order.STATUS_APPROVED,
                    Order.STATUS_REJECTED,
                    Order.STATUS_REWORK,
                ]
                else Order.STATUS_SUBMITTED,
                "decision_reason": order.decision_reason,
            }
        )

    context = {
        "form": form,
        "order": order,
    }
    return render(request, "orders/order_decision_form.html", context)