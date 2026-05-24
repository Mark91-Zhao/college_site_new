"""
portal/forms.py
Clean and fully compatible with Django built-in authentication.
"""

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Student, Staff, Course, Semester, Result, SemesterPerformance


# =====================================================
# STUDENT REGISTRATION (CREATES DJANGO USER)
# =====================================================
class StudentRegistrationForm(forms.ModelForm):

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]

        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords do not match.")

        validate_password(password1)
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


# =====================================================
# STUDENT FORM (ADMIN USE)
# =====================================================
class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["reg_number", "program", "year", "phone_number"]

        widgets = {
            "reg_number": forms.TextInput(attrs={"class": "form-control"}),
            "program": forms.TextInput(attrs={"class": "form-control"}),
            "year": forms.NumberInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
        }


# =====================================================
# STUDENT PROFILE UPDATE FORM (SELF-SERVICE)
# =====================================================
class StudentUpdateForm(forms.ModelForm):
    """
    Form for students to update their own profile, including User fields.
    """
    first_name = forms.CharField(
        label="First Name",
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    last_name = forms.CharField(
        label="Last Name",
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": "form-control"})
    )

    class Meta:
        model = Student
        fields = ["reg_number", "program", "year", "phone_number"]

        widgets = {
            "reg_number": forms.TextInput(attrs={"class": "form-control"}),
            "program": forms.TextInput(attrs={"class": "form-control"}),
            "year": forms.NumberInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        student = kwargs.get("instance")
        super().__init__(*args, **kwargs)

        if student and student.user:
            self.fields["first_name"].initial = student.user.first_name
            self.fields["last_name"].initial = student.user.last_name
            self.fields["email"].initial = student.user.email

    def save(self, commit=True):
        student = super().save(commit=False)
        user = student.user

        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]

        if commit:
            user.save()
            student.save()
        return student


# =====================================================
# STAFF FORM (ADMIN USE)
# =====================================================
class StaffForm(forms.ModelForm):
    class Meta:
        model = Staff
        fields = ["staff_id", "department", "role", "phone_number"]

        widgets = {
            "staff_id": forms.TextInput(attrs={"class": "form-control"}),
            "department": forms.TextInput(attrs={"class": "form-control"}),
            "role": forms.TextInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
        }


# =====================================================
# COURSE FORM
# =====================================================
class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["name", "code", "credit_hours"]

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "credit_hours": forms.NumberInput(attrs={"class": "form-control"}),
        }


# =====================================================
# SEMESTER FORM
# =====================================================
class SemesterForm(forms.ModelForm):
    class Meta:
        model = Semester
        fields = ["name", "year"]

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "year": forms.NumberInput(attrs={"class": "form-control"}),
        }


# =====================================================
# RESULT FORM (ADMIN USE) - Marks Only
# =====================================================
class ResultForm(forms.ModelForm):
    class Meta:
        model = Result
        fields = ["student", "course", "semester", "marks"]

        widgets = {
            "student": forms.Select(attrs={"class": "form-control"}),
            "course": forms.Select(attrs={"class": "form-control"}),
            "semester": forms.Select(attrs={"class": "form-control"}),
            "marks": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }

# =====================================================
# SEMESTER PERFORMANCE FORM (STAFF USE) - GPA Entry
# =====================================================
class SemesterPerformanceForm(forms.ModelForm):
    class Meta:
        model = SemesterPerformance
        fields = ["gpa"]  # ✅ Only GPA is editable

        widgets = {
            "gpa": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0.00",
                "max": "4.00",
                "placeholder": "Enter GPA between 0.00 and 4.00"
            }),
        }
