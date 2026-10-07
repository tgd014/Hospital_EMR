from django.contrib import admin
from .models import Encounter


@admin.register(Encounter)
class EncounterAdmin(admin.ModelAdmin):
    list_display = (
        "patient",
        "encounter_type",
        "status",
        "started_at",
        "ended_at",
    )

    list_filter = (
        "encounter_type",
        "status",
    )

    search_fields = (
        "patient__medical_record_number",
        "patient__first_name",
        "patient__last_name",
    )
