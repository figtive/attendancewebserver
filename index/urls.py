from django.urls import path,include
from . import views

urlpatterns = [
    path('course/<str:course_code>', views.showMeeting, name='show_meeting'),
    path('course/<str:course_code>/<str:pk>', views.showAttendance, name='show_attendance'),
    path('lecturer/<str:lecturer_npm>', views.showLecturerCourses, name='show_lecturer_course'),
    path('lecturers', views.showLecturer, name='show_lecturers'),
    path('import', views.importPage, name='import_page'),
    path('', views.showCoursesList, name='show_courses_list'),
]
