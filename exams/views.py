from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.db import IntegrityError, transaction
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
import os
import traceback
from datetime import datetime
from django.middleware.csrf import get_token

from .forms import StudentForm, ResultForm
from .models import Student, Result, Semester, Course


def home(request):
    semesters = Semester.objects.all()
    return render(request, "exams/home.html", {"semesters": semesters})


def dashboard(request):
    students = Student.objects.all().order_by("registration_number")
    return render(request, "exams/dashboard.html", {"students": students})


@csrf_protect
@require_http_methods(["GET", "POST"])
def register_student(request):
    student = None
    if request.method == "POST":
        form = StudentForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    student = form.save(commit=True)
                messages.success(request, "Student registered successfully. They can now log in with their registration number and password.")
            except IntegrityError:
                traceback.print_exc()
                form.add_error(None, "Duplicate registration number or email.")
                messages.error(request, "Registration failed due to duplicate data.")
            except Exception as e:
                traceback.print_exc()
                form.add_error(None, f"Unexpected error: {e}")
                messages.error(request, f"Registration failed: {e}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = StudentForm()
    return render(request, "exams/register_student.html", {"form": form, "student": student})


@csrf_protect
@require_http_methods(["GET", "POST"])
def student_login(request):
    if request.method == "POST":
        reg_no = request.POST.get("registration_number", "").strip()
        password = request.POST.get("password", "").strip()
        if not reg_no or not password:
            messages.error(request, "Please enter both registration number and password.")
            return render(request, "exams/student_login.html")
        user = authenticate(request, username=reg_no, password=password)
        if user is not None:
            student = Student.objects.filter(registration_number=reg_no).first()
            if not student:
                messages.error(request, "No student profile found for this registration number.")
                return render(request, "exams/student_login.html")
            login(request, user)
            messages.success(request, f"Welcome, {student.name}.")
            return redirect("exams:dashboard")
        else:
            messages.error(request, "Invalid registration number or password.")
    return render(request, "exams/student_login.html")


@csrf_protect
@require_http_methods(["GET", "POST"])
def staff_login(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        if not username or not password:
            messages.error(request, "Please enter username and password.")
            return render(request, "exams/staff_login.html")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active and user.is_staff:
                login(request, user)
                messages.success(request, f"Welcome, {user.username}.")
                return redirect("exams:dashboard")
            else:
                messages.error(request, "You are not authorized as staff.")
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, "exams/staff_login.html")


def user_logout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("exams:home")


@staff_member_required
@csrf_protect
@require_http_methods(["GET", "POST"])
def add_result(request):
    if request.method == "POST":
        form = ResultForm(request.POST)
        if form.is_valid():
            try:
                result = form.save(commit=True)
                messages.success(request, "Result saved.")
                return redirect("exams:add_result")  # <-- FIXED
            except Exception as e:
                traceback.print_exc()
                messages.error(request, f"Failed to save result: {e}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ResultForm()
    return render(request, "exams/add_result.html", {"form": form})


def student_results(request):
    reg_no = request.GET.get("registration_number", "").strip()
    semester_id = request.GET.get("semester", "").strip()

    student = Student.objects.filter(registration_number=reg_no).first() if reg_no else None
    semester = Semester.objects.filter(id=semester_id).first() if semester_id else None

    results = Result.objects.filter(student=student, semester=semester).select_related("course") if student and semester else []
    gpa = student.calculate_gpa(semester) if student and semester else None
    classification = student.gpa_classification(gpa) if gpa is not None else None
    status = student.withdrawal_status(semester) if student and semester else None

    semesters = Semester.objects.all().order_by("-start_date")
    return render(request, "exams/student_results.html", {
        "student": student,
        "semester": semester,
        "results": results,
        "gpa": gpa,
        "classification": classification,
        "status": status,
        "semesters": semesters,
    })


@staff_member_required
@csrf_protect
@require_http_methods(["GET", "POST"])
def upload_file(request):
    uploaded_files = []
    staff_dir = os.path.join(settings.MEDIA_ROOT, "staff")
    os.makedirs(staff_dir, exist_ok=True)

    if request.method == "POST":
        file = request.FILES.get("file")
        if file:
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_name, ext = os.path.splitext(file.name)
                safe_name = f"{base_name}_{timestamp}{ext}"
                save_path = os.path.join(staff_dir, safe_name)

                with open(save_path, "wb+") as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)

                uploaded_files.append({
                    "filename": safe_name,
                    "url": os.path.join(settings.MEDIA_URL.lstrip("/"), "staff", safe_name),
                    "timestamp": timestamp,
                })

                messages.success(request, f"Uploaded: {safe_name}")
                return redirect("exams:upload")  # <-- FIXED
            except Exception as e:
                traceback.print_exc()
                messages.error(request, f"Upload failed: {e}")
        else:
            messages.error(request, "No file selected.")

    files = []
    if os.path.exists(staff_dir):
        for fname in sorted(os.listdir(staff_dir), reverse=True):
            name, ext = os.path.splitext(fname)
            files.append({
                "filename": fname,
                "url": os.path.join(settings.MEDIA_URL.lstrip("/"), "staff", fname),
                "timestamp": "",
            })

    return render(request, "exams/upload.html", {"files": files, "uploaded_files": uploaded_files})


@csrf_exempt
@require_http_methods(["GET", "POST"])
def csrf_debug(request):
    expected = get_token(request)
    submitted_form_token = request.POST.get("csrfmiddlewaretoken", "")
    submitted_header_token = request.META.get("HTTP_X_CSRFTOKEN", "")
    context = {
        "expected_token": expected,
        "submitted_form_token": submitted_form_token,
        "submitted_header_token": submitted_header_token,
        "method": request.method,
    }
    return render(request, "exams/csrf_debug.html", context)
