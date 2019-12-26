#
# File: urls.py
#
# urls lists available urls in web server, this lists url for the web server
#   interface of attendance system, these are included by the root url file at
#   attendancewebserver/urls.py
# Copyright (c) 2019 KukFight Group
# Authors:
#   Andre Satria
#   Michael Sudirman
# This program is free script/software. This program is distributed in the 
# hope that it will be useful, but WITHOUT ANY WARRANTY; without even the 
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#

from django.urls import path,include
from . import views

urlpatterns = [
    path('', views.showCoursesList, name='show_courses_list'),
    path('course/<str:course_code>', views.showMeeting, name='show_meeting'),
    path('course/<str:course_code>/<str:pk>', views.showAttendance, name='show_attendance'),
    path('lecturer/<str:lecturer_npm>', views.showLecturerCourses, name='show_lecturer_course'),
    path('lecturers', views.showLecturer, name='show_lecturers'),
    path('import', views.importPage, name='import_page'),
    path('export/',views.export_csv,name='export_csv')
]
