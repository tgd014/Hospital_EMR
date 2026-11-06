
from django.db import models
from django.conf import settings
from django.utils import timezone
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

    chief_complaint = models.TextField(blank=True)
    history_of_present_illness = models.TextField(blank=True)
    past_medical_history = models.TextField(blank=True)
    past_surgical_history = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    current_medications = models.TextField(blank=True)
    clinical_examination = models.TextField(blank=True)
    assessment = models.TextField(blank=True)
    treatment_plan = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient} - {self.started_at}"


class RxNormMedication(models.Model):
    rxcui = models.CharField(max_length=20, unique=True, db_index=True)
    name = models.CharField(max_length=500, db_index=True)
    term_type = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.name} ({self.rxcui})"

    class Meta:
        ordering = ["name"]
        verbose_name = "RxNorm Medication"
        verbose_name_plural = "RxNorm Medication Catalog"


class MedicationPrescription(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("cancelled", "Cancelled"),
    ]

    ROUTE_CHOICES = [
        ("oral", "Oral"),
        ("topical", "Topical"),
        ("inhalation", "Inhalation"),
        ("intramuscular", "Intramuscular"),
        ("intravenous", "Intravenous"),
        ("subcutaneous", "Subcutaneous"),
        ("ophthalmic", "Ophthalmic"),
        ("otic", "Otic"),
        ("nasal", "Nasal"),
        ("rectal", "Rectal"),
        ("other", "Other"),
    ]

    encounter = models.ForeignKey(
        Encounter,
        on_delete=models.CASCADE,
        related_name="prescriptions",
    )
    rxnorm_medication = models.ForeignKey(
        RxNormMedication,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prescriptions",
    )
    medication_name = models.CharField(max_length=500)
    strength = models.CharField(max_length=100, blank=True)
    dosage = models.CharField(max_length=100)
    route = models.CharField(max_length=20, choices=ROUTE_CHOICES, default="oral")
    frequency = models.CharField(max_length=100)
    duration = models.CharField(max_length=100, blank=True)
    quantity = models.DecimalField(max_digits=8, decimal_places=2)
    instructions = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    prescribed_at = models.DateTimeField(default=timezone.now)
    prescribed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="medication_prescriptions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.medication_name} - {self.encounter.patient}"

    class Meta:
        ordering = ["-prescribed_at"]
        verbose_name = "Medication Prescription"
        verbose_name_plural = "Medication Prescriptions"
class ProcedureCatalog(models.Model):
    """Official ICD-10-PCS procedure titles used for searchable selection."""

    code = models.CharField(max_length=7, unique=True)
    abbreviated_title = models.CharField(max_length=200, blank=True)
    full_title = models.CharField(max_length=500)
    fiscal_year = models.CharField(max_length=4, default="2027")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.full_title}"

    class Meta:
        ordering = ["full_title"]
        verbose_name = "Procedure Catalog Entry"
        verbose_name_plural = "Procedure Catalog"


class EncounterProcedure(models.Model):
    PROCEDURE_CHOICES = [
        ("wound_dressing", "Wound dressing"),
        ("wound_debridement", "Wound debridement"),
        ("wound_suturing", "Wound suturing"),
        ("suture_removal", "Suture removal"),
        ("incision_and_drainage", "Incision and drainage"),
        ("biopsy", "Biopsy"),
        ("minor_operation", "Other minor operation"),
        ("appendectomy", "Appendectomy"),
        ("hernia_repair", "Hernia repair"),
        ("cesarean_section", "Caesarean section"),
        ("other_surgery", "Other surgery / operation"),
        ("other", "Other procedure"),
    ]

    STATUS_CHOICES = [
        ("planned", "Planned"),
        ("performed", "Performed"),
        ("cancelled", "Cancelled"),
    ]

    encounter = models.ForeignKey(
        Encounter,
        on_delete=models.CASCADE,
        related_name="procedures",
    )
    catalog_procedure = models.ForeignKey(
        ProcedureCatalog,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="encounter_procedures",
    )
    procedure_type = models.CharField(
        max_length=40,
        choices=PROCEDURE_CHOICES,
    )
    custom_name = models.CharField(max_length=250, blank=True)
    procedure_snapshot = models.CharField(max_length=500, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="planned",
    )
    notes = models.TextField(blank=True)
    recorded_at = models.DateTimeField(default=timezone.now)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_encounter_procedures",
    )

    @property
    def display_name(self):
        if self.procedure_snapshot:
            return self.procedure_snapshot
        if self.custom_name:
            return self.custom_name
        if self.catalog_procedure_id:
            return self.catalog_procedure.full_title
        return self.get_procedure_type_display()

    def __str__(self):
        return f"{self.display_name} - {self.encounter.patient}"

    class Meta:
        ordering = ["-recorded_at"]
        verbose_name = "Encounter Procedure"
        verbose_name_plural = "Encounter Procedures"

class VitalSigns(models.Model):
    encounter = models.ForeignKey(
        Encounter,
        on_delete=models.CASCADE,
        related_name="vital_signs",
    )

    systolic_bp = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    diastolic_bp = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    pulse = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    respiratory_rate = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    temperature = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
    )

    spo2 = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    weight_kg = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )

    height_cm = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )

    recorded_at = models.DateTimeField(default=timezone.now)

    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_vital_signs",
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def bmi(self):
        if self.weight_kg is None or self.height_cm is None:
            return None

        height_m = float(self.height_cm) / 100

        if height_m <= 0:
            return None

        return round(
            float(self.weight_kg) / (height_m ** 2),
            1,
        )

    def __str__(self):
        return (
            f"Vitals for {self.encounter.patient} "
            f"at {self.recorded_at:%Y-%m-%d %H:%M}"
        )

    class Meta:
        ordering = ["-recorded_at"]
        verbose_name = "Vital Signs"
        verbose_name_plural = "Vital Signs"


class TestOrder(models.Model):
    TEST_CATEGORIES = [
        ("laboratory", "Laboratory"),
        ("imaging", "Imaging"),
        ("other", "Other"),
    ]

    PRIORITY_CHOICES = [
        ("routine", "Routine"),
        ("urgent", "Urgent"),
        ("stat", "STAT"),
    ]

    STATUS_CHOICES = [
        ("ordered", "Ordered"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    encounter = models.ForeignKey(
        Encounter,
        on_delete=models.CASCADE,
        related_name="test_orders",
    )

    test_category = models.CharField(
        max_length=20,
        choices=TEST_CATEGORIES,
        default="laboratory",
    )

    test_name = models.CharField(max_length=200)

    lab_test = models.ForeignKey(
        "LabTest",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="test_orders",
    )

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default="routine",
    )

    clinical_indication = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ordered",
    )

    ordered_at = models.DateTimeField(default=timezone.now)

    ordered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ordered_test_orders",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"{self.test_name} - "
            f"{self.encounter.patient}"
        )

    class Meta:
        ordering = ["-ordered_at"]
        verbose_name = "Test Order"
        verbose_name_plural = "Test Orders"


class LabTest(models.Model):
    """
    Standardized laboratory and clinical test catalog based on LOINC.
    """

    loinc_code = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
    )

    long_common_name = models.CharField(max_length=500)
    short_name = models.CharField(max_length=255, blank=True)
    component = models.CharField(max_length=500, blank=True)
    property = models.CharField(max_length=100, blank=True)
    time_aspect = models.CharField(max_length=100, blank=True)
    system = models.CharField(max_length=255, blank=True)
    scale_type = models.CharField(max_length=100, blank=True)
    method_type = models.CharField(max_length=255, blank=True)
    test_class = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=50, blank=True)

    is_active = models.BooleanField(default=True)
    imported_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.loinc_code} - {self.long_common_name}"

    class Meta:
        ordering = ["long_common_name"]
        verbose_name = "Lab Test"
        verbose_name_plural = "Lab Test Catalog"


class LabResult(models.Model):
    """
    A manually entered laboratory result linked to a test order.

    A result can be saved as a draft while being entered. Submitting
    it marks it final. Corrections and audit history can be added
    through a separate workflow.
    """

    RESULT_TYPES = [
        ("numeric", "Numeric"),
        ("text", "Text"),
        ("positive_negative", "Positive / Negative"),
    ]

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("submitted", "Submitted"),
    ]

    ABNORMAL_FLAGS = [
        ("normal", "Normal"),
        ("abnormal", "Abnormal"),
        ("high", "High"),
        ("low", "Low"),
        ("critical", "Critical"),
        ("none", "Not specified"),
    ]

    test_order = models.ForeignKey(
        TestOrder,
        on_delete=models.CASCADE,
        related_name="lab_results",
    )

    result_type = models.CharField(
        max_length=20,
        choices=RESULT_TYPES,
        default="text",
    )

    result_value = models.TextField(
        help_text="Enter the measured value, finding, or interpretation."
    )

    units = models.CharField(
        max_length=100,
        blank=True,
    )

    reference_range = models.CharField(
        max_length=255,
        blank=True,
    )

    abnormal_flag = models.CharField(
        max_length=20,
        choices=ABNORMAL_FLAGS,
        default="none",
    )

    specimen_type = models.CharField(
        max_length=200,
        blank=True,
    )

    specimen_id = models.CharField(
        max_length=100,
        blank=True,
    )

    comments = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
    )

    entered_at = models.DateTimeField(default=timezone.now)

    entered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="entered_lab_results",
    )

    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submitted_lab_results",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_final(self):
        return self.status == "submitted"

    def __str__(self):
        return (
            f"Result for {self.test_order.test_name} - "
            f"{self.test_order.encounter.patient}"
        )

    class Meta:
        ordering = ["-entered_at"]
        verbose_name = "Lab Result"
        verbose_name_plural = "Lab Results"
