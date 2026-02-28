# portal/utils.py
# Utility functions for GPA and CGPA calculation
# Authored by Mark

def get_points_from_marks(marks: int) -> float:
    """
    Convert raw marks into grade points based on the grading scale.
    """
    if 80 <= marks <= 100:
        return 4.0
    elif 70 <= marks <= 79:
        return 3.5
    elif 65 <= marks <= 69:
        return 3.0
    elif 50 <= marks <= 64:
        return 2.0
    elif 40 <= marks <= 49:
        return 1.0
    elif 30 <= marks <= 39:
        return 0.0  # Fail (Supplementable)
    elif 0 <= marks <= 29:
        return 0.0  # Fail (Unsupplementable)
    else:
        return 0.0


def calculate_gpa(courses: list) -> float:
    """
    Calculate GPA for a semester.
    courses: list of dicts with keys {"marks": int, "credit_hours": int}
    """
    total_points = 0
    total_credits = 0

    for course in courses:
        marks = course.get("marks", 0)
        credits = course.get("credit_hours", 0)
        points = get_points_from_marks(marks)
        total_points += points * credits
        total_credits += credits

    if total_credits == 0:
        return 0.0

    return round(total_points / total_credits, 2)


def calculate_cgpa(semester_gpas: list) -> float:
    """
    Calculate CGPA across semesters.
    semester_gpas: list of GPA values per semester
    """
    if not semester_gpas:
        return 0.0
    return round(sum(semester_gpas) / len(semester_gpas), 2)


def classify_gpa(gpa: float) -> str:
    """
    Return classification based on GPA.
    """
    if 3.50 <= gpa <= 4.00:
        return "Distinction"
    elif 3.00 <= gpa <= 3.49:
        return "Upper Credit"
    elif 2.50 <= gpa <= 2.99:
        return "Lower Credit"
    elif 1.50 <= gpa <= 2.49:
        return "Average"
    elif 1.00 <= gpa <= 1.49:
        return "Pass"
    else:
        return "Fail"


def get_result_message(gpa: float, has_supplementary: bool, has_repeat: bool) -> str:
    """
    Return message based on GPA and supplementary/repeat status.
    """
    if gpa < 1.00:
        return "Withdrawn due to GPA below threshold."
    elif gpa >= 1.00 and not has_supplementary and not has_repeat:
        return "Congratulations, you have successfully passed this semester!"
    elif has_supplementary or has_repeat:
        return "You must repeat the course(s) listed."
    else:
        return "Result recorded."
