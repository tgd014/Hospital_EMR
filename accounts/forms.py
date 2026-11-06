
from django import forms
from django.contrib.auth.models import User

from .models import PatientRegistrationRequest


class PatientRegistrationForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        label="Create a username",
    )

    first_name = forms.CharField(max_length=100)
    middle_name = forms.CharField(max_length=100, required=False)
    last_name = forms.CharField(max_length=100)

    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    phone = forms.CharField(max_length=30)
    email = forms.EmailField()

    medical_record_number = forms.CharField(
        max_length=50,
        required=False,
        label="Medical record number (optional)",
        help_text="If known, this may help hospital staff locate your record.",
    )

    password = forms.CharField(
        widget=forms.PasswordInput,
        min_length=8,
        label="Create a password",
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput,
        label="Confirm password",
    )

    def clean_username(self):
        username = self.cleaned_data["username"].strip()

        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError(
                "This username is already taken."
            )

        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account using this email already exists. "
                "Please contact the hospital."
            )

        return email

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error(
                "confirm_password",
                "The passwords do not match.",
            )

        return cleaned_data
