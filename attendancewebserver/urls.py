#
# File: urls.py
#
# urls lists available urls in web server, this lists url for admin interface
#   and includes url specified in file index/urls.py
# Copyright (c) 2019 KukFight Group
# Authors:
#   Nicolaus Christian Gozali
#   Aufa Wiandra Moenzil
#   Anggra Fazza Nugraha
#   Michael Sudirman
#   Andre Satria
# This program is free script/software. This program is distributed in the 
# hope that it will be useful, but WITHOUT ANY WARRANTY; without even the 
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('index.urls')),
]

