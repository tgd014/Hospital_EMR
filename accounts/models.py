from django.db import models
from django.contrib.auth.models import User


class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    can_view_patients = models.BooleanField(default=False)
    can_create_patients = models.BooleanField(default=False)
    can_view_encounters = models.BooleanField(default=False)
    can_create_encounters = models.BooleanField(default=False)

    def __str__(self):
        return self.name



class UserRole(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="hospital_role",
    )

    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name="users",
    )

    def __str__(self):
        return f"{self.user.username} - {self.role.name}"
