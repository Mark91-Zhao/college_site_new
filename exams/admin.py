from django.contrib import admin
from .models import Semester, Course, Student, Result

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ("name", "start_date", "end_date")
    search_fields = ("name",)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "credit_hours")
    search_fields = ("code", "name")
    list_filter = ("credit_hours",)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("registration_number", "name", "email")
    search_fields = ("registration_number", "name", "email")

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "semester", "score")
    search_fields = ("student__registration_number", "course__code")
    list_filter = ("semester", "course")
