from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_ADMIN = "admin"
    ROLE_TEACHER = "teacher"
    ROLE_STUDENT = "student"

    ROLE_CHOICES = [
        (ROLE_ADMIN, "Admin"),
        (ROLE_TEACHER, "Teacher"),
        (ROLE_STUDENT, "Student"),
    ]

    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_STUDENT)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "name"]

    def __str__(self):
        return f"{self.name} ({self.email})"