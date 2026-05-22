from django.contrib import admin
from django.urls import path, include, reverse
from django.shortcuts import redirect
from allauth.account.views import LogoutView


def login_redirect(request):
    return redirect(reverse("openid_connect_login", kwargs={"provider_id": "authentik"}))


urlpatterns = [
    path("admin/", admin.site.urls),

    # Keep old names used by templates
    path("accounts/login/", login_redirect, name="login"),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),

    # allauth routes
    path("accounts/", include("allauth.urls")),

    # app routes
    path("", include("orders.urls")),
]