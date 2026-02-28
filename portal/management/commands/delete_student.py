from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from portal.models import Student

class Command(BaseCommand):
    help = "Delete both User and Student records for a given registration number"

    def add_arguments(self, parser):
        parser.add_argument("reg_number", type=str, help="Registration number of the student to delete")

    def handle(self, *args, **options):
        reg_number = options["reg_number"]

        try:
            student_deleted, _ = Student.objects.filter(reg_number=reg_number).delete()
            user_deleted, _ = User.objects.filter(username=reg_number).delete()

            if student_deleted or user_deleted:
                self.stdout.write(self.style.SUCCESS(
                    f"Successfully deleted records for registration number {reg_number}"
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f"No records found for registration number {reg_number}"
                ))

        except Exception as e:
            raise CommandError(f"Error deleting records: {e}")
