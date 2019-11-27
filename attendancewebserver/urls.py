from django.contrib import admin
from django.urls import path, include

import subprocess

subprocess.Popen(['python', './nfc.py'])
urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include('index.urls')),
]

