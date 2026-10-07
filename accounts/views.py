from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from patients.models import Patient
from encounters.models import Encounter


@login_required
def dashboard(request):
    patient_count = Patient.objects.count()
    encounter_count = Encounter.objects.count()

    return render(
        request,
        "dashboard.html",
        {
            "patient_count": patient_count,
            "encounter_count": encounter_count,
        },
    )


@login_required
def role_test(request):
    from .permissions import user_has_permission

    can_view_patients = user_has_permission(
        request.user,
        "can_view_patients",
    )

    can_create_encounters = user_has_permission(
        request.user,
        "can_create_encounters",
    )

    return render(
        request,
        "role_test.html",
        {
            "can_view_patients": can_view_patients,
            "can_create_encounters": can_create_encounters,
        },
    )