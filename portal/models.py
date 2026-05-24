"""
portal/models.py
Academic Management System
Production-Ready with Semester GPA + GPA-based Status
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver

# =====================================================
# ABSTRACT BASE MODEL
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
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student")
    reg_number = models.CharField(max_length=20, unique=True, db_index=True)
    program = models.CharField(max_length=150, db_index=True)
    year = models.PositiveIntegerField(default=1)
    phone_number = models.CharField(max_length=15, blank=True)

    class Meta:
        ordering = ["reg_number"]

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.reg_number})"

    @property
    def cumulative_gpa(self):
        gpas = [sp.gpa for sp in self.semester_performances.all() if sp.gpa is not None]
        return round(sum(gpas) / len(gpas), 2) if gpas else None

    @property
    def gpa_classification(self):
        gpa = self.cumulative_gpa
        if gpa is None:
            return "Not Assigned"
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


# =====================================================
# STAFF
# =====================================================
class Staff(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="staff")
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
    credit_hours = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE,
        related_name="courses",
        default=1   # ✅ Default semester ID (must exist in DB)
    )

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


# =====================================================
# RESULT (Course Marks + Grade Letter + Status)
# =====================================================
class Result(TimeStampedModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="results")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="results")
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name="results")

    marks = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True,
        blank=True
    )

    class Meta:
        unique_together = ("student", "course", "semester")
        indexes = [
            models.Index(fields=["student", "semester"]),
            models.Index(fields=["course"]),
        ]

    def __str__(self):
        return f"{self.student.reg_number} - {self.course.code}"

    @property
    def grade_letter(self):
        if self.marks is None:
            return None
        marks = float(self.marks)
        if marks >= 80:
            return "A"
        elif marks >= 70:
            return "B"
        elif marks >= 60:
            return "C"
        elif marks >= 50:
            return "D"
        else:
            return "F"

    @property
    def status(self):
        """
        Per-course status based on marks.
        """
        if self.marks is None:
            return "Pending"
        elif self.marks >= 40:
            return "Pass"
        else:
            return "Repeat"


# =====================================================
# SEMESTER PERFORMANCE (Stores GPA + Classification)
# =====================================================
class SemesterPerformance(TimeStampedModel):
    STATUS_CHOICES = [
        ("Distinction", "Distinction"),
        ("Upper Credit", "Upper Credit"),
        ("Lower Credit", "Lower Credit"),
        ("Average", "Average"),
        ("Pass", "Pass"),
        ("Repeat", "Repeat"),
        ("Pending", "Pending"),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="semester_performances")
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name="semester_performances")
    gpa = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(4.0)], null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending"
    )

    class Meta:
        unique_together = ("student", "semester")
        ordering = ["student", "semester"]

    def __str__(self):
        return f"{self.student.reg_number} - {self.semester.name} ({self.gpa})"

    def save(self, *args, **kwargs):
        # ✅ Auto-assign status based on GPA thresholds
        if self.gpa is None:
            self.status = "Pending"
        else:
            gpa = float(self.gpa)
            if gpa >= 3.5:
                self.status = "Distinction"
            elif gpa >= 3.0:
                self.status = "Upper Credit"
            elif gpa >= 2.5:
                self.status = "Lower Credit"
            elif gpa >= 2.0:
                self.status = "Average"
            elif gpa >= 1.0:
                self.status = "Pass"
            else:
                self.status = "Repeat"
        super().save(*args, **kwargs)


# =====================================================
# AUTO CREATE USER PROFILES
# =====================================================
@receiver(post_save, sender=User)
def create_user_profiles(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.is_staff or instance.is_superuser:
        if not hasattr(instance, "staff"):
            Staff.objects.create(
                user=instance,
                staff_id=f"STF{instance.id:04d}",
                department="Administration",
                role="Administrator",
                phone_number=""
            )
    else:
        if not hasattr(instance, "student"):
            Student.objects.create(
                user=instance,
                reg_number=instance.username,
                program="Not Assigned",
                year=1
            )
