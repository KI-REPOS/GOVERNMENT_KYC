# backend/gov_archive_project/wsgi.py
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gov_archive_project.settings')

application = get_wsgi_application()