from django.contrib import admin
from django.urls import path, include
from accounts.views import patient_password_reset
from accounts.views import (
    dashboard,
    role_test,
    patient_register,
    patient_registration_requests,
    patient_registration_review,
    patient_portal_login,
    patient_portal_dashboard,
    patient_portal_logout,
)

from patients.views import (
    patient_list,
    patient_create,
    patient_detail,
)

from encounters.views import (
    encounter_create,
    encounter_detail,
    medication_prescription_create,
    rxnorm_medication_search,
    vitals_create,
    test_order_create,
    lab_worklist,
    lab_result_create,
    lab_result_detail,
    procedure_create,
    procedure_catalog_search,
)


urlpatterns = [
    path(
    "patient-portal/password-reset/",
    patient_password_reset,
    name="patient_password_reset",),
    
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),

    # Hospital staff
    path("dashboard/", dashboard, name="dashboard"),
    path("role-test/", role_test, name="role_test"),

    # Patient portal
    path(
        "patient-portal/login/",
        patient_portal_login,
        name="patient_portal_login",
    ),
    path(
        "patient-portal/",
        patient_portal_dashboard,
        name="patient_portal_dashboard",
    ),
    path(
        "patient-portal/logout/",
        patient_portal_logout,
        name="patient_portal_logout",
    ),
    path(
        "patient-portal/register/",
        patient_register,
        name="patient_register",
    ),

    # Staff registration review
    path(
        "staff/patient-registration-requests/",
        patient_registration_requests,
        name="patient_registration_requests",
    ),
    path(
        "staff/patient-registration-requests/<int:request_id>/",
        patient_registration_review,
        name="patient_registration_review",
    ),

    # Patients
    path("patients/", patient_list, name="patient_list"),
    path("patients/new/", patient_create, name="patient_create"),
    path(
        "patients/<int:patient_id>/",
        patient_detail,
        name="patient_detail",
    ),

    # Encounters
    path(
        "patients/<int:patient_id>/encounters/new/",
        encounter_create,
        name="encounter_create",
    ),
    path(
        "encounters/<int:encounter_id>/",
        encounter_detail,
        name="encounter_detail",
    ),

    # Medications
    path(
        "medications/rxnorm-search/",
        rxnorm_medication_search,
        name="rxnorm_medication_search",
    ),
    path(
        "encounters/<int:encounter_id>/prescriptions/new/",
        medication_prescription_create,
        name="medication_prescription_create",
    ),

    # Procedures
    path(
        "procedures/catalog-search/",
        procedure_catalog_search,
        name="procedure_catalog_search",
    ),
    path(
        "encounters/<int:encounter_id>/procedures/new/",
        procedure_create,
        name="procedure_create",
    ),

    # Vitals
    path(
        "encounters/<int:encounter_id>/vitals/",
        vitals_create,
        name="vitals_create",
    ),

    # Test orders
    path(
        "encounters/<int:encounter_id>/orders/tests/new/",
        test_order_create,
        name="test_order_create",
    ),

    # Laboratory
    path("lab/worklist/", lab_worklist, name="lab_worklist"),
    path(
        "lab/results/<int:test_order_id>/",
        lab_result_create,
        name="lab_result_create",
    ),
    path(
        "lab/results/detail/<int:result_id>/",
        lab_result_detail,
        name="lab_result_detail",
    ),
]
