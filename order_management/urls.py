from django.conf import settings
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.urls import include, path, reverse
from allauth.account.views import LogoutView as AllauthLogoutView


def authentik_login_redirect(request):
    return redirect(reverse("openid_connect_login", kwargs={"provider_id": "authentik"}))


urlpatterns = [
    path("admin/", admin.site.urls),
]

if settings.USE_AUTHENTIK:
    urlpatterns += [
        path("accounts/login/", authentik_login_redirect, name="login"),
        path("accounts/logout/", AllauthLogoutView.as_view(), name="logout"),
        path("accounts/", include("allauth.urls")),
    ]
else:
    urlpatterns += [
        path(
            "accounts/login/",
            LoginView.as_view(template_name="registration/login.html"),
            name="login",
        ),
        path("accounts/logout/", LogoutView.as_view(), name="logout"),
    ]

urlpatterns += [
    path("", include("orders.urls")),
]
