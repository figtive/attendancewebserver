from django.contrib import admin
from django.urls import path

import subprocess

subprocess.Popen(['python', './attendancewebserver/nfc.py'])
urlpatterns = [
    path('admin/', admin.site.urls),
]
