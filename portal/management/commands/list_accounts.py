import os
import csv
from django.core.management.base import BaseCommand
from portal.models import Student, Staff

class Command(BaseCommand):
    help = "List all current student registration numbers and staff IDs, and export to CSV"

    def handle(self, *args, **options):
        # Prepare data
        students = Student.objects.all().order_by("reg_number")
        staff_members = Staff.objects.all().order_by("staff_id")

        # Print to console
        if students.exists():
            self.stdout.write(self.style.SUCCESS("=== Students ==="))
            for student in students:
                self.stdout.write(
                    f"Reg Number: {student.reg_number} | Program: {student.program} | Year: {student.year}"
                )
        else:
            self.stdout.write(self.style.WARNING("No student accounts found."))

        if staff_members.exists():
            self.stdout.write(self.style.SUCCESS("\n=== Staff ==="))
            for staff in staff_members:
                self.stdout.write(
                    f"Staff ID: {staff.staff_id} | Department: {staff.department} | Role: {staff.role}"
                )
        else:
            self.stdout.write(self.style.WARNING("No staff accounts found."))

        # Export to CSV
        logs_dir = os.path.join("logs")
        os.makedirs(logs_dir, exist_ok=True)
        csv_file = os.path.join(logs_dir, "accounts_list.csv")

        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Type", "Identifier", "Name", "Program/Department", "Year/Role", "Phone"])

            for student in students:
                writer.writerow([
                    "Student",
                    student.reg_number,
                    f"{student.user.first_name} {student.user.last_name}",
                    student.program,
                    student.year,
                    student.phone_number
                ])

            for staff in staff_members:
                writer.writerow([
                    "Staff",
                    staff.staff_id,
                    f"{staff.user.first_name} {staff.user.last_name}",
                    staff.department,
                    staff.role,
                    staff.phone_number
                ])

        self.stdout.write(self.style.SUCCESS(f"\nAccounts exported to {csv_file}"))
