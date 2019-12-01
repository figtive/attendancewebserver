from django.contrib import admin
from django.urls import path, include

import os
import subprocess

subprocess.Popen(['python', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "nfc.py")])
urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include('index.urls')),
]

