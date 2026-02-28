import os
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from portal.models import Student, Staff

class Command(BaseCommand):
    help = "Delete User and linked Student/Staff records for a given identifier, including orphaned Users"

    def add_arguments(self, parser):
        parser.add_argument("identifier", type=str, help="Registration number (student) or Staff ID")

    def handle(self, *args, **options):
        identifier = options["identifier"]

        try:
            # Delete Student if exists
            student_deleted, _ = Student.objects.filter(reg_number=identifier).delete()

            # Delete Staff if exists
            staff_deleted, _ = Staff.objects.filter(staff_id=identifier).delete()

            # Delete User if exists
            user_deleted, _ = User.objects.filter(username=identifier).delete()

            log_message = ""
            if student_deleted or staff_deleted or user_deleted:
                if student_deleted:
                    log_message = f"[{datetime.now()}] Deleted Student record for {identifier}\n"
                if staff_deleted:
                    log_message += f"[{datetime.now()}] Deleted Staff record for {identifier}\n"
                if user_deleted:
                    log_message += f"[{datetime.now()}] Deleted User record for {identifier}\n"

                self.stdout.write(self.style.SUCCESS(
                    f"Successfully deleted records for identifier {identifier}"
                ))
            else:
                log_message = f"[{datetime.now()}] No records found for identifier {identifier}\n"
                self.stdout.write(self.style.WARNING(
                    f"No Student, Staff, or User records found for identifier {identifier}"
                ))

            # Write to log file
            logs_dir = os.path.join("logs")
            os.makedirs(logs_dir, exist_ok=True)
            log_file = os.path.join(logs_dir, "account_deletions.log")

            with open(log_file, "a") as f:
                f.write(log_message)

        except Exception as e:
            raise CommandError(f"Error deleting records: {e}")
