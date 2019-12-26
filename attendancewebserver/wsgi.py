#
# File: wsgi.py
#
# wsgi is used here to execute additional commands to run nfc script
#   on the start of web server, it will be only executed once
# Copyright (c) 2019 KukFight Group
# Authors:
#   Nicolaus Christian Gozali
# This program is free script/software. This program is distributed in the 
# hope that it will be useful, but WITHOUT ANY WARRANTY; without even the 
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#

import os
import subprocess

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendancewebserver.settings')

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
subprocess.Popen(['python', os.path.join(base_dir, "nfc", "nfc.py")])

application = get_wsgi_application()
