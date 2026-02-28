from django.contrib import admin
from .models import Student, Staff, Course, Semester, Result


# =====================================================
# STUDENT ADMIN (IMPROVED)
# =====================================================
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):

    list_display = (
        "reg_number",
        "user",
        "program",
        "year",
        "gpa",
        "gpa_classification",
        "is_withdrawn",
    )

    search_fields = (
        "reg_number",
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
    )

    list_filter = (
        "year",
        "program",
    )

    ordering = ("reg_number",)

    readonly_fields = ("gpa", "gpa_classification", "is_withdrawn")


# =====================================================
# STAFF ADMIN (IMPROVED)
# =====================================================
@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):

    list_display = (
        "staff_id",
        "user",
        "department",
        "role",
    )

    search_fields = (
        "staff_id",
        "user__username",
        "user__email",
    )

    list_filter = (
        "department",
        "role",
    )

    ordering = ("staff_id",)


# =====================================================
# COURSE ADMIN
# =====================================================
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "credit_hours",
    )

    search_fields = ("name",)

    ordering = ("name",)


# =====================================================
# SEMESTER ADMIN
# =====================================================
@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):

    list_display = ("name", "year")

    list_filter = ("year",)

    ordering = ("-year",)


# =====================================================
# RESULT ADMIN (NEW & POWERFUL)
# =====================================================
@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):

    list_display = (
        "student",
        "course",
        "semester",
        "marks",
        "grade_letter",
        "grade_point",
        "status",
    )

    search_fields = (
        "student__reg_number",
        "student__user__username",
        "course__name",
    )

    list_filter = (
        "semester",
        "course",
    )

    ordering = ("-semester",)

    readonly_fields = (
        "grade_point",
        "grade_letter",
        "status",
    )