
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone


class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    can_view_patients = models.BooleanField(default=False)
    can_create_patients = models.BooleanField(default=False)
    can_view_encounters = models.BooleanField(default=False)
    can_create_encounters = models.BooleanField(default=False)
    can_prescribe_medications = models.BooleanField(default=False)
    can_record_procedures = models.BooleanField(default=False)

    # Test ordering and laboratory permissions
    can_order_tests = models.BooleanField(default=False)
    can_view_lab_worklist = models.BooleanField(default=False)
    can_enter_lab_results = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class UserRole(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
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


class PatientAccount(models.Model):
    """
    Links one patient login account to one hospital Patient record.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient_account",
    )

    patient = models.OneToOneField(
        "patients.Patient",
        on_delete=models.PROTECT,
        related_name="portal_account",
    )

    linked_at = models.DateTimeField(default=timezone.now)

    def clean(self):
        super().clean()

        if self.user_id:
            if self.user.is_staff or self.user.is_superuser:
                raise ValidationError(
                    "Hospital staff accounts cannot be linked "
                    "to patient portal accounts."
                )

            if UserRole.objects.filter(user=self.user).exists():
                raise ValidationError(
                    "Users with hospital staff roles cannot be "
                    "linked to patient portal accounts."
                )

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.patient.medical_record_number}"
        )


class PatientRegistrationRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending Verification"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient_registration_request",
    )

    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    phone = models.CharField(max_length=30)
    email = models.EmailField()

    # Optional information to help staff locate the existing record.
    # This is NOT used to grant automatic access.
    medical_record_number = models.CharField(
        max_length=50,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )

    submitted_at = models.DateTimeField(auto_now_add=True)

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_patient_registrations",
    )

    reviewed_at = models.DateTimeField(null=True, blank=True)

    staff_notes = models.TextField(blank=True)

    def __str__(self):
        return (
            f"{self.first_name} {self.last_name} "
            f"- {self.get_status_display()}"
        )
