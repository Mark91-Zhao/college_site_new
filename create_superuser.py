import os
import django
from django.contrib.auth import get_user_model

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "college_site_new.settings")
django.setup()

User = get_user_model()

username = "admin"
email = "admin@example.com"
password = "Admin12345"

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(
        username=username,
        email=email,
        password=password
    )
    print("Superuser created successfully.")
else:
    print("Superuser already exists.")