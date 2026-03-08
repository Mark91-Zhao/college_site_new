import os
import django
from django.db import connections
from django.db.utils import OperationalError

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "college_site_new.settings")

django.setup()

db_conn = connections["default"]

try:
    db_conn.cursor().execute("SELECT 1;")
    print("✅ Database connection SUCCESSFUL!")
except OperationalError as e:
    print("❌ Database connection FAILED!")
    print(e)