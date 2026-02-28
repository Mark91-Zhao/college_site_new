import os
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from portal.models import Student, Staff

class Command(BaseCommand):
    help = "Reset password for a student or staff account by identifier and log the action"

    def add_arguments(self, parser):
        parser.add_argument("identifier", type=str, help="Registration number (student) or Staff ID")
        parser.add_argument("new_password", type=str, help="New temporary password")

    def handle(self, *args, **options):
        identifier = options["identifier"]
        new_password = options["new_password"]

        try:
            # Find User by username (reg_number or staff_id)
            user = User.objects.filter(username=identifier).first()

            if not user:
                self.stdout.write(self.style.WARNING(
                    f"No User found with identifier {identifier}"
                ))
                return

            # Reset password
            user.set_password(new_password)
            user.save()

            # Determine account type for clarity
            if Student.objects.filter(reg_number=identifier).exists():
                account_type = "Student"
            elif Staff.objects.filter(staff_id=identifier).exists():
                account_type = "Staff"
            else:
                account_type = "Unknown"

            self.stdout.write(self.style.SUCCESS(
                f"Password reset successful for {account_type} account {identifier}"
            ))

            # Log the reset
            logs_dir = os.path.join("logs")
            os.makedirs(logs_dir, exist_ok=True)
            log_file = os.path.join(logs_dir, "account_resets.log")

            with open(log_file, "a") as f:
                f.write(f"[{datetime.now()}] Reset password for {account_type} {identifier} | New password: {new_password}\n")

        except Exception as e:
            raise CommandError(f"Error resetting password: {e}")
