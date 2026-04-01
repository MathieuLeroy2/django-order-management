from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


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


class TeacherStudentLink(models.Model):
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="managed_student_links",
        limit_choices_to={"role": User.ROLE_TEACHER},
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="teacher_links",
        limit_choices_to={"role": User.ROLE_STUDENT},
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["teacher", "student"],
                name="unique_teacher_student_link",
            )
        ]
        ordering = ["teacher__name", "student__name"]

    def clean(self):
        if self.teacher and self.teacher.role != User.ROLE_TEACHER:
            raise ValidationError({"teacher": "Selected user must have role Teacher."})

        if self.student and self.student.role != User.ROLE_STUDENT:
            raise ValidationError({"student": "Selected user must have role Student."})

    def __str__(self):
        return f"{self.teacher.name} -> {self.student.name}"