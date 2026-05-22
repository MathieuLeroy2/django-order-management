from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

from .models import User


class AuthentikSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Maps Authentik OIDC users to the local Django User model.

    Authentik remains the identity provider.
    Django keeps app-specific fields such as role and teacher/student links.
    """

    def _get_authentik_data(self, sociallogin):
        extra = sociallogin.account.extra_data or {}

        username = (
            extra.get("preferred_username")
            or extra.get("nickname")
            or extra.get("username")
            or extra.get("sub")
        )

        email = extra.get("email") or ""
        name = extra.get("name") or username or ""

        groups = extra.get("groups") or []
        if isinstance(groups, str):
            groups = [groups]

        return {
            "username": username,
            "email": email,
            "name": name,
            "groups": groups,
        }

    def _sync_user_fields(self, user, data):
        if data["username"]:
            user.username = data["username"]

        user.email = data["email"]
        user.name = data["name"]

        groups = set(data["groups"])

        if "bestellingen-admin" in groups:
            user.role = User.ROLE_ADMIN
            user.is_staff = True
        elif "bestellingen-teacher" in groups:
            user.role = User.ROLE_TEACHER
            user.is_staff = False
        else:
            user.role = User.ROLE_STUDENT
            user.is_staff = False

        return user

    def pre_social_login(self, request, sociallogin):
        """
        Link an Authentik login to an existing Django user when possible.
        This prevents duplicate users when a local user already exists.
        """
        if sociallogin.is_existing:
            return

        data = self._get_authentik_data(sociallogin)
        UserModel = get_user_model()

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
        """
        Populate new users created through Authentik.
        """
        user = super().populate_user(request, sociallogin, data)
        authentik_data = self._get_authentik_data(sociallogin)
        return self._sync_user_fields(user, authentik_data)

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        authentik_data = self._get_authentik_data(sociallogin)
        self._sync_user_fields(user, authentik_data)
        user.save()
        return user