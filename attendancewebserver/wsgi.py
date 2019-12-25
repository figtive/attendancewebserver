import os
import subprocess

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendancewebserver.settings')

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
subprocess.Popen(['python', os.path.join(base_dir, "nfc", "nfc.py")])

application = get_wsgi_application()
