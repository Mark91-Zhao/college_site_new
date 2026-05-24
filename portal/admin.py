from django.contrib import admin
from django.utils.html import format_html
from django.contrib.admin import SimpleListFilter
from .models import Student, Staff, Course, Semester, Result, SemesterPerformance

# ========================= CUSTOM STATUS FILTER =========================
class StatusFilter(SimpleListFilter):
    title = "Status"
    parameter_name = "status"

    def lookups(self, request, model_admin):
        return [
            ("Pass", "Pass"),
            ("Supplementary", "Supplementary"),
            ("Repeat", "Repeat"),
            ("Pending", "Pending"),
        ]

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            ids = [obj.id for obj in queryset if obj.status == value]
            return queryset.filter(id__in=ids)
        return queryset


# ========================= RESULT INLINE FOR STUDENTS =========================
class ResultInline(admin.TabularInline):
    model = Result
    extra = 0
    readonly_fields = ("grade_letter",)
    fields = ("course", "semester", "marks", "grade_letter")
    can_delete = False
    show_change_link = True


# ========================= SEMESTER PERFORMANCE INLINE =========================
class SemesterPerformanceInline(admin.TabularInline):
    model = SemesterPerformance
    extra = 0
    fields = ("semester", "gpa", "status_badge")
    readonly_fields = ("status_badge",)
    show_change_link = True

    def status_badge(self, obj):
        color_map = {
            "Distinction": "success",      # green
            "Upper Credit": "primary",     # dark blue
            "Lower Credit": "info",        # light blue
            "Average": "secondary",        # gray
            "Pass": "teal",                # teal
            "Repeat": "danger",            # red
            "Pending": "warning",          # yellow
        }
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color_map.get(obj.status, "secondary"),
            obj.status
        )
    status_badge.short_description = "Classification"


# ========================= STUDENT ADMIN =========================
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "reg_number",
        "user_name",
        "program",
        "year",
        "cumulative_gpa",
        "classification_display",
        "phone_number_display",
    )
    search_fields = (
        "reg_number",
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
        "phone_number",
    )
    list_filter = ("year", "program")
    ordering = ("reg_number",)
    inlines = [ResultInline, SemesterPerformanceInline]
    fields = ("user", "reg_number", "program", "year", "phone_number")

    def user_name(self, obj):
        return obj.user.get_full_name()
    user_name.short_description = "Student Name"

    def classification_display(self, obj):
        return obj.gpa_classification
    classification_display.short_description = "Classification"

    def phone_number_display(self, obj):
        return obj.phone_number or "N/A"
    phone_number_display.short_description = "Phone"


# ========================= STAFF ADMIN =========================
@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ("staff_id", "user", "department", "role")
    search_fields = ("staff_id", "user__first_name", "user__last_name", "department")
    list_filter = ("department", "role")


# ========================= SEMESTER ADMIN =========================
@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ("name", "year")
    search_fields = ("name",)
    list_filter = ("year",)
    fields = ("name", "year")


# ========================= COURSE ADMIN =========================
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "credit_hours", "semester")
    search_fields = ("code", "name")
    list_filter = ("semester",)


# ========================= RESULT ADMIN =========================
@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "semester", "marks", "grade_letter")
    list_editable = ("marks",)
    search_fields = ("student__reg_number", "course__code", "semester__name")
    list_filter = ("semester",)


# ========================= SEMESTER PERFORMANCE ADMIN =========================
@admin.register(SemesterPerformance)
class SemesterPerformanceAdmin(admin.ModelAdmin):
    list_display = ("student", "semester", "gpa", "status_badge")
    search_fields = ("student__reg_number", "semester__name")
    list_filter = ("semester", "status")

    def status_badge(self, obj):
        color_map = {
            "Distinction": "success",
            "Upper Credit": "primary",
            "Lower Credit": "info",
            "Average": "secondary",
            "Pass": "teal",
            "Repeat": "danger",
            "Pending": "warning",
        }
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color_map.get(obj.status, "secondary"),
            obj.status
        )
    status_badge.short_description = "Classification"
