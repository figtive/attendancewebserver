#
# File: admin.py
#
# admin lists models to show in admin interface that can be accessed at url /admin.
# Copyright (c) 2019 KukFight Group
# Authors:
#   Nicolaus Christian Gozali
#   Aufa Wiandra Moenzil
#   Anggra Fazza Nugraha
# This program is free script/software. This program is distributed in the 
# hope that it will be useful, but WITHOUT ANY WARRANTY; without even the 
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#

from django.contrib import admin
from .models import *

admin.site.register(Student)
admin.site.register(Lecturer)
admin.site.register(Course)
admin.site.register(CourseClass)
admin.site.register(Meeting)
admin.site.register(Record)
admin.site.register(Registration)
admin.site.register(Attendance)
