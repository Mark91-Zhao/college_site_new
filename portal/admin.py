from django.contrib import admin
from .models import Student, Staff, Course, Semester, Result

# =====================================================
# STUDENT ADMIN (FIXED)
# =====================================================
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):

    list_display = (
        "reg_number",
        "user",
        "program",
        "year",
        "gpa_display",
        "classification_display",
        "withdrawn_display",
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

    # ---- Safe display methods ----

    def gpa_display(self, obj):
        return obj.gpa
    gpa_display.short_description = "GPA"

    def classification_display(self, obj):
        return obj.gpa_classification
    classification_display.short_description = "Classification"

    def withdrawn_display(self, obj):
        return obj.is_withdrawn
    withdrawn_display.short_description = "Withdrawn"

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