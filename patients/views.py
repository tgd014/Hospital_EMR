from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .models import Patient
from accounts.permissions import user_has_permission


@login_required
def patient_list(request):
    if not user_has_permission(request.user, "can_view_patients"):
        return render(
            request,
            "permission_denied.html",
            {"message": "You do not have permission to view patients."},
            status=403,
        )

    patients = Patient.objects.all().order_by("-created_at")

    can_create_patients = user_has_permission(
        request.user,
        "can_create_patients",
    )

    return render(
        request,
        "patients/patient_list.html",
        {
            "patients": patients,
            "can_create_patients": can_create_patients,
        },
    )


@login_required
def patient_create(request):
    if not user_has_permission(request.user, "can_create_patients"):
        return render(
            request,
            "permission_denied.html",
            {"message": "You do not have permission to create patients."},
            status=403,
        )

    if request.method == "POST":
        Patient.objects.create(
            medical_record_number=request.POST["medical_record_number"],
            first_name=request.POST["first_name"],
            middle_name=request.POST.get("middle_name", ""),
            last_name=request.POST["last_name"],
            date_of_birth=request.POST["date_of_birth"],
            phone=request.POST.get("phone", ""),
            email=request.POST.get("email", ""),
            address=request.POST.get("address", ""),
        )

        return redirect("patient_list")

    return render(
        request,
        "patients/patient_create.html",
    )

@login_required
def patient_detail(request, patient_id):
    if not user_has_permission(request.user, "can_view_patients"):
        return render(
            request,
            "permission_denied.html",
            {"message": "You do not have permission to view patients."},
            status=403,
        )

    patient = Patient.objects.get(id=patient_id)

    encounters = patient.encounters.all().order_by("-started_at")

    return render(
        request,
        "patients/patient_detail.html",
        {
            "patient": patient,
            "encounters": encounters,
        },
    )