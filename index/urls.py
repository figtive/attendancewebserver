from django.urls import path,include
from . import views

urlpatterns = [
    path('',views.index,name='index'),
    path('course/<str:course_code>', views.showMeeting, name='show_attendance'),
    path('course/<str:course_code>/<str:pk>', views.showAttendance, name='show_attendance'),
    path('lecturer/<str:lecturer_npm>', views.showLecturerCourses, name='show_attendance'),
    path('lecturers', views.showLecturer, name='show_attendance'),
    path('import', views.importPage, name='show_attendance'),
]
