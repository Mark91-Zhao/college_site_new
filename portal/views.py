"""
portal/views.py
Complete Consolidated Enterprise Academic System
Enhanced • Secure • Role-Based • Production Ready
"""

from io import BytesIO
import csv

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.contrib import messages
from .forms import CourseForm
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.db import transaction
from django.core.paginator import Paginator

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet

from .models import Student, Staff, Course, Semester, Result

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
        student = request.user.student
        results = student.results.select_related("semester", "course")
        gpa = calculate_gpa(results)

        return render(request, "portal/home.html", {
            "role": "student",
            "student": student,
            "gpa": gpa,
            "classification": classify_gpa(gpa),
        })

    return render(request, "portal/home.html", {"role": "guest"})


# =====================================================
# STUDENT REGISTRATION
# =====================================================

def student_register(request):

    if request.method == "POST":

        reg_number = request.POST.get("reg_number", "").strip()
        full_name = request.POST.get("full_name", "").strip()
        program = request.POST.get("program", "").strip()
        year = request.POST.get("year", "").strip()
        email = request.POST.get("email", "").strip()
        phone_number = request.POST.get("phone_number", "").strip()
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if not all([reg_number, full_name, program, year, email, password]):
            messages.error(request, "All fields are required.")
            return redirect("portal:student_register")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("portal:student_register")

        if User.objects.filter(username=reg_number).exists():
            messages.error(request, "Registration number already exists.")
            return redirect("portal:student_register")

        try:
            year = int(year)
        except ValueError:
            messages.error(request, "Year must be a valid number.")
            return redirect("portal:student_register")

        first_name, *last = full_name.split(" ")
        last_name = " ".join(last)

        with transaction.atomic():
            user = User.objects.create_user(
                username=reg_number,
                password=password,
                first_name=first_name,
                last_name=last_name,
                email=email
            )

            Student.objects.create(
                user=user,
                reg_number=reg_number,
                program=program,
                year=year,
                phone_number=phone_number
            )

        messages.success(request, "Registration successful. Please login.")
        return redirect("portal:login")

    return render(request, "portal/student_register.html")

# =====================================================
# STUDENT DASHBOARD
# =====================================================

@login_required
def student_dashboard(request):

    if not is_student(request.user):
        messages.error(request, "Access denied.")
        return redirect("portal:home")

    student = request.user.student
    results = student.results.select_related("semester", "course")

    cumulative_gpa = calculate_gpa(results)
    academic_status = classify_gpa(cumulative_gpa)

    return render(request, "portal/student_dashboard.html", {
        "student": student,
        "results": results,
        "gpa": cumulative_gpa,
        "academic_status": academic_status,
    })
# =====================================================
# STAFF DASHBOARD
# =====================================================
@login_required
def staff_dashboard(request):

    # 🔒 STRICT ACCESS CONTROL
    is_staff_profile = hasattr(request.user, "staff")
    is_group_staff = request.user.groups.filter(name="Staff").exists()
    is_superuser = request.user.is_superuser

    if not (is_staff_profile or is_group_staff or is_superuser):
        messages.error(request, "Access denied.")
        return redirect("portal:home")

    # ==========================
    # SYSTEM STATISTICS
    # ==========================
    total_students = Student.objects.count()
    total_courses = Course.objects.count()
    total_semesters = Semester.objects.count()
    total_results = Result.objects.count()

    # ==========================
    # PAGINATED RECENT STUDENTS
    # ==========================
    students_queryset = Student.objects.order_by("-id")

    students_paginator = Paginator(students_queryset, 10)  # 10 per page
    student_page_number = request.GET.get("student_page")
    latest_students = students_paginator.get_page(student_page_number)

    # ==========================
    # PAGINATED RECENT RESULTS
    # ==========================
    results_queryset = Result.objects.select_related(
        "student", "course", "semester"
    ).order_by("-id")

    results_paginator = Paginator(results_queryset, 10)
    results_page_number = request.GET.get("results_page")
    recent_results = results_paginator.get_page(results_page_number)

    # ==========================
    # GPA ANALYTICS
    # ==========================
    student_gpa_data = []

    students = Student.objects.prefetch_related("results__course")

    for student in students:

        results = student.results.all()

        total_points = 0
        total_credits = 0

        for result in results:
            total_points += result.grade_point * result.course.credit_hours
            total_credits += result.course.credit_hours

        gpa = round(total_points / total_credits, 2) if total_credits > 0 else 0.0

        student_gpa_data.append({
            "student": student,
            "gpa": gpa
        })

    top_students = sorted(
        student_gpa_data,
        key=lambda x: x["gpa"],
        reverse=True
    )[:5]

    at_risk_students = [
        s for s in student_gpa_data if s["gpa"] < 1.5
    ]

    # ==========================
    # COURSE PERFORMANCE
    # ==========================
    course_stats = []

    for course in Course.objects.all():

        results = Result.objects.filter(course=course)
        count = results.count()

        if count > 0:
            avg_mark = round(
                sum(r.marks for r in results) / count,
                2
            )
        else:
            avg_mark = 0

        course_stats.append({
            "course": course,
            "average_mark": avg_mark,
            "total_students": count
        })

    # ==========================
    # GPA DISTRIBUTION
    # ==========================
    distinction_count = len([s for s in student_gpa_data if s["gpa"] >= 3.5])
    upper_count = len([s for s in student_gpa_data if 3.0 <= s["gpa"] < 3.5])
    lower_count = len([s for s in student_gpa_data if 2.5 <= s["gpa"] < 3.0])
    average_count = len([s for s in student_gpa_data if 1.5 <= s["gpa"] < 2.5])
    fail_count = len([s for s in student_gpa_data if s["gpa"] < 1.5])

    return render(request, "portal/staff_dashboard.html", {

        "total_students": total_students,
        "total_courses": total_courses,
        "total_semesters": total_semesters,
        "total_results": total_results,

        # Now paginated
        "students": latest_students,
        "recent_results": recent_results,

        "top_students": top_students,
        "at_risk_students": at_risk_students,
        "course_stats": course_stats,

        "distinction_count": distinction_count,
        "upper_count": upper_count,
        "lower_count": lower_count,
        "average_count": average_count,
        "fail_count": fail_count,
    })
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

        messages.success(
            request,
            f"Upload completed. Success: {success_count}, Errors: {error_count}"
        )

        return redirect("portal:staff_dashboard")

    return render(request, "portal/upload_results.html")
# =====================================================
# TRANSCRIPT
# =====================================================

@login_required
def transcript(request):

    if not is_student(request.user):
        messages.error(request, "Access denied.")
        return redirect("portal:home")

    student = request.user.student
    results = student.results.select_related("semester", "course")

    gpa = calculate_gpa(results)

    return render(request, "portal/transcript.html", {
        "student": student,
        "results": results,
        "gpa": gpa,
        "classification": classify_gpa(gpa),
    })


# =====================================================
# EXPORT TRANSCRIPT PDF
# =====================================================
@login_required
def export_transcript_pdf(request):

    if not is_student(request.user):
        messages.error(request, "Access denied.")
        return redirect("portal:home")

    student = request.user.student
    results = student.results.select_related("semester", "course")

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

    # =====================================================
    # INSTITUTIONAL HEADER
    # =====================================================
    elements.append(
        Paragraph(
            "<b>MAWLLOW COLLEGE OF FORESTRY & WILDLIFE</b>",
            styles["Title"]
        )
    )

    elements.append(
        Paragraph(
            "Academic Records Office",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            "Official Transcript Document",
            styles["Normal"]
        )
    )

    elements.append(Spacer(1, 20))

    # =====================================================
    # STUDENT DETAILS
    # =====================================================
    student_info = f"""
    <b>Name:</b> {student.user.get_full_name()}<br/>
    <b>Registration Number:</b> {student.reg_number}<br/>
    <b>Program:</b> {student.program}<br/>
    <b>Year:</b> {student.year}
    """

    elements.append(Paragraph(student_info, styles["Normal"]))
    elements.append(Spacer(1, 20))

    # =====================================================
    # RESULTS TABLE
    # =====================================================
    data = [["Course", "Semester", "Marks", "Grade", "Credits"]]

    for result in results:
        data.append([
            result.course.name,
            result.semester.name,
            result.marks,
            result.grade_letter,
            result.course.credit_hours
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
    elements.append(Spacer(1, 25))

    # =====================================================
    # GPA
    # =====================================================
    gpa = calculate_gpa(results)
    classification = classify_gpa(gpa)

    elements.append(
        Paragraph(f"<b>Cumulative GPA:</b> {gpa}", styles["Heading2"])
    )

    elements.append(
        Paragraph(f"<b>Academic Status:</b> {classification}", styles["Heading3"])
    )

    elements.append(Spacer(1, 40))

    # =====================================================
    # DIGITAL SIGNATURE BLOCK
    # =====================================================
    signature_block = """
    <b>______________________________</b><br/>
    Registrar / Academic Officer<br/>
    Official Digital Signature<br/>
    """

    elements.append(Paragraph(signature_block, styles["Normal"]))

    # =====================================================
    # BUILD PDF
    # =====================================================
    document.build(elements)

    buffer.seek(0)

    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="Transcript_{student.reg_number}.pdf"'
    )

    return response
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
# STUDENT PROFILE
# =====================================================

@login_required
def student_profile(request):

    if not hasattr(request.user, "student"):
        messages.error(request, "Access denied.")
        return redirect("portal:home")

    return render(request, "portal/student_profile.html", {
        "student": request.user.student
    })


# =====================================================
# STAFF PROFILE
# =====================================================

@login_required
def staff_profile(request):

    if not hasattr(request.user, "staff"):
        messages.error(request, "Access denied.")
        return redirect("portal:home")

    return render(request, "portal/staff_profile.html", {
        "staff": request.user.staff
    })
# =====================================================
# STAFF PROFILE UPDATE
# =====================================================

@login_required
def staff_update(request, pk):

    staff = get_object_or_404(Staff, pk=pk)

    # Ensure only the owner can edit
    if request.user != staff.user:
        messages.error(request, "Access denied.")
        return redirect("portal:home")

    if request.method == "POST":

        staff.department = request.POST.get("department", "").strip()
        staff.role = request.POST.get("role", "").strip()
        staff.phone_number = request.POST.get("phone_number", "").strip()

        staff.save()

        messages.success(request, "Profile updated successfully.")
        return redirect("portal:staff_profile")

    return render(request, "portal/staff_update.html", {
        "staff": staff
    })
# =====================================================
# STUDENT LIST (STAFF ONLY)
# =====================================================
@login_required
def student_list(request):

    # Only staff, superuser, or staff profile
    if not (hasattr(request.user, "staff") or request.user.is_superuser):
        messages.error(request, "Access denied.")
        return redirect("portal:home")

    students = Student.objects.select_related("user").all()

    return render(request, "portal/student_list.html", {
        "students": students
    })
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

        with transaction.atomic():
            user = User.objects.create_user(
                username=reg_number,
                password="default123",  # You can change this logic later
                first_name=first_name,
                last_name=last_name,
                email=email
            )

            Student.objects.create(
                user=user,
                reg_number=reg_number,
                program=program,
                year=year,
                phone_number=phone_number
            )

        messages.success(request, "Student created successfully.")
        return redirect("portal:student_list")

    return render(request, "portal/student_create.html")
# =====================================================
# STUDENT DETAIL (STAFF ONLY)
# =====================================================
@login_required
def student_detail(request, pk):

    # Strict access control (staff or superuser only)
    if not (hasattr(request.user, "staff") or request.user.is_superuser):
        messages.error(request, "Access denied.")
        return redirect("portal:home")

    # Get student safely
    student = get_object_or_404(
        Student.objects.select_related("user"),
        pk=pk
    )

    # Load related results efficiently
    results = student.results.select_related("course", "semester")

    # Calculate GPA
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
def student_update(request, pk):

    # -------------------------------------------------
    # STRICT ACCESS CONTROL
    # -------------------------------------------------
    if not (hasattr(request.user, "staff") or request.user.is_superuser):
        messages.error(request, "Access denied.")
        return redirect("portal:home")

    # -------------------------------------------------
    # GET STUDENT OR 404
    # -------------------------------------------------
    student = get_object_or_404(Student.objects.select_related("user"), pk=pk)

    if request.method == "POST":

        program = request.POST.get("program", "").strip()
        year = request.POST.get("year", "").strip()
        phone_number = request.POST.get("phone_number", "").strip()

        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------
        if not program:
            messages.error(request, "Program is required.")
            return redirect("portal:student_update", pk=pk)

        try:
            year = int(year)
        except ValueError:
            messages.error(request, "Year must be a valid number.")
            return redirect("portal:student_update", pk=pk)

        # -------------------------------------------------
        # UPDATE RECORD
        # -------------------------------------------------
        student.program = program
        student.year = year
        student.phone_number = phone_number

        student.save()

        messages.success(request, "Student updated successfully.")
        return redirect("portal:student_list")

    return render(request, "portal/student_update.html", {
        "student": student
    })
# =====================================================
# STUDENT DELETE (STAFF ONLY)
# =====================================================

@login_required
def student_delete(request, pk):

    # Only staff or superuser can delete
    if not (hasattr(request.user, "staff") or request.user.is_superuser):
        messages.error(request, "Access denied.")
        return redirect("portal:home")

    student = get_object_or_404(Student, pk=pk)

    if request.method == "POST":
        student.user.delete()  # This also deletes linked Student via OneToOne
        messages.success(request, "Student deleted successfully.")
        return redirect("portal:student_list")

    return render(request, "portal/student_delete.html", {
        "student": student
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

    return render(request, "portal/course_list.html", {
        "courses": courses
    })

# =====================================================
# COURSE CREATE
# =====================================================
@login_required
def course_create(request):

    # =====================================================
    # ACCESS CONTROL
    # =====================================================
    if not (hasattr(request.user, "staff") or request.user.is_superuser):
        messages.error(request, "Access denied.")
        return redirect("portal:home")

    # =====================================================
    # POST REQUEST
    # =====================================================
    if request.method == "POST":

        name = request.POST.get("name", "").strip()
        code = request.POST.get("code", "").strip()
        credit_hours = request.POST.get("credit_hours", "").strip()

        # -------------------------------------------------
        # Basic Validation
        # -------------------------------------------------
        if not all([name, code, credit_hours]):
            messages.error(request, "All fields are required.")
            return redirect("portal:course_create")

        # -------------------------------------------------
        # Prevent Duplicate Course Code
        # -------------------------------------------------
        if Course.objects.filter(code__iexact=code).exists():
            messages.error(request, "Course code already exists.")
            return redirect("portal:course_create")

        # -------------------------------------------------
        # Validate Credit Hours
        # -------------------------------------------------
        try:
            credit_hours = int(credit_hours)
            if credit_hours <= 0:
                messages.error(request, "Credit hours must be greater than 0.")
                return redirect("portal:course_create")
        except ValueError:
            messages.error(request, "Credit hours must be a valid number.")
            return redirect("portal:course_create")

        # -------------------------------------------------
        # Save Course Safely
        # -------------------------------------------------
        try:
            with transaction.atomic():
                Course.objects.create(
                    name=name,
                    code=code,
                    credit_hours=credit_hours
                )

            messages.success(request, "Course created successfully.")
            return redirect("portal:course_list")

        except Exception:
            messages.error(request, "Error occurred while saving course.")
            return redirect("portal:course_create")

    # =====================================================
    # GET REQUEST
    # =====================================================
    return render(request, "portal/course_form.html")
# =====================================================
# COURSE UPDATE
# =====================================================
@login_required
def course_update(request, pk):

    # =====================================================
    # ACCESS CONTROL
    # =====================================================
    if not (hasattr(request.user, "staff") or request.user.is_superuser):
        messages.error(request, "Access denied.")
        return redirect("portal:home")

    course = get_object_or_404(Course, pk=pk)

    # =====================================================
    # POST REQUEST
    # =====================================================
    if request.method == "POST":

        name = request.POST.get("name", "").strip()
        code = request.POST.get("code", "").strip()
        credit_hours = request.POST.get("credit_hours", "").strip()

        # -------------------------------------------------
        # Validate Required Fields
        # -------------------------------------------------
        if not all([name, code, credit_hours]):
            messages.error(request, "All fields are required.")
            return redirect("portal:course_update", pk=pk)

        # -------------------------------------------------
        # Prevent Duplicate Code (Exclude Current Course)
        # -------------------------------------------------
        if Course.objects.filter(code__iexact=code).exclude(pk=pk).exists():
            messages.error(request, "Course code already exists.")
            return redirect("portal:course_update", pk=pk)

        # -------------------------------------------------
        # Validate Credit Hours
        # -------------------------------------------------
        try:
            credit_hours = int(credit_hours)
            if credit_hours <= 0:
                messages.error(request, "Credit hours must be greater than 0.")
                return redirect("portal:course_update", pk=pk)
        except ValueError:
            messages.error(request, "Credit hours must be a valid number.")
            return redirect("portal:course_update", pk=pk)

        # -------------------------------------------------
        # Save Safely
        # -------------------------------------------------
        try:
            from django.db import transaction

            with transaction.atomic():
                course.name = name
                course.code = code
                course.credit_hours = credit_hours
                course.save()

            messages.success(request, "Course updated successfully.")
            return redirect("portal:course_list")

        except Exception:
            messages.error(request, "Error occurred while updating course.")
            return redirect("portal:course_update", pk=pk)

    # =====================================================
    # GET REQUEST
    # =====================================================
    return render(request, "portal/course_form.html", {
        "course": course
    })
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

    return render(request, "portal/course_confirm_delete.html", {
        "course": course
    })