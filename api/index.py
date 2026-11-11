"""Vercel serverless entrypoint for Django WSGI."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Ensure tables exist on ephemeral /tmp sqlite
import django

django.setup()
from django.core.management import call_command

try:
    call_command("migrate", "--noinput", verbosity=0)
except Exception as e:
    print("migrate warning:", e)

from django.core.wsgi import get_wsgi_application

app = get_wsgi_application()
