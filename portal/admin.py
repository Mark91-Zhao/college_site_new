from django.contrib import admin
from django.utils.html import format_html
from .models import Student, Staff, Course, Semester, Result

# ========================= RESULT INLINE FOR STUDENTS =========================
class ResultInline(admin.TabularInline):
    model = Result
    extra = 0
    readonly_fields = ("grade_letter", "grade_point", "status_display")
    fields = ("course", "semester", "marks", "grade_letter", "grade_point", "status_display")
    can_delete = False
    show_change_link = True

    # Display property in inline safely
    def status_display(self, obj):
        status = obj.status or "Pending"
        if status == "PASS":
            color = "success"
        elif status == "UNSUPPLEMENTABLE FAIL":
            color = "danger"
        else:
            color = "warning"
        return format_html('<span class="badge bg-{}">{}</span>', color, status)
    status_display.short_description = "Status"


# ========================= STUDENT ADMIN =========================
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "reg_number",
        "user_name",
        "program",
        "year",
        "gpa_display",
        "classification_display",
        "withdrawn_display",
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
    inlines = [ResultInline]

    # ------------------------ Display Methods ------------------------
    def user_name(self, obj):
        return obj.user.get_full_name()
    user_name.short_description = "Student Name"

    def gpa_display(self, obj):
        return obj.gpa
    gpa_display.short_description = "GPA"

    def classification_display(self, obj):
        return obj.gpa_classification
    classification_display.short_description = "Classification"

    def withdrawn_display(self, obj):
        return obj.is_withdrawn
    withdrawn_display.short_description = "Withdrawn"

    def phone_number_display(self, obj):
        return obj.phone_number or "N/A"
    phone_number_display.short_description = "Phone"

    # ----------------- Safe Mini Dashboard -----------------
    def change_view(self, request, object_id, form_url="", extra_context=None):
        student = self.get_object(request, object_id)
        if not student:
            return super().change_view(request, object_id, form_url, extra_context=extra_context)

        results = student.results.all()

        # Python-level filtering using property
        passed = sum(1 for r in results if r.status == "PASS")
        failed = sum(1 for r in results if r.status == "UNSUPPLEMENTABLE FAIL")
        repeat = sum(1 for r in results if r.status == "REPEAT COURSE")

        gpa = student.gpa if student.gpa is not None else "N/A"
        classification = student.gpa_classification or "N/A"
        withdrawn = "Yes" if student.is_withdrawn else "No"

        mini_dashboard = format_html(
            """
            <div style="padding:10px;margin-bottom:20px;border:1px solid #ddd;border-radius:5px;background:#f9f9f9;">
                <h3>🎓 Student Summary</h3>
                <p><strong>GPA:</strong> {} | <strong>Classification:</strong> {} | <strong>Withdrawn:</strong> {}</p>
                <p>✅ Passed: {} | ❌ Failed: {} | 🔁 Repeat: {}</p>
            </div>
            """,
            gpa,
            classification,
            withdrawn,
            passed,
            failed,
            repeat,
        )

        extra_context = extra_context or {}
        extra_context["mini_dashboard"] = mini_dashboard
        return super().change_view(request, object_id, form_url, extra_context=extra_context)


# ========================= STAFF ADMIN =========================
@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = (
        "staff_id",
        "user_name",
        "department",
        "role",
        "phone_number_display",
    )

    search_fields = ("staff_id", "user__username", "user__email", "phone_number")
    list_filter = ("department", "role")
    ordering = ("staff_id",)

    # ----------------- Staff Mini Dashboard -----------------
    def change_view(self, request, object_id, form_url="", extra_context=None):
        staff = self.get_object(request, object_id)
        if not staff:
            return super().change_view(request, object_id, form_url, extra_context=extra_context)

        students_count = Student.objects.filter(program=staff.department).count()
        results_count = Result.objects.filter(student__program=staff.department).count()

        mini_dashboard = format_html(
            """
            <div style="padding:10px;margin-bottom:20px;border:1px solid #ddd;border-radius:5px;background:#f0f8ff;">
                <h3>🧑‍🏫 Staff Summary</h3>
                <p>👨‍🎓 Students Managed: {}</p>
                <p>📊 Results Entered: {}</p>
            </div>
            """,
            students_count,
            results_count,
        )

        extra_context = extra_context or {}
        extra_context["mini_dashboard"] = mini_dashboard
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def user_name(self, obj):
        return obj.user.get_full_name()
    user_name.short_description = "Staff Name"

    def phone_number_display(self, obj):
        return obj.phone_number or "N/A"
    phone_number_display.short_description = "Phone"


# ========================= COURSE ADMIN =========================
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("name", "credit_hours")
    search_fields = ("name",)
    ordering = ("name",)


# ========================= SEMESTER ADMIN =========================
@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ("name", "year")
    list_filter = ("year",)
    ordering = ("-year",)


# ========================= RESULT ADMIN =========================
@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = (
        "student_name",
        "course",
        "semester",
        "marks",
        "grade_letter",
        "grade_point",
        "status_badge",
    )

    search_fields = (
        "student__reg_number",
        "student__user__username",
        "course__name",
    )

    list_filter = ("semester", "course")
    ordering = ("-semester",)

    readonly_fields = ("grade_letter", "grade_point", "status_display")

    def student_name(self, obj):
        return obj.student.user.get_full_name()
    student_name.short_description = "Student"

    def status_display(self, obj):
        status = obj.status or "Pending"
        if status == "PASS":
            color = "success"
        elif status == "UNSUPPLEMENTABLE FAIL":
            color = "danger"
        else:
            color = "warning"
        return format_html('<span class="badge bg-{}">{}</span>', color, status)
    status_display.short_description = "Status"

    def status_badge(self, obj):
        return self.status_display(obj)
    status_badge.short_description = "Status"