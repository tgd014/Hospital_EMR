from django.contrib import messages
from django.contrib.auth import (
    get_user_model,
    login,
    logout,
)
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction, IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from patients.models import Patient
from encounters.models import Encounter

from .forms import PatientRegistrationForm
from .models import (
    PatientAccount,
    PatientRegistrationRequest,
    UserRole,
)
from .permissions import user_has_permission


User = get_user_model()


# ---------------------------------------------------------
# HOSPITAL STAFF DASHBOARD
# ---------------------------------------------------------

@login_required
def dashboard(request):
    # Patient accounts must not enter the hospital staff dashboard.
    if PatientAccount.objects.filter(user=request.user).exists():
        return redirect("patient_portal_dashboard")

    patient_count = Patient.objects.count()
    encounter_count = Encounter.objects.count()

    context = {
        "patient_count": patient_count,
        "encounter_count": encounter_count,
        "can_view_patients": user_has_permission(
            request.user, "can_view_patients"
        ),
        "can_create_patients": user_has_permission(
            request.user, "can_create_patients"
        ),
        "can_view_encounters": user_has_permission(
            request.user, "can_view_encounters"
        ),
        "can_create_encounters": user_has_permission(
            request.user, "can_create_encounters"
        ),
        "can_order_tests": user_has_permission(
            request.user, "can_order_tests"
        ),
        "can_view_lab_worklist": user_has_permission(
            request.user, "can_view_lab_worklist"
        ),
        "can_enter_lab_results": user_has_permission(
            request.user, "can_enter_lab_results"
        ),
    }

    return render(request, "dashboard.html", context)


@login_required
def role_test(request):
    if PatientAccount.objects.filter(user=request.user).exists():
        return render(
            request,
            "permission_denied.html",
            {"message": "Patient accounts cannot access staff permissions."},
            status=403,
        )

    permission_definitions = [
        ("can_view_patients", "View Patients"),
        ("can_create_patients", "Register Patients"),
        ("can_view_encounters", "View Clinical Encounters"),
        ("can_create_encounters", "Create Clinical Encounters"),
        ("can_order_tests", "Order Diagnostic Tests"),
        ("can_view_lab_worklist", "View Laboratory Worklist"),
        ("can_enter_lab_results", "Enter Laboratory Results"),
    ]

    permissions = []

    for permission_name, label in permission_definitions:
        permissions.append({
            "name": permission_name,
            "label": label,
            "allowed": user_has_permission(
                request.user, permission_name
            ),
        })

    try:
        hospital_role = request.user.hospital_role.role.name
    except Exception:
        hospital_role = None

    return render(
        request,
        "role_test.html",
        {
            "permissions": permissions,
            "hospital_role": hospital_role,
        },
    )


# ---------------------------------------------------------
# PATIENT PORTAL LOGIN
# ---------------------------------------------------------

def patient_portal_login(request):
    if request.user.is_authenticated:
        if PatientAccount.objects.filter(user=request.user).exists():
            return redirect("patient_portal_dashboard")
        return redirect("dashboard")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()

            # Only approved users linked to a Patient record
            # may use the patient portal.
            patient_account = (
                PatientAccount.objects
                .filter(user=user)
                .select_related("patient")
                .first()
            )

            if patient_account is None:
                form.add_error(
                    None,
                    "This account is not approved for the patient portal. "
                    "Please contact the hospital if you need assistance.",
                )
            else:
                login(request, user)
                return redirect("patient_portal_dashboard")

    else:
        form = AuthenticationForm(request)

    return render(
        request,
        "patient_portal/login.html",
        {"form": form},
    )

def patient_password_reset(request):
    User = get_user_model()

    form = None
    error = None
    success = False

    if request.method == "POST":
        username = request.POST.get("username", "").strip()

        user = User.objects.filter(
            username=username,
            patient_account__isnull=False,
            is_active=True,
        ).first()

        if user is None:
            error = "No approved patient account was found with that username."
        else:
            form = SetPasswordForm(user, request.POST)

            if form.is_valid():
                form.save()
                success = True

    return render(
        request,
        "patient_portal/password_reset.html",
        {
            "form": form,
            "error": error,
            "success": success,
        },
    )

# ---------------------------------------------------------
# PATIENT PORTAL DASHBOARD
# ---------------------------------------------------------

@login_required
def patient_portal_dashboard(request):
    patient_account = (
        PatientAccount.objects
        .filter(user=request.user)
        .select_related("patient")
        .first()
    )

    # Never allow a staff account or an unlinked account
    # to access patient information through this page.
    if patient_account is None:
        return render(
            request,
            "permission_denied.html",
            {
                "message": (
                    "This account is not linked to a patient record "
                    "and cannot access the patient portal."
                )
            },
            status=403,
        )

    patient = patient_account.patient

    context = {
        "patient": patient,
    }

    return render(
        request,
        "patient_portal/dashboard.html",
        context,
    )


# ---------------------------------------------------------
# PATIENT PORTAL LOGOUT
# ---------------------------------------------------------

@login_required
@require_POST
def patient_portal_logout(request):
    is_patient_account = PatientAccount.objects.filter(
        user=request.user
    ).exists()

    if not is_patient_account:
        return redirect("dashboard")

    logout(request)
    return redirect("patient_portal_login")


# ---------------------------------------------------------
# PATIENT SELF-REGISTRATION
# ---------------------------------------------------------

def patient_register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = PatientRegistrationForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data

            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=data["username"],
                        email=data["email"],
                        password=data["password"],
                        first_name=data["first_name"],
                        last_name=data["last_name"],
                        is_active=False,
                        is_staff=False,
                        is_superuser=False,
                    )

                    PatientRegistrationRequest.objects.create(
                        user=user,
                        first_name=data["first_name"],
                        middle_name=data["middle_name"],
                        last_name=data["last_name"],
                        date_of_birth=data["date_of_birth"],
                        phone=data["phone"],
                        email=data["email"],
                        medical_record_number=data[
                            "medical_record_number"
                        ],
                    )

                return render(
                    request,
                    "patient_portal/registration_submitted.html",
                )

            except IntegrityError:
                form.add_error(
                    None,
                    "We could not create your request. "
                    "Please try again or contact the hospital.",
                )

    else:
        form = PatientRegistrationForm()

    return render(
        request,
        "patient_portal/register.html",
        {"form": form},
    )


# ---------------------------------------------------------
# STAFF: PATIENT REGISTRATION REQUEST LIST
# ---------------------------------------------------------

@login_required
def patient_registration_requests(request):
    if not (
        user_has_permission(request.user, "can_view_patients")
        and user_has_permission(request.user, "can_create_patients")
    ):
        return render(
            request,
            "permission_denied.html",
            {
                "message": (
                    "You do not have permission to review "
                    "patient registrations."
                )
            },
            status=403,
        )

    registration_requests = (
        PatientRegistrationRequest.objects
        .select_related("user", "reviewed_by")
        .order_by("status", "-submitted_at")
    )

    return render(
        request,
        "accounts/patient_registration_requests.html",
        {"registration_requests": registration_requests},
    )


# ---------------------------------------------------------
# STAFF: REVIEW AND APPROVE/REJECT PATIENT REGISTRATION
# ---------------------------------------------------------

@login_required
@require_http_methods(["GET", "POST"])
def patient_registration_review(request, request_id):
    if not (
        user_has_permission(request.user, "can_view_patients")
        and user_has_permission(request.user, "can_create_patients")
    ):
        return render(
            request,
            "permission_denied.html",
            {
                "message": (
                    "You do not have permission to review "
                    "patient registrations."
                )
            },
            status=403,
        )

    registration = get_object_or_404(
        PatientRegistrationRequest.objects.select_related("user"),
        pk=request_id,
    )

    if registration.status != "pending":
        messages.info(
            request,
            "This registration request has already been reviewed.",
        )
        return redirect("patient_registration_requests")

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "reject":
            with transaction.atomic():
                registration = (
                    PatientRegistrationRequest.objects
                    .select_for_update()
                    .get(pk=request_id)
                )

                if registration.status != "pending":
                    messages.error(
                        request,
                        "This request has already been reviewed.",
                    )
                    return redirect("patient_registration_requests")

                registration.status = "rejected"
                registration.reviewed_by = request.user
                registration.reviewed_at = timezone.now()
                registration.save(
                    update_fields=[
                        "status",
                        "reviewed_by",
                        "reviewed_at",
                    ]
                )

            messages.success(request, "Registration request rejected.")
            return redirect("patient_registration_requests")

        elif action == "approve":
            patient_id = request.POST.get("patient_id")

            if not patient_id:
                messages.error(
                    request,
                    "Please select the matching patient record.",
                )
                return redirect(
                    "patient_registration_review",
                    request_id=request_id,
                )

            patient = get_object_or_404(Patient, pk=patient_id)

            try:
                with transaction.atomic():
                    registration = (
                        PatientRegistrationRequest.objects
                        .select_for_update()
                        .select_related("user")
                        .get(pk=request_id)
                    )

                    if registration.status != "pending":
                        raise ValidationError(
                            "This request has already been reviewed."
                        )

                    if (
                        registration.user.is_staff
                        or registration.user.is_superuser
                    ):
                        raise ValidationError(
                            "Hospital staff accounts cannot be patient accounts."
                        )

                    if UserRole.objects.filter(
                        user=registration.user
                    ).exists():
                        raise ValidationError(
                            "This user already has a hospital staff role."
                        )

                    if PatientAccount.objects.filter(
                        patient=patient
                    ).exists():
                        raise ValidationError(
                            "This patient record is already linked to an account."
                        )

                    if PatientAccount.objects.filter(
                        user=registration.user
                    ).exists():
                        raise ValidationError(
                            "This user already has a patient account."
                        )

                    account = PatientAccount(
                        user=registration.user,
                        patient=patient,
                    )
                    account.full_clean()
                    account.save()

                    registration.status = "approved"
                    registration.reviewed_by = request.user
                    registration.reviewed_at = timezone.now()
                    registration.save(
                        update_fields=[
                            "status",
                            "reviewed_by",
                            "reviewed_at",
                        ]
                    )

                    registration.user.is_active = True
                    registration.user.save(
                        update_fields=["is_active"]
                    )

                messages.success(
                    request,
                    "Patient account approved and linked successfully.",
                )
                return redirect("patient_registration_requests")

            except ValidationError as error:
                messages.error(request, " ".join(error.messages))

            except IntegrityError:
                messages.error(
                    request,
                    "This patient or user has already been linked to another account.",
                )

        else:
            messages.error(request, "Invalid review action.")

    patients = Patient.objects.order_by("medical_record_number")

    return render(
        request,
        "accounts/patient_registration_review.html",
        {
            "registration": registration,
            "patients": patients,
        },
    )