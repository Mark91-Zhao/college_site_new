"""
portal/views.py
Complete Consolidated Enterprise Academic System
Enhanced • Secure • Role-Based • Production Ready
"""

from io import BytesIO
import csv

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from .forms import StudentUpdateForm
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from django.http import HttpResponse

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet

from .models import Student, Staff, Course, Semester, Result
from .utils import get_or_create_student

# =====================================================
# ROLE HELPERS
# =====================================================
def is_student(user):
    return user.is_authenticated and hasattr(user, "student")

def is_staff_member(user):
    return user.is_authenticated and hasattr(user, "staff")

# =====================================================
# GPA CALCULATION
# =====================================================
def calculate_gpa(results):
    total_points = 0
    total_credits = 0
    for result in results:
        if result.grade_point is not None:
            total_points += result.grade_point * result.course.credit_hours
            total_credits += result.course.credit_hours
    if total_credits == 0:
        return 0.0
    return round(total_points / total_credits, 2)

def classify_gpa(gpa):
    if gpa < 1.0:
        return "Withdraw"
    elif gpa >= 3.5:
        return "Distinction"
    elif gpa >= 3.0:
        return "Upper Credit"
    elif gpa >= 2.5:
        return "Lower Credit"
    elif gpa >= 1.5:
        return "Average"
    return "Pass"

# =====================================================
# HOME
# =====================================================
def home(request):
    if not request.user.is_authenticated:
        return render(request, "portal/home.html", {"role": "guest"})

    if is_staff_member(request.user):
        return render(request, "portal/home.html", {
            "role": "staff",
            "total_students": Student.objects.count(),
            "total_courses": Course.objects.count(),
            "total_semesters": Semester.objects.count(),
            "total_results": Result.objects.count(),
        })

    if is_student(request.user):
        student = get_or_create_student(request.user)
        results = student.results.select_related("semester", "course").all()
        gpa = calculate_gpa(results)
        return render(request, "portal/home.html", {
            "role": "student",
            "student": student,
            "gpa": gpa,
            "classification": classify_gpa(gpa),
        })

    return render(request, "portal/home.html", {"role": "guest"})
# =====================================================
# LOGIN VIEWS (Student & Staff)
# =====================================================
def student_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            if is_student(user):   # ✅ enforce role
                login(request, user)
                return redirect("portal:student_dashboard")
            else:
                messages.error(request, "This account is not a student account.")
                return redirect("student_login")
    return render(request, "registration/student_login.html")


def staff_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            if is_staff_member(user):   # ✅ enforce role
                login(request, user)
                return redirect("portal:staff_dashboard")
            else:
                messages.error(request, "This account is not a staff account.")
                return redirect("staff_login")
    return render(request, "registration/staff_login.html")

# =====================================================
# STUDENT REGISTRATION
# =====================================================
def student_register(request):
    if request.method == "POST":
        reg_number = request.POST.get("reg_number", "").strip().upper()
        full_name = request.POST.get("full_name", "").strip()
        program = request.POST.get("program", "").strip()
        year = request.POST.get("year", "").strip()
        email = request.POST.get("email", "").strip()
        phone_number = request.POST.get("phone_number", "").strip()
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if not all([reg_number, full_name, program, year, email, password]):
            messages.error(request, "All fields are required.")
            return redirect("portal:register")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("portal:register")

        if User.objects.filter(username=reg_number).exists():
            messages.error(request, "Registration number already exists.")
            return redirect("portal:register")

        try:
            year = int(year)
        except ValueError:
            messages.error(request, "Year must be a valid number.")
            return redirect("portal:register")

        names = full_name.split()
        first_name = names[0]
        last_name = " ".join(names[1:]) if len(names) > 1 else ""

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=reg_number,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                student = get_or_create_student(user)
                student.reg_number = reg_number
                student.program = program
                student.year = year
                student.phone_number = phone_number
                student.save()

            messages.success(request, "Registration successful. Please login.")
            return redirect("login")

        except Exception as e:
            print("Registration error:", e)
            messages.error(request, "Error creating account. Please contact admin.")
            return redirect("portal:register")

    return render(request, "registration/register.html")

# =====================================================
# STUDENT PROFILE (Legacy → Redirect to Dashboard)
# =====================================================
@login_required
def student_profile(request):
    """
    Legacy profile view.
    Redirects to the unified student dashboard.
    """
    return redirect("portal:student_dashboard")


# =====================================================
# STUDENT PROFILE UPDATE (Legacy → Redirect to Dashboard)
# =====================================================
@login_required
def student_update_profile(request):
    """
    Legacy update view.
    Redirects to the unified student dashboard where editing happens inline.
    """
    return redirect("portal:student_dashboard")

# ==================== STUDENT DASHBOARD ====================
@login_required
def student_dashboard(request):
    # Block non-students
    if not hasattr(request.user, "student"):
        messages.error(request, "Access denied. Students only.")
        return redirect("portal:home")

    student = get_or_create_student(request.user)
    results = student.results.select_related("semester", "course").all()

    cumulative_gpa = calculate_gpa(results)
    academic_status = classify_gpa(cumulative_gpa)
    all_passed = all(result.status == "PASS" for result in results)

    # Semester-wise data
    semesters = Semester.objects.order_by("year", "name")
    semester_data = []
    for semester in semesters:
        semester_results = results.filter(semester=semester)
        if not semester_results.exists():
            continue
        total_points = sum((res.grade_point or 0) * res.course.credit_hours for res in semester_results)
        total_credits = sum(res.course.credit_hours for res in semester_results if res.grade_point is not None)
        semester_gpa = round(total_points / total_credits, 2) if total_credits else 0.0
        semester_data.append({"semester": semester, "gpa": semester_gpa, "results": semester_results})

    # ✅ Add the update form here
    form = StudentUpdateForm(instance=student)

    context = {
        "student": student,
        "form": form,
        "gpa": cumulative_gpa,
        "academic_status": academic_status,
        "congratulations": all_passed,
        "semester_data": semester_data,
    }
    return render(request, "portal/student_dashboard.html", context)

# ==================== STUDENT RESULTS ====================
@login_required
def student_results(request):
    """
    Display all results for the logged-in student.
    """
    student = get_or_create_student(request.user)
    results = student.results.select_related("course", "semester").all()

    return render(request, "portal/student_results.html", {
        "student": student,
        "results": results,
    })


# ==================== TRANSCRIPT HTML ====================
@login_required
def transcript(request):
    """
    Display a detailed transcript in HTML format.
    """
    student = get_or_create_student(request.user)
    results = student.results.select_related("semester", "course").all()

    cumulative_gpa = calculate_gpa(results)
    classification = classify_gpa(cumulative_gpa)
    all_passed = all(result.status == "PASS" for result in results)

    semesters = Semester.objects.order_by("year", "name")
    semester_data = []
    for semester in semesters:
        semester_results = results.filter(semester=semester)
        if not semester_results.exists():
            continue

        total_points = sum(
            (res.grade_point or 0) * res.course.credit_hours for res in semester_results
        )
        total_credits = sum(
            res.course.credit_hours for res in semester_results if res.grade_point is not None
        )
        semester_gpa = round(total_points / total_credits, 2) if total_credits else 0.0

        semester_data.append({
            "semester": semester,
            "gpa": semester_gpa,
            "results": semester_results
        })

    context = {
        "student": student,
        "gpa": cumulative_gpa,
        "classification": classification,
        "congratulations": all_passed,
        "semester_data": semester_data,
    }
    return render(request, "portal/transcript.html", context)


# ==================== EXPORT TRANSCRIPT PDF ====================
@login_required
def export_transcript_pdf(request):
    """
    Generate a PDF transcript for the logged-in student.
    """
    student = get_or_create_student(request.user)
    results = student.results.select_related("semester", "course").all()

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=30,
        leftMargin=30,
        topMargin=60,
        bottomMargin=50
    )
    elements = []
    styles = getSampleStyleSheet()

    # Header
    elements.append(Paragraph("<b>MAWLLOW COLLEGE OF FORESTRY & WILDLIFE</b>", styles["Title"]))
    elements.append(Paragraph("Academic Records Office", styles["Normal"]))
    elements.append(Paragraph("Official Transcript Document", styles["Normal"]))
    elements.append(Spacer(1, 20))

    # Student info
    student_info = f"""
    <b>Name:</b> {student.user.get_full_name()}<br/>
    <b>Registration Number:</b> {student.reg_number}<br/>
    <b>Program:</b> {student.program}<br/>
    <b>Year:</b> {student.year}
    """
    elements.append(Paragraph(student_info, styles["Normal"]))
    elements.append(Spacer(1, 20))

    semesters = Semester.objects.order_by("year", "name")
    all_passed = True

    for semester in semesters:
        semester_results = results.filter(semester=semester)
        if not semester_results.exists():
            continue

        total_points = sum((res.grade_point or 0) * res.course.credit_hours for res in semester_results)
        total_credits = sum(res.course.credit_hours for res in semester_results if res.grade_point is not None)
        semester_gpa = round(total_points / total_credits, 2) if total_credits else 0.0

        elements.append(Paragraph(f"<b>{semester.name} — GPA: {semester_gpa}</b>", styles["Heading3"]))
        elements.append(Spacer(1, 10))

        data = [["Course", "Marks", "Grade", "Credits", "Remark"]]
        for res in semester_results:
            remark = res.status
            if remark != "PASS":
                all_passed = False
            data.append([
                res.course.name,
                res.marks if res.marks is not None else "-",
                res.grade_letter or "-",
                res.course.credit_hours,
                remark
            ])

        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.darkgreen),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 20))

    cumulative_gpa = calculate_gpa(results)
    classification = classify_gpa(cumulative_gpa)
    elements.append(Paragraph(f"<b>Cumulative GPA:</b> {cumulative_gpa}", styles["Heading2"]))
    elements.append(Paragraph(f"<b>Academic Classification:</b> {classification}", styles["Heading3"]))
    elements.append(Spacer(1, 20))

    if all_passed and results.exists():
        elements.append(Paragraph("🎉 Well done! You passed all courses.", styles["Heading2"]))
        elements.append(Spacer(1, 20))

    signature_block = """
    <b>______________________________</b><br/>
    Registrar / Academic Officer<br/>
    Official Digital Signature<br/>
    """
    elements.append(Paragraph(signature_block, styles["Normal"]))

    document.build(elements)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="Transcript_{student.reg_number}.pdf"'
    return response
# =====================================================
# STAFF DASHBOARD
# =====================================================
@login_required
def staff_dashboard(request):
    if not (hasattr(request.user, "staff") or request.user.is_superuser):
        messages.error(request, "Access denied.")
        return redirect("portal:home")

    total_students = Student.objects.count()
    total_courses = Course.objects.count()
    total_semesters = Semester.objects.count()
    total_results = Result.objects.count()

    students_queryset = Student.objects.order_by("-id")
    students_paginator = Paginator(students_queryset, 10)
    student_page_number = request.GET.get("student_page")
    latest_students = students_paginator.get_page(student_page_number)

    results_queryset = Result.objects.select_related("student", "course", "semester").order_by("-id")
    results_paginator = Paginator(results_queryset, 10)
    results_page_number = request.GET.get("results_page")
    recent_results = results_paginator.get_page(results_page_number)

    student_gpa_data = []
    students = Student.objects.prefetch_related("results__course")
    for student in students:
        results = student.results.all()
        total_points = sum(res.grade_point * res.course.credit_hours for res in results if res.grade_point is not None)
        total_credits = sum(res.course.credit_hours for res in results if res.grade_point is not None)
        gpa = round(total_points / total_credits, 2) if total_credits > 0 else 0.0
        student_gpa_data.append({"student": student, "gpa": gpa})

    top_students = sorted(student_gpa_data, key=lambda x: x["gpa"], reverse=True)[:5]
    at_risk_students = [s for s in student_gpa_data if s["gpa"] < 1.5]

    distinction_count = len([s for s in student_gpa_data if s["gpa"] >= 3.5])
    upper_count = len([s for s in student_gpa_data if 3.0 <= s["gpa"] < 3.5])
    lower_count = len([s for s in student_gpa_data if 2.5 <= s["gpa"] < 3.0])
    average_count = len([s for s in student_gpa_data if 1.5 <= s["gpa"] < 2.5])
    pass_count = len([s for s in student_gpa_data if 1.0 <= s["gpa"] < 1.5])
    fail_count = len([s for s in student_gpa_data if s["gpa"] < 1.0])

    course_stats = []
    for course in Course.objects.all():
        results = Result.objects.filter(course=course)
        count = results.count()
        avg_mark = round(sum(r.marks for r in results) / count, 2) if count else 0
        course_stats.append({"course": course, "average_mark": avg_mark, "total_students": count})

    return render(request, "portal/staff_dashboard.html", {
        "total_students": total_students,
        "total_courses": total_courses,
        "total_semesters": total_semesters,
        "total_results": total_results,
        "students": latest_students,
        "recent_results": recent_results,
        "top_students": top_students,
        "at_risk_students": at_risk_students,
        "course_stats": course_stats,
        "distinction_count": distinction_count,
        "upper_count": upper_count,
        "lower_count": lower_count,
        "average_count": average_count,
        "pass_count": pass_count,
        "fail_count": fail_count,
    })

# =====================================================
# STAFF PROFILE
# =====================================================
@login_required
def staff_profile(request):
    if not hasattr(request.user, "staff"):
        messages.error(request, "Staff profile not found.")
        return redirect("portal:home")
    staff = request.user.staff
    return render(request, "portal/staff_profile.html", {"staff": staff})

# =====================================================
# STAFF UPDATE
# =====================================================
@login_required
def staff_update(request, pk):
    """
    Allow a staff member to update their own profile.
    """
    staff = get_object_or_404(Staff, pk=pk)
    if request.user != staff.user:
        messages.error(request, "Access denied.")
        return redirect("portal:home")

    if request.method == "POST":
        staff.user.first_name = request.POST.get("first_name")
        staff.user.last_name = request.POST.get("last_name")
        staff.user.email = request.POST.get("email")
        staff.user.save()

        staff.department = request.POST.get("department")
        staff.role = request.POST.get("role")
        staff.phone_number = request.POST.get("phone_number")
        staff.save()

        messages.success(request, "Profile updated successfully.")
        return redirect("portal:staff_profile")

    return render(request, "portal/staff_update.html", {"staff": staff})

# =====================================================
# STUDENT CREATE (STAFF ONLY)
# =====================================================
@login_required
def student_create(request):
    if not (hasattr(request.user, "staff") or request.user.is_superuser):
        messages.error(request, "Access denied.")
        return redirect("portal:home")

    if request.method == "POST":
        reg_number = request.POST.get("reg_number", "").strip()
        full_name = request.POST.get("full_name", "").strip()
        program = request.POST.get("program", "").strip()
        year = request.POST.get("year", "").strip()
        email = request.POST.get("email", "").strip()
        phone_number = request.POST.get("phone_number", "").strip()

        if not all([reg_number, full_name, program, year]):
            messages.error(request, "All required fields must be filled.")
            return redirect("portal:student_create")

        try:
            year = int(year)
        except ValueError:
            messages.error(request, "Year must be a valid number.")
            return redirect("portal:student_create")

        first_name, *last = full_name.split(" ")
        last_name = " ".join(last)

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=reg_number,
                    password="default123",
                    first_name=first_name,
                    last_name=last_name,
                    email=email
                )
                student = get_or_create_student(user)
                student.reg_number = reg_number
                student.program = program
                student.year = year
                student.phone_number = phone_number
                student.save()

            messages.success(request, "Student created successfully.")
            return redirect("portal:student_list")

        except Exception as e:
            print("Error creating student:", e)
            messages.error(request, "Error occurred while creating student.")
            return redirect("portal:student_create")

    return render(request, "portal/student_create.html")


# =====================================================
# STUDENT DETAIL (STAFF ONLY)
# =====================================================
@login_required
def student_detail(request, pk):
    if not (hasattr(request.user, "staff") or request.user.is_superuser):
        messages.error(request, "Access denied.")
        return redirect("portal:home")

    student = get_object_or_404(Student.objects.select_related("user"), pk=pk)
    results = student.results.select_related("course", "semester")
    gpa = calculate_gpa(results)
    classification = classify_gpa(gpa)

    return render(request, "portal/student_detail.html", {
        "student": student,
        "results": results,
        "gpa": gpa,
        "classification": classification,
    })


# =====================================================
# STUDENT UPDATE (STAFF ONLY)
# =====================================================
@login_required
def student_update_staff(request, pk):
    """
    Allow staff or superusers to update a student's record.
    """
    if not (hasattr(request.user, "staff") or request.user.is_superuser):
        messages.error(request, "Access denied.")
        return redirect("portal:home")

    student = get_object_or_404(Student.objects.select_related("user"), pk=pk)
    student = get_or_create_student(student.user)

    if request.method == "POST":
        program = request.POST.get("program", "").strip()
        year = request.POST.get("year", "").strip()
        phone_number = request.POST.get("phone_number", "").strip()

        if not program:
            messages.error(request, "Program is required.")
            return redirect("portal:student_update_staff", pk=pk)

        try:
            year = int(year)
        except ValueError:
            messages.error(request, "Year must be a valid number.")
            return redirect("portal:student_update_staff", pk=pk)

        student.program = program
        student.year = year
        student.phone_number = phone_number
        student.save()

        messages.success(request, "Student updated successfully.")
        return redirect("portal:student_list")

    return render(request, "portal/student_update.html", {"student": student})

# =====================================================
# STUDENT DELETE (STAFF ONLY)
# =====================================================
@login_required
def student_delete(request, pk):
    if not (hasattr(request.user, "staff") or request.user.is_superuser):
        messages.error(request, "Access denied.")
        return redirect("portal:home")

    student = get_object_or_404(Student.objects.select_related("user"), pk=pk)
    student = get_or_create_student(student.user)

    if request.method == "POST":
        student.user.delete()
        messages.success(request, "Student deleted successfully.")
        return redirect("portal:student_list")

    return render(request, "portal/student_delete.html", {"student": student})


# =====================================================
# ADD RESULT (STAFF ONLY)
# =====================================================
@staff_member_required
def add_result(request):
    if request.method == "POST":
        reg_number = request.POST.get("reg_number")
        course_id = request.POST.get("course")
        semester_id = request.POST.get("semester")
        marks = request.POST.get("marks")

        student = get_object_or_404(Student, reg_number=reg_number)
        course = get_object_or_404(Course, id=course_id)
        semester = get_object_or_404(Semester, id=semester_id)

        Result.objects.update_or_create(
            student=student,
            course=course,
            semester=semester,
            defaults={"marks": float(marks)}
        )

        messages.success(request, "Result saved successfully.")
        return redirect("portal:staff_dashboard")

    return render(request, "portal/add_result.html", {
        "courses": Course.objects.all(),
        "semesters": Semester.objects.all(),
    })


# =====================================================
# COURSE LIST
# =====================================================
@login_required
def course_list(request):
    if not (hasattr(request.user, "staff") or request.user.is_superuser):
        messages.error(request, "Access denied.")
        return redirect("portal:home")

    courses = Course.objects.all()
    return render(request, "portal/course_list.html", {"courses": courses})


# =====================================================
# COURSE CREATE
# =====================================================
@login_required
def course_create(request):
    if not (hasattr(request.user, "staff") or request.user.is_superuser):
        messages.error(request, "Access denied.")
        return redirect("portal:home")

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        code = request.POST.get("code", "").strip()
        credit_hours = request.POST.get("credit_hours", "").strip()

        if not all([name, code, credit_hours]):
            messages.error(request, "All fields are required.")
            return redirect("portal:course_create")

        if Course.objects.filter(code__iexact=code).exists():
            messages.error(request, "Course code already exists.")
            return redirect("portal:course_create")

        try:
            credit_hours = int(credit_hours)
            if credit_hours <= 0:
                messages.error(request, "Credit hours must be > 0.")
                return redirect("portal:course_create")
        except ValueError:
            messages.error(request, "Credit hours must be a number.")
            return redirect("portal:course_create")

        try:
            with transaction.atomic():
                Course.objects.create(name=name, code=code, credit_hours=credit_hours)
            messages.success(request, "Course created successfully.")
            return redirect("portal:course_list")
        except Exception:
            messages.error(request, "Error occurred while saving course.")
            return redirect("portal:course_create")

    return render(request, "portal/course_form.html")


# =====================================================
# COURSE UPDATE
# =====================================================
@login_required
def course_update(request, pk):
    if not (hasattr(request.user, "staff") or request.user.is_superuser):
        messages.error(request, "Access denied.")
        return redirect("portal:home")

    course = get_object_or_404(Course, pk=pk)

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        code = request.POST.get("code", "").strip()
        credit_hours = request.POST.get("credit_hours", "").strip()

        if not all([name, code, credit_hours]):
            messages.error(request, "All fields are required.")
            return redirect("portal:course_update", pk=pk)

        if Course.objects.filter(code__iexact=code).exclude(pk=pk).exists():
            messages.error(request, "Course code already exists.")
            return redirect("portal:course_update", pk=pk)

        try:
            credit_hours = int(credit_hours)
            if credit_hours <= 0:
                messages.error(request, "Credit hours must be > 0.")
                return redirect("portal:course_update", pk=pk)
        except ValueError:
            messages.error(request, "Credit hours must be a number.")
            return redirect("portal:course_update", pk=pk)

        try:
            with transaction.atomic():
                course.name = name
                course.code = code
                course.credit_hours = credit_hours
                course.save()
            messages.success(request, "Course updated successfully.")
            return redirect("portal:course_list")
        except Exception:
            messages.error(request, "Error updating course.")
            return redirect("portal:course_update", pk=pk)

    return render(request, "portal/course_form.html", {"course": course})


# =====================================================
# COURSE DELETE
# =====================================================
@login_required
def course_delete(request, pk):
    if not (hasattr(request.user, "staff") or request.user.is_superuser):
        messages.error(request, "Access denied.")
        return redirect("portal:home")

    course = get_object_or_404(Course, pk=pk)

    if request.method == "POST":
        course.delete()
        messages.success(request, "Course deleted successfully.")
        return redirect("portal:course_list")

    return render(request, "portal/course_confirm_delete.html", {"course": course})


# =====================================================
# STUDENT LIST
# =====================================================
@login_required
def student_list(request):
    if not (hasattr(request.user, "staff") or request.user.is_superuser):
        messages.error(request, "Access denied.")
        return redirect("portal:home")

    students_queryset = Student.objects.select_related("user").order_by("-id")
    paginator = Paginator(students_queryset, 10)
    page_number = request.GET.get("page")
    students = paginator.get_page(page_number)
    return render(request, "portal/student_list.html", {"students": students})


# =====================================================
# BULK CSV UPLOAD
# =====================================================
@staff_member_required
def upload_results(request):
    if request.method == "POST":
        csv_file = request.FILES.get("file")
        if not csv_file or not csv_file.name.endswith(".csv"):
            messages.error(request, "Please upload a valid CSV file.")
            return redirect("portal:upload_results")

        decoded_file = csv_file.read().decode("utf-8").splitlines()
        reader = csv.DictReader(decoded_file)

        success_count = 0
        error_count = 0

        for row in reader:
            try:
                student = Student.objects.get(reg_number=row["reg_number"])
                course = Course.objects.get(name=row["course"])
                semester = Semester.objects.get(name=row["semester"])
                Result.objects.update_or_create(
                    student=student,
                    course=course,
                    semester=semester,
                    defaults={"marks": float(row["marks"])}
                )
                success_count += 1
            except Exception:
                error_count += 1
                continue

        messages.success(request, f"Upload completed. Success: {success_count}, Errors: {error_count}")
        return redirect("portal:staff_dashboard")

    return render(request, "portal/upload_results.html")


# =====================================================
# DOWNLOAD CSV TEMPLATE
# =====================================================
@staff_member_required
def download_results_template(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="results_template.csv"'
    writer = csv.writer(response)
    writer.writerow(["reg_number", "course", "semester", "marks"])
    return response
# =====================================================
# CSV EXPORT
# =====================================================
@login_required
def export_excel(request):
    """
    Export all student results to CSV (Excel-readable).
    Segmented with headers for clarity.
    """
    if not (hasattr(request.user, "staff") or request.user.is_superuser):
        messages.error(request, "Access denied.")
        return redirect("portal:home")

    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="results_export.csv"'

    writer = csv.writer(response)

    # ==================== HEADER ====================
    writer.writerow(["Malawi College of Forestry & Wildlife"])
    writer.writerow(["Academic Records Export"])
    writer.writerow([])  # blank line

    # ==================== COLUMN HEADERS ====================
    writer.writerow([
        "Reg Number", "Name", "Program", "Year",
        "Course", "Semester", "Marks", "Grade", "Status"
    ])

    # ==================== DATA ROWS ====================
    for result in Result.objects.select_related("student__user", "course", "semester"):
        writer.writerow([
            result.student.reg_number,
            result.student.user.get_full_name(),
            result.student.program,
            result.student.year,
            result.course.name,
            result.semester.name,
            result.marks if result.marks is not None else "-",
            result.grade_letter or "-",
            result.status or "-"
        ])

    return response

# =====================================================
# SMART LOGIN REDIRECT
# =====================================================
@login_required
def dashboard_redirect(request):
    user = request.user
    if user.is_superuser:
        return redirect("/admin/")
    if hasattr(user, "staff"):
        return redirect("portal:staff_dashboard")
    if hasattr(user, "student"):
        return redirect("portal:student_dashboard")
    return redirect("/")