"""
portal/models.py
Complete Academic Management System
Production-Ready Version

Features:
✔ Authentication-linked profiles
✔ Course model with code
✔ Dedicated Result model
✔ Official GPA system
✔ GPA classification (with Average)
✔ Repeat & Withdraw logic
✔ Indexed & optimized queries
✔ Timestamp tracking
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Sum, F
from django.db.models.signals import post_save
from django.dispatch import receiver


# =====================================================
# ABSTRACT BASE MODEL (Reusable timestamps)
# =====================================================
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# =====================================================
# STUDENT
# =====================================================
class Student(TimeStampedModel):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="student"
    )

    reg_number = models.CharField(max_length=20, unique=True, db_index=True)
    program = models.CharField(max_length=150, db_index=True)
    year = models.PositiveIntegerField(default=1)
    phone_number = models.CharField(max_length=15, blank=True)

    class Meta:
        ordering = ["reg_number"]

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.reg_number})"

    # ==========================================
    # GPA CALCULATION (Optimized)
    # ==========================================
    @property
    def gpa(self):

        results = self.results.annotate(
            total_points=F("course__credit_hours") * F("marks")
        )

        total_points = 0
        total_credits = 0

        for result in self.results.all():
            total_points += result.grade_point * result.course.credit_hours
            total_credits += result.course.credit_hours

        if total_credits == 0:
            return 0.0

        return round(total_points / total_credits, 2)

    # ==========================================
    # GPA CLASSIFICATION (Includes Average)
    # ==========================================
    @property
    def gpa_classification(self):

        gpa = self.gpa

        if gpa < 1.0:
            return "Fail"
        elif gpa < 1.5:
            return "Pass"
        elif gpa < 2.5:
            return "Average"
        elif gpa < 3.0:
            return "Lower Credit"
        elif gpa < 3.5:
            return "Upper Credit"
        else:
            return "Distinction"

    @property
    def is_withdrawn(self):
        return self.gpa < 1.0


# =====================================================
# STAFF
# =====================================================
class Staff(TimeStampedModel):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="staff"
    )

    staff_id = models.CharField(max_length=20, unique=True, db_index=True)
    department = models.CharField(max_length=150, db_index=True)
    role = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15, blank=True)

    class Meta:
        ordering = ["staff_id"]

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.staff_id})"


# =====================================================
# SEMESTER
# =====================================================
class Semester(TimeStampedModel):

    name = models.CharField(max_length=50)
    year = models.PositiveIntegerField()

    class Meta:
        unique_together = ("name", "year")
        ordering = ["-year", "name"]

    def __str__(self):
        return f"{self.name} ({self.year})"


# =====================================================
# COURSE
# =====================================================
class Course(TimeStampedModel):

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=150)
    credit_hours = models.PositiveIntegerField()

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


# =====================================================
# RESULT
# =====================================================
class Result(TimeStampedModel):

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="results"
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="results"
    )

    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE,
        related_name="results"
    )

    marks = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    class Meta:
        unique_together = ("student", "course", "semester")
        indexes = [
            models.Index(fields=["student", "semester"]),
            models.Index(fields=["course"]),
        ]

    def __str__(self):
        return f"{self.student.reg_number} - {self.course.code}"

    # ==========================================
    # GRADE POINT SYSTEM
    # ==========================================
    @property
    def grade_point(self):

        if self.marks >= 80:
            return 4.0
        elif self.marks >= 70:
            return 3.5
        elif self.marks >= 65:
            return 3.0
        elif self.marks >= 50:
            return 2.0
        elif self.marks >= 40:
            return 1.0
        else:
            return 0.0

    # ==========================================
    # LETTER GRADE
    # ==========================================
    @property
    def grade_letter(self):

        if self.marks >= 80:
            return "A"
        elif self.marks >= 70:
            return "B+"
        elif self.marks >= 65:
            return "B"
        elif self.marks >= 50:
            return "C"
        elif self.marks >= 40:
            return "D"
        elif self.marks >= 30:
            return "E1"
        else:
            return "E2"

    # ==========================================
    # ACADEMIC STATUS
    # ==========================================
    @property
    def status(self):

        if self.marks < 30:
            return "UNSUPPLEMENTABLE FAIL"
        elif self.marks < 40:
            return "REPEAT COURSE"
        return "PASS"


# =====================================================
# AUTO CREATE STUDENT PROFILE
# =====================================================

@receiver(post_save, sender=User)
def create_student_profile(sender, instance, created, **kwargs):

    if created:

        # Only create Student if user is NOT staff and NOT superuser
        if not instance.is_staff and not instance.is_superuser:

            Student.objects.create(
                user=instance,
                reg_number=instance.username,
                program="Not Assigned",
                year=1
            )