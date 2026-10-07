from django.contrib import admin
from django.urls import path, include

from accounts.views import dashboard, role_test
from patients.views import patient_list, patient_create, patient_detail
from encounters.views import encounter_create


urlpatterns = [
    path("admin/", admin.site.urls),

    path("accounts/", include("django.contrib.auth.urls")),

    path("dashboard/", dashboard, name="dashboard"),

    path("role-test/", role_test, name="role_test"),

    path("patients/", patient_list, name="patient_list"),
    path("patients/new/", patient_create, name="patient_create"),
    path(
        "patients/<int:patient_id>/",
        patient_detail,
        name="patient_detail",
    ),

    path(
        "patients/<int:patient_id>/encounters/new/",
        encounter_create,
        name="encounter_create",
    ),
]