
from django.contrib import admin
from .models import (
    Role,
    UserRole,
    PatientAccount,
    PatientRegistrationRequest,
)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "can_view_patients",
        "can_create_patients",
        "can_view_encounters",
        "can_create_encounters",
        "can_prescribe_medications",
        "can_record_procedures",
    )
    search_fields = ("name",)


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("user", "role")
    list_filter = ("role",)
    search_fields = ("user__username",)


@admin.register(PatientAccount)
class PatientAccountAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "patient",
        "linked_at",
    )
    search_fields = (
        "user__username",
        "patient__medical_record_number",
        "patient__first_name",
        "patient__last_name",
    )
    readonly_fields = ("linked_at",)


@admin.register(PatientRegistrationRequest)
class PatientRegistrationRequestAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "email",
        "phone",
        "status",
        "submitted_at",
        "reviewed_by",
    )

    list_filter = (
        "status",
        "submitted_at",
    )

    search_fields = (
        "first_name",
        "last_name",
        "email",
        "phone",
        "medical_record_number",
        "user__username",
    )

    readonly_fields = (
        "user",
        "submitted_at",
        "reviewed_at",
        "reviewed_by",
    )

    ordering = ("status", "-submitted_at")
