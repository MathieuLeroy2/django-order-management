from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.core.exceptions import PermissionDenied

from .models import User


ALLOWED_GROUPS = {
    "bestellingenNoord-admin",
    "bestellingenNoord-teacher",
    "bestellingenNoord-student",
}


class AuthentikSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Maps Authentik OIDC users to the local Django User model.

    Authentik handles login.
    Django keeps app-specific fields such as role and teacher/student links.

    Users are only allowed into the application if they are a member of one
    of the explicitly allowed Authentik groups.
    """

    def _get_authentik_data(self, sociallogin):
        extra = sociallogin.account.extra_data or {}

        userinfo = extra.get("userinfo") or {}
        id_token = extra.get("id_token") or {}

        userinfo = extra.get("userinfo") or {}
        id_token = extra.get("id_token") or {}

        username = (
            userinfo.get("preferred_username")
            or id_token.get("preferred_username")
            or userinfo.get("username")
            or id_token.get("username")
            or userinfo.get("nickname")
            or id_token.get("nickname")
            or userinfo.get("email")
            or id_token.get("email")
            or userinfo.get("sub")
            or id_token.get("sub")
            or extra.get("preferred_username")
            or extra.get("username")
            userinfo.get("preferred_username")
            or id_token.get("preferred_username")
            or userinfo.get("username")
            or id_token.get("username")
            or userinfo.get("nickname")
            or id_token.get("nickname")
            or userinfo.get("email")
            or id_token.get("email")
            or userinfo.get("sub")
            or id_token.get("sub")
            or extra.get("preferred_username")
            or extra.get("username")
            or extra.get("nickname")
            or extra.get("email")
            or extra.get("email")
            or extra.get("sub")
        )

        if username:
            username = str(username).strip()

        email = (
            userinfo.get("email")
            or id_token.get("email")
            or extra.get("email")
            or ""
        )

        name = (
            userinfo.get("name")
            or id_token.get("name")
            or extra.get("name")
            or username
            or ""
        )
        if username:
            username = str(username).strip()

        email = (
            userinfo.get("email")
            or id_token.get("email")
            or extra.get("email")
            or ""
        )

        name = (
            userinfo.get("name")
            or id_token.get("name")
            or extra.get("name")
            or username
            or ""
        )

        groups = (
            userinfo.get("groups")
            or id_token.get("groups")
            or extra.get("groups")
            or []
        )

        groups = (
            userinfo.get("groups")
            or id_token.get("groups")
            or extra.get("groups")
            or []
        )

        if isinstance(groups, str):
            groups = [groups]
        elif not isinstance(groups, list):
            groups = list(groups) if groups else []
        elif not isinstance(groups, list):
            groups = list(groups) if groups else []

        return {
            "username": username,
            "email": email,
            "name": name,
            "groups": groups,
        }

    def _has_allowed_group(self, data):
        return bool(set(data["groups"]) & ALLOWED_GROUPS)

    def _has_allowed_group(self, data):
        return bool(set(data["groups"]) & ALLOWED_GROUPS)

    def _sync_user_fields(self, user, data):
        groups = set(data["groups"])

        if not self._has_allowed_group(data):
            user.is_active = False
            raise PermissionDenied(
                "You are authenticated in Authentik, but you are not assigned "
                "to one of the allowed Bestellingen groups."
            )

        groups = set(data["groups"])

        if not self._has_allowed_group(data):
            user.is_active = False
            raise PermissionDenied(
                "You are authenticated in Authentik, but you are not assigned "
                "to one of the allowed Bestellingen groups."
            )

        if data["username"]:
            user.username = data["username"]

        user.email = data["email"] or ""
        user.name = data["name"] or ""
        user.is_active = True
        user.email = data["email"] or ""
        user.name = data["name"] or ""
        user.is_active = True

        if "bestellingenNoord-admin" in groups:
            user.role = User.ROLE_ADMIN
            user.is_staff = True
            user.is_superuser = True
        elif "bestellingenNoord-teacher" in groups:
            user.role = User.ROLE_TEACHER
            user.is_staff = False
            user.is_superuser = False
        elif "bestellingenNoord-student" in groups:
            user.role = User.ROLE_STUDENT
            user.is_staff = False
            user.is_superuser = False
        else:
            user.is_active = False
            raise PermissionDenied(
                "You are not assigned to an allowed Bestellingen role."
            )

        return user

    def pre_social_login(self, request, sociallogin):
        data = self._get_authentik_data(sociallogin)

        if not self._has_allowed_group(data):
            raise PermissionDenied(
                "You are authenticated in Authentik, but you are not allowed "
                "to access this application."
            )


        if not self._has_allowed_group(data):
            raise PermissionDenied(
                "You are authenticated in Authentik, but you are not allowed "
                "to access this application."
            )

        UserModel = get_user_model()

        if sociallogin.is_existing:
            user = sociallogin.user
            self._sync_user_fields(user, data)
            user.save()
            return

        if sociallogin.is_existing:
            user = sociallogin.user
            self._sync_user_fields(user, data)
            user.save()
            return

        existing_user = None

        if data["username"]:
            existing_user = UserModel.objects.filter(
                username__iexact=data["username"]
            ).first()

        if existing_user is None and data["email"]:
            existing_user = UserModel.objects.filter(
                email__iexact=data["email"]
            ).first()

        if existing_user:
            self._sync_user_fields(existing_user, data)
            existing_user.save()
            sociallogin.connect(request, existing_user)

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        authentik_data = self._get_authentik_data(sociallogin)
        return self._sync_user_fields(user, authentik_data)

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        authentik_data = self._get_authentik_data(sociallogin)
        self._sync_user_fields(user, authentik_data)
        user.save()
        return user
