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

from .models import Student, Staff, Course, Result
from .models import Student, Semester, SemesterPerformance
from .utils import get_or_create_student

from .forms import SemesterPerformanceForm

# =====================================================
# ROLE HELPERS
# =====================================================
def is_student(user):
    return user.is_authenticated and hasattr(user, "student")

def is_staff_member(user):
    return user.is_authenticated and hasattr(user, "staff")


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
        return render(request, "portal/home.html", {
            "role": "student",
            "student": student,
            "gpa": student.cumulative_gpa,   # ✅ FIXED
            "classification": student.gpa_classification,
        })

    return render(request, "portal/home.html", {"role": "guest"})


# =====================================================
# LOGIN VIEWS
# =====================================================
def student_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            if is_student(user):
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
            if is_staff_member(user):
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
# STUDENT DASHBOARD
# =====================================================
@login_required
def student_dashboard(request):
    if not hasattr(request.user, "student"):
        messages.error(request, "Access denied. Students only.")
        return redirect("portal:home")

    student = get_or_create_student(request.user)

    # All results for this student
    results = Result.objects.filter(student=student).select_related("semester", "course")

    # Only semesters where this student has results
    my_semesters = Semester.objects.filter(results__student=student).distinct().order_by("year", "name")

    # GPA records for this student
    semester_performances = SemesterPerformance.objects.filter(student=student)

    # Attach results + GPA to each semester object
    for sem in my_semesters:
        sem.my_results = [r for r in results if r.semester_id == sem.id]
        sp = semester_performances.filter(semester=sem).first()
        sem.my_gpa = sp.gpa if sp else None

    form = StudentUpdateForm(instance=student)

    context = {
        "student": student,
        "form": form,
        "cumulative_gpa": student.cumulative_gpa,
        "academic_status": student.gpa_classification,
        "my_semesters": my_semesters,
        "total_my_courses": results.values("course").distinct().count(),
        "total_my_results": results.count(),
    }
    return render(request, "portal/student_dashboard.html", context)

# =====================================================
# STUDENT RESULTS
# =====================================================
@login_required
def student_results(request):
    student = get_or_create_student(request.user)
    results = student.results.select_related("course", "semester").all()

    return render(request, "portal/student_results.html", {
        "student": student,
        "results": results,
    })


# =====================================================
# TRANSCRIPT HTML
# =====================================================
@login_required
def transcript(request):
    student = get_or_create_student(request.user)
    results = student.results.select_related("semester", "course").all()

    context = {
        "student": student,
        "gpa": student.cumulative_gpa,
        "classification": student.gpa_classification,
        "congratulations": all(result.status == "PASS" for result in results),
        "semester_data": results,
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
    elements.append(Paragraph("<b>MALAWI COLLEGE OF FORESTRY & WILDLIFE</b>", styles["Title"]))
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

        elements.append(Paragraph(f"<b>{semester.name}</b>", styles["Heading3"]))
        elements.append(Spacer(1, 10))

        data = [["Course", "Marks", "Credits", "Remark"]]
        for res in semester_results:
            remark = res.status
            if remark != "PASS":
                all_passed = False
            data.append([
                res.course.name,
                res.marks if res.marks is not None else "-",
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

    # ✅ Use manual GPA
    elements.append(Paragraph(f"<b>Cumulative GPA:</b> {student.cumulative_gpa or 'Not Assigned'}", styles["Heading2"]))
    elements.append(Paragraph(f"<b>Academic Classification:</b> {student.gpa_classification}", styles["Heading3"]))
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
    # ✅ Access control
    if not (hasattr(request.user, "staff") or request.user.is_superuser):
        messages.error(request, "Access denied.")
        return redirect("portal:home")

    # ================= SUMMARY COUNTS =================
    total_students = Student.objects.count()
    total_courses = Course.objects.count()
    total_semesters = Semester.objects.count()
    total_results = Result.objects.count()

    # ================= STUDENTS PAGINATION =================
    students_queryset = Student.objects.order_by("-id")
    students_paginator = Paginator(students_queryset, 10)
    student_page_number = request.GET.get("student_page")
    latest_students = students_paginator.get_page(student_page_number)

    # ================= RESULTS GROUPED BY SEMESTER =================
    student_search = request.GET.get("student_search", "").strip().lower()
    course_search = request.GET.get("course_search", "").strip().lower()

    semesters = Semester.objects.prefetch_related("results").order_by("year", "name")
    for semester in semesters:
        results = semester.results.select_related("student", "course")
        if student_search:
            results = results.filter(
                Q(student__reg_number__icontains=student_search) |
                Q(student__user__first_name__icontains=student_search) |
                Q(student__user__last_name__icontains=student_search)
            )
        if course_search:
            results = results.filter(
                Q(course__code__icontains=course_search) |
                Q(course__name__icontains=course_search)
            )
        semester.filtered_results = results

    # ================= SEMESTER GPA DATA =================
    semester_performances = SemesterPerformance.objects.select_related("student", "semester").order_by("-id")

    student_gpa_data = [
        {"student": s, "gpa": s.cumulative_gpa or 0.0}
        for s in Student.objects.all()
    ]
    top_students = sorted(student_gpa_data, key=lambda x: x["gpa"], reverse=True)[:5]
    at_risk_students = [s for s in student_gpa_data if s["gpa"] and s["gpa"] < 1.5]

    distinction_count = len([s for s in student_gpa_data if s["gpa"] and s["gpa"] >= 3.5])
    upper_count = len([s for s in student_gpa_data if s["gpa"] and 3.0 <= s["gpa"] < 3.5])
    lower_count = len([s for s in student_gpa_data if s["gpa"] and 2.5 <= s["gpa"] < 3.0])
    average_count = len([s for s in student_gpa_data if s["gpa"] and 1.5 <= s["gpa"] < 2.5])
    pass_count = len([s for s in student_gpa_data if s["gpa"] and 1.0 <= s["gpa"] < 1.5])
    fail_count = len([s for s in student_gpa_data if s["gpa"] and s["gpa"] < 1.0])

    # ================= COURSE STATS =================
    course_stats = []
    for semester in Semester.objects.prefetch_related("courses").order_by("year", "name"):
        semester_courses = []
        for course in semester.courses.all():
            results = Result.objects.filter(course=course)
            count = results.count()
            avg_mark = round(
                sum(r.marks for r in results if r.marks is not None) / count, 2
            ) if count else 0
            semester_courses.append({
                "course": course,
                "average_mark": avg_mark,
                "total_students": count
            })
        course_stats.append({
            "semester": semester,
            "courses": semester_courses
        })

    # ================= CONTEXT =================
    return render(request, "portal/staff_dashboard.html", {
        "total_students": total_students,
        "total_courses": total_courses,
        "total_semesters": total_semesters,
        "total_results": total_results,
        "students": latest_students,
        "semesters": semesters,
        "semester_performances": semester_performances,
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

    # ✅ Use manual GPA field and classification property
    gpa = student.cumulative_gpa
    classification = student.gpa_classification

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
    Allow staff or superusers to update a student's record, including manual GPA.
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
        gpa = request.POST.get("gpa", "").strip()   # ✅ new GPA field

        if not program:
            messages.error(request, "Program is required.")
            return redirect("portal:student_update_staff", pk=pk)

        try:
            year = int(year)
        except ValueError:
            messages.error(request, "Year must be a valid number.")
            return redirect("portal:student_update_staff", pk=pk)

        # ✅ Handle GPA input safely
        if gpa:
            try:
                student.cumulative_gpa = float(gpa)
            except ValueError:
                messages.error(request, "GPA must be a valid number.")
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
def add_result(request, student_id, semester_id):
    student = get_object_or_404(Student, id=student_id)
    semester = get_object_or_404(Semester, id=semester_id)

    if request.method == "POST":
        course_id = request.POST.get("course")
        marks = request.POST.get("marks")
        manual_gpa = request.POST.get("manual_gpa")

        # GPA must be provided manually
        if not manual_gpa:
            messages.error(request, "GPA is required. Please enter a value.")
            return redirect("portal:add_result", student_id=student.id, semester_id=semester.id)

        course = get_object_or_404(Course, id=course_id)

        defaults = {
            "marks": float(marks) if marks else None,
            "manual_gpa": float(manual_gpa),
        }

        Result.objects.update_or_create(
            student=student,
            course=course,
            semester=semester,
            defaults=defaults
        )

        messages.success(request, "Result saved successfully.")
        return redirect("portal:staff_dashboard")

    # ✅ Only show courses for the selected semester
    courses = Course.objects.filter(semester=semester)

    return render(request, "portal/add_result.html", {
        "student": student,
        "semester": semester,
        "courses": courses,
    })
# =====================================================
# ADD RESULT (SEMESTER)
# =====================================================
@staff_member_required
def add_result_semester(request, semester_id):
    semester = get_object_or_404(Semester, id=semester_id)
    courses = Course.objects.filter(semester=semester)
    students = Student.objects.all()

    if request.method == "POST":
        student_id = request.POST.get("student")
        gpa = request.POST.get("gpa")

        if not student_id:
            messages.error(request, "Please select a student.")
            return redirect("portal:add_result_semester", semester_id=semester.id)

        student = get_object_or_404(Student, id=student_id)

        # ✅ Save cumulative GPA once per student per semester
        if gpa:
            SemesterPerformance.objects.update_or_create(
                student=student,
                semester=semester,
                defaults={"gpa": float(gpa)}
            )

        # ✅ Save marks for each course
        for course in courses:
            marks = request.POST.get(f"marks_{course.id}")
            if marks:
                Result.objects.update_or_create(
                    student=student,
                    course=course,
                    semester=semester,
                    defaults={"marks": float(marks)}
                )

        messages.success(request, f"Results and GPA saved for {student.reg_number} in {semester.name}.")
        return redirect("portal:staff_dashboard")

    return render(request, "portal/add_result_semester.html", {
        "semester": semester,
        "students": students,
        "courses": courses,
    })


# =====================================================
# SEMESTER GPA ENTRY (STAFF ONLY)
# =====================================================
@staff_member_required
def add_semester_gpa(request, student_id, semester_id):
    student = get_object_or_404(Student, id=student_id)
    semester = get_object_or_404(Semester, id=semester_id)

    # Check if GPA record already exists
    existing = SemesterPerformance.objects.filter(student=student, semester=semester).first()

    if request.method == "POST":
        form = SemesterPerformanceForm(request.POST, instance=existing)
        if form.is_valid():
            sp = form.save(commit=False)   # don’t commit yet
            sp.student = student           # ✅ force student
            sp.semester = semester         # ✅ force semester
            sp.save()
            messages.success(request, "Semester GPA saved successfully.")
            return redirect("portal:staff_dashboard")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = SemesterPerformanceForm(instance=existing)

    return render(request, "portal/add_semester_gpa.html", {
        "form": form,
        "student": student,
        "semester": semester,
        "header": f"Enter GPA for {student.reg_number} — {semester.name} ({semester.year})"
    })

# =====================================================
# COURSE LIST
# =====================================================
@login_required
def course_list(request):
    # ✅ Access control
    if not (hasattr(request.user, "staff") or request.user.is_superuser):
        messages.error(request, "Access denied.")
        return redirect("portal:home")

    # ================= COURSE LIST BY SEMESTER =================
    # Group courses by semester, ordered by year then name
    semesters = Semester.objects.prefetch_related("courses").order_by("year", "name")

    return render(request, "portal/course_list.html", {
        "semesters": semesters
    })

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
# BULK GPA UPLOAD
# =====================================================
@staff_member_required
def upload_gpa(request):
    if request.method == "POST":
        csv_file = request.FILES.get("file")
        if not csv_file or not csv_file.name.endswith(".csv"):
            messages.error(request, "Please upload a valid CSV file.")
            return redirect("portal:upload_gpa")

        decoded_file = csv_file.read().decode("utf-8").splitlines()
        reader = csv.DictReader(decoded_file)

        success_count, error_count = 0, 0

        for row in reader:
            try:
                student = Student.objects.get(reg_number=row["reg_number"])
                semester = Semester.objects.get(name=row["semester"])
                SemesterPerformance.objects.update_or_create(
                    student=student,
                    semester=semester,
                    defaults={"gpa": float(row["gpa"])}
                )
                success_count += 1
            except Exception:
                error_count += 1
                continue

        messages.success(request, f"GPA upload completed. Success: {success_count}, Errors: {error_count}")
        return redirect("portal:staff_dashboard")

    return render(request, "portal/upload_gpa.html")
# =====================================================
# DOWNLOAD GPA TEMPLATE
# =====================================================
@staff_member_required
def download_gpa_template(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="gpa_template.csv"'
    writer = csv.writer(response)
    writer.writerow(["reg_number", "semester", "gpa"])
    return response
# =====================================================
# GPA EXPORT
# =====================================================
@login_required
def export_gpa(request):
    if not (hasattr(request.user, "staff") or request.user.is_superuser):
        messages.error(request, "Access denied.")
        return redirect("portal:home")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="gpa_export.csv"'
    writer = csv.writer(response)

    writer.writerow(["Reg Number", "Name", "Program", "Year", "Semester", "GPA"])

    for sp in SemesterPerformance.objects.select_related("student__user", "semester"):
        writer.writerow([
            sp.student.reg_number,
            sp.student.user.get_full_name(),
            sp.student.program,
            sp.student.year,
            sp.semester.name,
            sp.gpa
        ])

    return response

# =====================================================
# TRANSCRIPTS
# =====================================================
@login_required
def transcript(request):
    if not hasattr(request.user, "student"):
        messages.error(request, "Access denied.")
        return redirect("portal:home")

    student = request.user.student

    # Build semester data with results + GPA performance
    semester_data = []
    semesters = Semester.objects.all().order_by("year", "name")

    for sem in semesters:
        results = Result.objects.filter(student=student, semester=sem).select_related("course")
        performance = SemesterPerformance.objects.filter(student=student, semester=sem).first()

        if results.exists() or performance:
            semester_data.append({
                "semester": sem,
                "results": results,
                "performance": performance,
            })

    return render(request, "portal/transcript.html", {
        "student": student,
        "semester_data": semester_data,
    })

# =====================================================
# STUDENT UPDATE(SELF)
# =====================================================
@login_required
def student_update_self(request, pk):
    student = get_object_or_404(Student, pk=pk, user=request.user)

    if request.method == "POST":
        form = StudentUpdateForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("portal:student_dashboard")
    else:
        form = StudentUpdateForm(instance=student)

    semesters = Semester.objects.order_by("year", "name")
    semester_performances = SemesterPerformance.objects.filter(student=student).select_related("semester")
    semester_data = Result.objects.filter(student=student).select_related("course", "semester")

    return render(request, "portal/student_dashboard.html", {
        "student": student,
        "form": form,
        "semesters": semesters,
        "semester_performances": semester_performances,
        "semester_data": semester_data,
    })

# =====================================================
# AJAX HELPERS
# =====================================================
from django.http import JsonResponse

@login_required
def get_courses_by_semester(request, semester_id):
    # ✅ Restrict access to staff or superuser
    if not (hasattr(request.user, "staff") or request.user.is_superuser):
        return JsonResponse({"error": "Access denied"}, status=403)

    courses = Course.objects.filter(semester_id=semester_id).order_by("code")
    data = [{"id": c.id, "code": c.code, "name": c.name} for c in courses]
    return JsonResponse(data, safe=False)


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