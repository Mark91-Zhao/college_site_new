from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from portal.models import Staff

class Command(BaseCommand):
    help = "Delete both User and Staff records for a given staff ID"

    def add_arguments(self, parser):
        parser.add_argument("staff_id", type=str, help="Staff ID of the staff member to delete")

    def handle(self, *args, **options):
        staff_id = options["staff_id"]

        try:
            # Delete Staff record if exists
            staff_deleted, _ = Staff.objects.filter(staff_id=staff_id).delete()

            # Delete User record if exists
            user_deleted, _ = User.objects.filter(username=staff_id).delete()

            if staff_deleted or user_deleted:
                self.stdout.write(self.style.SUCCESS(
                    f"Successfully deleted records for staff ID {staff_id}"
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f"No records found for staff ID {staff_id}"
                ))

        except Exception as e:
            raise CommandError(f"Error deleting records: {e}")
