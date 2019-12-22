import os
import subprocess

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendancewebserver.settings')

subprocess.Popen(['python', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "nfc.py")])

application = get_wsgi_application()
