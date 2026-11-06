
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from decimal import Decimal, InvalidOperation
from django.views.decorators.http import require_http_methods

from accounts.permissions import user_has_permission
from patients.models import Patient
from .models import (
    Encounter, VitalSigns, TestOrder, LabTest, LabResult,
    MedicationPrescription, RxNormMedication, EncounterProcedure,
    ProcedureCatalog,
)


@login_required
def encounter_create(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)

    if not user_has_permission(request.user, "can_create_encounters"):
        return render(
            request,
            "permission_denied.html",
            {"message": "You do not have permission to create encounters."},
            status=403,
        )

    if request.method == "POST":
        encounter = Encounter.objects.create(
            patient=patient,
            encounter_type=request.POST.get("encounter_type", "outpatient"),
            status="open",
            started_at=timezone.now(),
            chief_complaint=request.POST.get("chief_complaint", "").strip(),
            history_of_present_illness=request.POST.get(
                "history_of_present_illness", ""
            ).strip(),
            past_medical_history=request.POST.get(
                "past_medical_history", ""
            ).strip(),
            past_surgical_history=request.POST.get(
                "past_surgical_history", ""
            ).strip(),
            allergies=request.POST.get("allergies", "").strip(),
            current_medications=request.POST.get(
                "current_medications", ""
            ).strip(),
            clinical_examination=request.POST.get(
                "clinical_examination", ""
            ).strip(),
            assessment=request.POST.get("assessment", "").strip(),
            treatment_plan=request.POST.get("treatment_plan", "").strip(),
        )

        return redirect("encounter_detail", encounter_id=encounter.id)

    return render(
        request,
        "encounters/encounter_create.html",
        {"patient": patient},
    )


@login_required
@login_required
def encounter_detail(request, encounter_id):
    encounter = get_object_or_404(
        Encounter.objects.select_related("patient"),
        id=encounter_id,
    )

    if not user_has_permission(request.user, "can_view_encounters"):
        return render(
            request,
            "permission_denied.html",
            {"message": "You do not have permission to view encounters."},
            status=403,
        )

    if request.method == "POST":
        if not user_has_permission(request.user, "can_create_encounters"):
            return render(
                request,
                "permission_denied.html",
                {"message": "You do not have permission to edit encounters."},
                status=403,
            )

        if encounter.status != "open":
            return render(
                request,
                "permission_denied.html",
                {"message": "This encounter is closed and cannot be edited."},
                status=403,
            )

        fields = [
            "chief_complaint",
            "history_of_present_illness",
            "past_medical_history",
            "past_surgical_history",
            "allergies",
            "current_medications",
            "clinical_examination",
            "assessment",
            "treatment_plan",
        ]

        for field in fields:
            setattr(encounter, field, request.POST.get(field, "").strip())

        encounter.save(update_fields=fields)
        return redirect("encounter_detail", encounter_id=encounter.id)

    vital_signs = encounter.vital_signs.select_related("recorded_by").all()
    prescriptions = encounter.prescriptions.select_related("prescribed_by").all()
    procedures = encounter.procedures.select_related(
        "recorded_by", "catalog_procedure"
    ).all()
    test_orders = encounter.test_orders.select_related(
        "ordered_by", "lab_test"
    ).prefetch_related("lab_results").all()

    clinical_sections = [
        ("Chief Complaint", encounter.chief_complaint),
        ("History of Present Illness", encounter.history_of_present_illness),
        ("Past Medical History", encounter.past_medical_history),
        ("Past Surgical History", encounter.past_surgical_history),
        ("Allergies", encounter.allergies),
        ("Current Medications", encounter.current_medications),
        ("Clinical Examination", encounter.clinical_examination),
        ("Assessment / Diagnosis", encounter.assessment),
        ("Treatment Plan", encounter.treatment_plan),
    ]

    return render(
        request,
        "encounters/encounter_detail.html",
        {
            "encounter": encounter,
            "patient": encounter.patient,
            "clinical_sections": clinical_sections,
            "vital_signs": vital_signs,
            "prescriptions": prescriptions,
            "can_prescribe_medications": user_has_permission(
                request.user,
                "can_prescribe_medications",
            ),
            "procedures": procedures,
            "can_record_procedures": user_has_permission(
                request.user,
                "can_record_procedures",
            ),
            "test_orders": test_orders,
        },
    )

@login_required
@require_http_methods(["GET"])
def rxnorm_medication_search(request):
    if not (
        user_has_permission(request.user, "can_view_encounters")
        and user_has_permission(request.user, "can_prescribe_medications")
    ):
        return JsonResponse({"results": []}, status=403)

    query = request.GET.get("q", "").strip()
    results = []
    if len(query) >= 2:
        results = list(
            RxNormMedication.objects.filter(name__icontains=query)
            .order_by("name")[:20]
            .values("rxcui", "name", "term_type")
        )
    return JsonResponse({"results": results})


@login_required
@require_http_methods(["GET", "POST"])
def medication_prescription_create(request, encounter_id):
    encounter = get_object_or_404(
        Encounter.objects.select_related("patient"), id=encounter_id
    )

    if not (
        user_has_permission(request.user, "can_view_encounters")
        and user_has_permission(request.user, "can_prescribe_medications")
    ):
        return render(
            request,
            "permission_denied.html",
            {"message": "You do not have permission to prescribe medication."},
            status=403,
        )

    if encounter.status != "open":
        return render(
            request,
            "permission_denied.html",
            {"message": "Medication cannot be prescribed for a closed encounter."},
            status=403,
        )

    if request.method == "POST":
        medication_name = request.POST.get("medication_name", "").strip()
        rxnorm_id = request.POST.get("rxnorm_medication_id", "").strip()
        rxnorm_medication = None
        if rxnorm_id:
            rxnorm_medication = get_object_or_404(RxNormMedication, rxcui=rxnorm_id)
            medication_name = rxnorm_medication.name
        dosage = request.POST.get("dosage", "").strip()
        frequency = request.POST.get("frequency", "").strip()
        quantity = request.POST.get("quantity", "").strip()
        route = request.POST.get("route", "oral").strip()
        valid_routes = {choice[0] for choice in MedicationPrescription.ROUTE_CHOICES}

        try:
            quantity_value = Decimal(quantity)
            if not quantity_value.is_finite() or quantity_value <= 0:
                raise InvalidOperation
        except (InvalidOperation, TypeError):
            quantity_value = None

        if not medication_name or not dosage or not frequency or quantity_value is None:
            error = "Enter a medication, dosage, frequency, and a quantity greater than zero."
        elif route not in valid_routes:
            error = "Select a valid route of administration."
        else:
            MedicationPrescription.objects.create(
                encounter=encounter,
                medication_name=medication_name,
                rxnorm_medication=rxnorm_medication,
                strength=request.POST.get("strength", "").strip(),
                dosage=dosage,
                route=route,
                frequency=frequency,
                duration=request.POST.get("duration", "").strip(),
                quantity=quantity_value,
                instructions=request.POST.get("instructions", "").strip(),
                prescribed_by=request.user,
            )
            return redirect("encounter_detail", encounter_id=encounter.id)

        return render(
            request,
            "encounters/medication_prescription_create.html",
            {
                "encounter": encounter,
                "patient": encounter.patient,
                "error": error,
                "route_choices": MedicationPrescription.ROUTE_CHOICES,
                "selected_route": route if route in valid_routes else "oral",
            },
        )

    return render(
        request,
        "encounters/medication_prescription_create.html",
        {
            "encounter": encounter,
            "patient": encounter.patient,
            "route_choices": MedicationPrescription.ROUTE_CHOICES,
            "selected_route": "oral",
        },
    )

@login_required
@require_http_methods(["GET", "POST"])
def procedure_create(request, encounter_id):
    encounter = get_object_or_404(
        Encounter.objects.select_related("patient"),
        id=encounter_id,
    )

    if not (
        user_has_permission(request.user, "can_view_encounters")
        and user_has_permission(request.user, "can_record_procedures")
    ):
        return render(
            request,
            "permission_denied.html",
            {"message": "You do not have permission to record procedures."},
            status=403,
        )

    if encounter.status != "open":
        return render(
            request,
            "permission_denied.html",
            {"message": "Procedures cannot be added to a closed encounter."},
            status=403,
        )

    statuses = EncounterProcedure.STATUS_CHOICES

    if request.method == "POST":
        catalog_code = request.POST.get("catalog_procedure_code", "").strip()
        custom_name = request.POST.get("custom_name", "").strip()
        legacy_procedure_type = request.POST.get("procedure_type", "").strip()
        status = request.POST.get("status", "planned").strip()
        notes = request.POST.get("notes", "").strip()

        valid_types = {choice[0] for choice in EncounterProcedure.PROCEDURE_CHOICES}
        valid_statuses = {choice[0] for choice in statuses}
        custom_types = {"other_surgery", "other"}
        catalog_procedure = None
        procedure_type = "other"
        procedure_snapshot = ""
        error = None

        if catalog_code and custom_name:
            error = "Choose a catalog procedure or enter a custom procedure name, not both."
        elif catalog_code:
            try:
                catalog_procedure = ProcedureCatalog.objects.get(
                    code=catalog_code,
                    is_active=True,
                )
            except ProcedureCatalog.DoesNotExist:
                error = "Choose a valid procedure from the catalog."
            else:
                procedure_snapshot = catalog_procedure.full_title
        elif custom_name:
            if len(custom_name) > 250:
                error = "The custom procedure name must be 250 characters or fewer."
            else:
                procedure_snapshot = custom_name
        elif legacy_procedure_type in valid_types:
            procedure_type = legacy_procedure_type
            if procedure_type in custom_types:
                error = "Enter the procedure name."
        else:
            error = "Search for a catalog procedure or enter a custom procedure name."

        if status not in valid_statuses:
            error = "Choose a valid procedure status."

        if not error:
            EncounterProcedure.objects.create(
                encounter=encounter,
                procedure_type=procedure_type,
                custom_name=custom_name,
                catalog_procedure=catalog_procedure,
                procedure_snapshot=procedure_snapshot,
                status=status,
                notes=notes,
                recorded_by=request.user,
            )
            return redirect(
                "encounter_detail",
                encounter_id=encounter.id,
            )

        return render(
            request,
            "encounters/procedure_create.html",
            {
                "encounter": encounter,
                "patient": encounter.patient,
                "statuses": statuses,
                "error": error,
                "custom_name": custom_name,
                "selected_status": status if status in valid_statuses else "planned",
            },
        )

    return render(
        request,
        "encounters/procedure_create.html",
        {
            "encounter": encounter,
            "patient": encounter.patient,
            "statuses": statuses,
            "selected_status": "planned",
        },
    )


@login_required
@require_http_methods(["GET"])
def procedure_catalog_search(request):
    if not (
        user_has_permission(request.user, "can_view_encounters")
        and user_has_permission(request.user, "can_record_procedures")
    ):
        return JsonResponse({"results": []}, status=403)

    query = request.GET.get("q", "").strip()
    if len(query) < 2:
        return JsonResponse({"results": []})

    procedures = (
        ProcedureCatalog.objects.filter(is_active=True)
        .filter(
            Q(code__startswith=query.upper())
            | Q(full_title__icontains=query)
            | Q(abbreviated_title__icontains=query)
        )
        .order_by("full_title")[:20]
        .values("code", "full_title", "abbreviated_title")
    )
    return JsonResponse({"results": list(procedures)})
@login_required
def vitals_create(request, encounter_id):
    encounter = get_object_or_404(
        Encounter.objects.select_related("patient"),
        id=encounter_id,
    )

    if not user_has_permission(request.user, "can_view_encounters"):
        return render(
            request,
            "permission_denied.html",
            {"message": "You do not have permission to view encounters."},
            status=403,
        )

    if request.method == "POST":
        if not user_has_permission(request.user, "can_create_encounters"):
            return render(
                request,
                "permission_denied.html",
                {"message": "You do not have permission to record vital signs."},
                status=403,
            )

        if encounter.status != "open":
            return render(
                request,
                "permission_denied.html",
                {"message": "Vitals cannot be added to a closed encounter."},
                status=403,
            )

        def optional_value(field_name):
            value = request.POST.get(field_name, "").strip()
            return value or None

        vital_fields = [
            "systolic_bp",
            "diastolic_bp",
            "pulse",
            "respiratory_rate",
            "temperature",
            "spo2",
            "weight_kg",
            "height_cm",
        ]

        values = {field: optional_value(field) for field in vital_fields}

        if not any(value is not None for value in values.values()):
            return render(
                request,
                "encounters/vitals.html",
                {
                    "encounter": encounter,
                    "patient": encounter.patient,
                    "readings": encounter.vital_signs.select_related(
                        "recorded_by"
                    ).all(),
                    "vital_fields": get_vital_fields(),
                    "error": "Enter at least one vital sign before saving.",
                },
            )

        try:
            for field in [
                "systolic_bp",
                "diastolic_bp",
                "pulse",
                "respiratory_rate",
            ]:
                if values[field] is not None:
                    values[field] = int(values[field])

            for field in [
                "temperature",
                "spo2",
                "weight_kg",
                "height_cm",
            ]:
                if values[field] is not None:
                    values[field] = float(values[field])

            VitalSigns.objects.create(
                encounter=encounter,
                recorded_by=request.user,
                **values,
                notes=request.POST.get("notes", "").strip(),
            )

        except (ValueError, TypeError):
            return render(
                request,
                "encounters/vitals.html",
                {
                    "encounter": encounter,
                    "patient": encounter.patient,
                    "readings": encounter.vital_signs.select_related(
                        "recorded_by"
                    ).all(),
                    "vital_fields": get_vital_fields(),
                    "error": "Please enter valid numeric values.",
                },
            )

        return redirect("vitals_create", encounter_id=encounter.id)

    return render(
        request,
        "encounters/vitals.html",
        {
            "encounter": encounter,
            "patient": encounter.patient,
            "readings": encounter.vital_signs.select_related(
                "recorded_by"
            ).all(),
            "vital_fields": get_vital_fields(),
        },
    )


@login_required
def test_order_create(request, encounter_id):
    encounter = get_object_or_404(
        Encounter.objects.select_related("patient"),
        id=encounter_id,
    )

    if not user_has_permission(request.user, "can_order_tests"):
        return render(
            request,
            "permission_denied.html",
            {"message": "You do not have permission to order tests."},
            status=403,
        )

    if encounter.status != "open":
        return render(
            request,
            "permission_denied.html",
            {"message": "Tests cannot be ordered for a closed encounter."},
            status=403,
        )

    search_query = request.GET.get("q", "").strip()

    def render_order_form(error=None, selected_lab_test=None):
        lab_tests = LabTest.objects.none()

        if len(search_query) >= 2:
            lab_tests = (
                LabTest.objects.filter(is_active=True)
                .filter(
                    Q(loinc_code__icontains=search_query)
                    | Q(long_common_name__icontains=search_query)
                    | Q(short_name__icontains=search_query)
                    | Q(component__icontains=search_query)
                )
                .order_by("long_common_name")[:50]
            )

        return render(
            request,
            "encounters/test_order_create.html",
            {
                "encounter": encounter,
                "patient": encounter.patient,
                "error": error,
                "search_query": search_query,
                "lab_tests": lab_tests,
                "selected_lab_test": selected_lab_test,
            },
        )

    if request.method == "POST":
        lab_test_id = request.POST.get("lab_test_id", "").strip()
        test_name = request.POST.get("test_name", "").strip()
        lab_test = None

        if lab_test_id:
            try:
                lab_test = LabTest.objects.get(
                    id=lab_test_id,
                    is_active=True,
                )
            except (LabTest.DoesNotExist, ValueError, TypeError):
                return render_order_form(
                    error="Please select a valid active test from the catalog."
                )

            test_name = lab_test.long_common_name

        if not test_name:
            return render_order_form(
                error="Search for a catalog test and select it, or enter a test name."
            )

        test_category = request.POST.get("test_category", "laboratory")
        valid_categories = {
            choice[0] for choice in TestOrder.TEST_CATEGORIES
        }
        if test_category not in valid_categories:
            test_category = "laboratory"

        priority = request.POST.get("priority", "routine")
        valid_priorities = {
            choice[0] for choice in TestOrder.PRIORITY_CHOICES
        }
        if priority not in valid_priorities:
            priority = "routine"

        TestOrder.objects.create(
            encounter=encounter,
            lab_test=lab_test,
            test_category=test_category,
            test_name=test_name,
            priority=priority,
            clinical_indication=request.POST.get(
                "clinical_indication", ""
            ).strip(),
            notes=request.POST.get("notes", "").strip(),
            status="ordered",
            ordered_at=timezone.now(),
            ordered_by=request.user,
        )

        return redirect("encounter_detail", encounter_id=encounter.id)

    return render_order_form()


@login_required
def lab_worklist(request):
    if not user_has_permission(request.user, "can_view_lab_worklist"):
        return render(
            request,
            "permission_denied.html",
            {"message": "You do not have permission to view the lab worklist."},
            status=403,
        )

    test_orders = (
        TestOrder.objects.filter(
            test_category="laboratory",
            status__in=["ordered", "in_progress", "completed"],
        )
        .select_related("encounter__patient", "ordered_by", "lab_test")
        .prefetch_related("lab_results")
        .order_by("priority", "ordered_at")
    )

    return render(
        request,
        "lab/worklist.html",
        {"test_orders": test_orders},
    )


@login_required
@require_http_methods(["GET", "POST"])
def lab_result_create(request, test_order_id):
    if not user_has_permission(request.user, "can_enter_lab_results"):
        return render(
            request,
            "permission_denied.html",
            {"message": "You do not have permission to enter lab results."},
            status=403,
        )

    test_order = get_object_or_404(
        TestOrder.objects.select_related("encounter__patient", "lab_test"),
        id=test_order_id,
        test_category="laboratory",
    )

    if test_order.status == "cancelled":
        return render(
            request,
            "permission_denied.html",
            {"message": "A cancelled test order cannot receive results."},
            status=403,
        )

    existing_result = (
        test_order.lab_results.filter(status="submitted")
        .order_by("-submitted_at")
        .first()
    )

    if existing_result:
        return render(
            request,
            "lab/result_detail.html",
            {
                "test_order": test_order,
                "result": existing_result,
                "already_submitted": True,
            },
        )

    draft_result = test_order.lab_results.filter(
        status="draft",
        entered_by=request.user,
    ).first()

    if request.method == "POST":
        result_type = request.POST.get("result_type", "text")
        valid_result_types = {
            choice[0] for choice in LabResult.RESULT_TYPES
        }

        if result_type not in valid_result_types:
            result_type = "text"

        result_value = request.POST.get("result_value", "").strip()

        if not result_value:
            return render(
                request,
                "lab/result_form.html",
                {
                    "test_order": test_order,
                    "result": draft_result,
                    "error": "Enter a result before submitting.",
                    "result_types": LabResult.RESULT_TYPES,
                    "abnormal_flags": LabResult.ABNORMAL_FLAGS,
                },
            )

        if result_type == "numeric":
            try:
                float(result_value)
            except ValueError:
                return render(
                    request,
                    "lab/result_form.html",
                    {
                        "test_order": test_order,
                        "result": draft_result,
                        "error": "Enter a valid number for a numeric result.",
                        "result_types": LabResult.RESULT_TYPES,
                        "abnormal_flags": LabResult.ABNORMAL_FLAGS,
                    },
                )

        abnormal_flag = request.POST.get("abnormal_flag", "none")
        valid_flags = {choice[0] for choice in LabResult.ABNORMAL_FLAGS}
        if abnormal_flag not in valid_flags:
            abnormal_flag = "none"

        result_data = {
            "result_type": result_type,
            "result_value": result_value,
            "units": request.POST.get("units", "").strip(),
            "reference_range": request.POST.get(
                "reference_range", ""
            ).strip(),
            "abnormal_flag": abnormal_flag,
            "specimen_type": request.POST.get(
                "specimen_type", ""
            ).strip(),
            "specimen_id": request.POST.get(
                "specimen_id", ""
            ).strip(),
            "comments": request.POST.get("comments", "").strip(),
        }

        if draft_result:
            for field, value in result_data.items():
                setattr(draft_result, field, value)
            draft_result.status = "submitted"
            draft_result.submitted_at = timezone.now()
            draft_result.submitted_by = request.user
            draft_result.save()
            result = draft_result
        else:
            result = LabResult.objects.create(
                test_order=test_order,
                **result_data,
                status="submitted",
                entered_at=timezone.now(),
                entered_by=request.user,
                submitted_at=timezone.now(),
                submitted_by=request.user,
            )

        test_order.status = "completed"
        test_order.save(update_fields=["status"])

        return redirect("lab_result_detail", result_id=result.id)

    return render(
        request,
        "lab/result_form.html",
        {
            "test_order": test_order,
            "result": draft_result,
            "result_types": LabResult.RESULT_TYPES,
            "abnormal_flags": LabResult.ABNORMAL_FLAGS,
        },
    )


@login_required
def lab_result_detail(request, result_id):
    result = get_object_or_404(
        LabResult.objects.select_related(
            "test_order__encounter__patient",
            "entered_by",
            "submitted_by",
        ),
        id=result_id,
        status="submitted",
    )

    if not (
        user_has_permission(request.user, "can_view_lab_worklist")
        or user_has_permission(request.user, "can_view_encounters")
    ):
        return render(
            request,
            "permission_denied.html",
            {"message": "You do not have permission to view this lab result."},
            status=403,
        )

    return render(
        request,
        "lab/result_detail.html",
        {
            "test_order": result.test_order,
            "result": result,
            "already_submitted": True,
        },
    )


def get_vital_fields():
    return [
        {
            "name": "systolic_bp",
            "label": "Systolic BP (mmHg)",
            "step": "1",
            "max": "300",
        },
        {
            "name": "diastolic_bp",
            "label": "Diastolic BP (mmHg)",
            "step": "1",
            "max": "200",
        },
        {
            "name": "pulse",
            "label": "Pulse (beats/min)",
            "step": "1",
            "max": "300",
        },
        {
            "name": "respiratory_rate",
            "label": "Respiratory Rate (breaths/min)",
            "step": "1",
            "max": "100",
        },
        {
            "name": "temperature",
            "label": "Temperature (Ã‚Â°C)",
            "step": "0.1",
            "max": "50",
        },
        {
            "name": "spo2",
            "label": "Oxygen Saturation (%)",
            "step": "0.01",
            "max": "100",
        },
        {
            "name": "weight_kg",
            "label": "Weight (kg)",
            "step": "0.01",
            "max": "1000",
        },
        {
            "name": "height_cm",
            "label": "Height (cm)",
            "step": "0.01",
            "max": "300",
        },
    ]
