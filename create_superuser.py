import os
import django
from django.contrib.auth import get_user_model

# Set settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "college_site_new.settings")
django.setup()

# Get user model
User = get_user_model()

# Superuser credentials
username = "Mark"
email = "kanthitimark@gmail.com"
password = "22In1991#*#*"

# Create superuser if it doesn't exist
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print("Superuser created successfully.")
else:
    print("Superuser already exists.")