from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect


def login_redirect(request):
    return redirect("/accounts/oidc/authentik/login/")


urlpatterns = [
    path("admin/", admin.site.urls),

    # Keep the normal Django login URL, but immediately send users to Authentik.
    path("accounts/login/", login_redirect, name="login"),

    # allauth provides the OIDC login/callback/logout routes.
    path("accounts/", include("allauth.urls")),

    path("", include("orders.urls")),
]