from django.db import models
from patients.models import Patient


class Encounter(models.Model):

    ENCOUNTER_TYPES = [
        ("outpatient", "Outpatient"),
    ]

    STATUS_CHOICES = [
        ("open", "Open"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="encounters",
    )

    encounter_type = models.CharField(
        max_length=20,
        choices=ENCOUNTER_TYPES,
        default="outpatient",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="open",
    )

    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient} - {self.started_at}"
