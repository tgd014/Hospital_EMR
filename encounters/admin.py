from django.contrib import admin
from .models import Encounter, LabTest, ProcedureCatalog


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


@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
    list_display = (
        "loinc_code",
        "long_common_name",
        "test_class",
        "system",
        "status",
        "is_active",
    )

    list_filter = (
        "test_class",
        "status",
        "is_active",
    )

    search_fields = (
        "loinc_code",
        "long_common_name",
        "short_name",
        "component",
    )

    list_per_page = 50


@admin.register(ProcedureCatalog)
class ProcedureCatalogAdmin(admin.ModelAdmin):
    list_display = ("code", "abbreviated_title", "fiscal_year", "is_active")
    list_filter = ("fiscal_year", "is_active")
    search_fields = ("code", "full_title", "abbreviated_title")
    list_per_page = 50
