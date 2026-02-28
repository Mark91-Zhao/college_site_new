from django.db import models

class Semester(models.Model):
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.name} ({self.start_date} - {self.end_date})"


class Course(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    credit_hours = models.IntegerField(default=3)

    def __str__(self):
        return f"{self.code} - {self.name}"

class Student(models.Model):
    name = models.CharField(max_length=200)
    registration_number = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.registration_number})"

    def calculate_gpa(self, semester):
        results = Result.objects.filter(student=self, semester=semester)
        total_points = 0
        total_credits = 0
        for r in results:
            total_points += r.course.credit_hours * r.points
            total_credits += r.course.credit_hours
        if total_credits == 0:
            return 0
        return round(total_points / total_credits, 2)

    def gpa_classification(self, gpa):
        if gpa >= 3.5:
            return "Distinction"
        elif gpa >= 3.0:
            return "Upper Credit"
        elif gpa >= 2.5:
            return "Lower Credit"
        elif gpa >= 1.5:
            return "Average"
        elif gpa >= 1.0:
            return "Pass"
        else:
            return "Fail"

    def withdrawal_status(self, semester):
        gpa = self.calculate_gpa(semester)
        if gpa < 1.0:
            return "Withdrawn"
        failed_repeat = Result.objects.filter(student=self, semester=semester, score__lt=30).exists()
        if failed_repeat:
            return "Withdrawn"
        return "Active"   


class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    score = models.IntegerField()

    def __str__(self):
        return f"{self.student.registration_number} - {self.course.code} ({self.semester.name})"

    @property
    def grade(self):
        if self.score >= 80:
            return "A"
        elif self.score >= 70:
            return "B+"
        elif self.score >= 65:
            return "B"
        elif self.score >= 50:
            return "C"
        elif self.score >= 40:
            return "D"
        elif self.score >= 30:
            return "E1"
        else:
            return "E2"

    @property
    def points(self):
        if self.score >= 80:
            return 4
        elif self.score >= 70:
            return 3.5
        elif self.score >= 65:
            return 3
        elif self.score >= 50:
            return 2
        elif self.score >= 40:
            return 1
        else:
            return 0
