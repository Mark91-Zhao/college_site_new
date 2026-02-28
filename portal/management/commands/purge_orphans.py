import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from portal.models import Student, Staff

class Command(BaseCommand):
    help = "Scan and purge orphaned User, Student, or Staff records"

    def handle(self, *args, **options):
        logs_dir = os.path.join("logs")
        os.makedirs(logs_dir, exist_ok=True)
        log_file = os.path.join(logs_dir, "purge_orphans.log")

        log_entries = []

        # 1. Users without Student or Staff
        orphan_users = User.objects.filter(student__isnull=True, staff__isnull=True)
        for user in orphan_users:
            log_entries.append(f"[{datetime.now()}] Deleted orphan User {user.username}\n")
            user.delete()

        # 2. Students without User
        orphan_students = Student.objects.filter(user__isnull=True)
        for student in orphan_students:
            log_entries.append(f"[{datetime.now()}] Deleted orphan Student {student.reg_number}\n")
            student.delete()

        # 3. Staff without User
        orphan_staff = Staff.objects.filter(user__isnull=True)
        for staff in orphan_staff:
            log_entries.append(f"[{datetime.now()}] Deleted orphan Staff {staff.staff_id}\n")
            staff.delete()

        # Write log
        with open(log_file, "a") as f:
            for entry in log_entries:
                f.write(entry)

        if log_entries:
            self.stdout.write(self.style.SUCCESS("Orphaned records purged successfully."))
        else:
            self.stdout.write(self.style.SUCCESS("No orphaned records found."))
