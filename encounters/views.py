from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from patients.models import Patient
from accounts.permissions import user_has_permission
from .models import Encounter


@login_required
def encounter_create(request, patient_id):

    if not user_has_permission(request.user, "can_create_encounters"):
        return render(
            request,
            "permission_denied.html",
            {
                "message": "You do not have permission to create encounters."
            },
            status=403,
        )

    patient = get_object_or_404(
        Patient,
        id=patient_id,
    )

    if request.method == "POST":

        encounter = Encounter.objects.create(
            patient=patient,
            encounter_type="outpatient",
            status="open",
            started_at=timezone.now(),
        )

        return redirect(
            "patient_detail",
            patient_id=patient.id,
        )

    return render(
        request,
        "encounters/encounter_create.html",
        {
            "patient": patient,
        },
    )