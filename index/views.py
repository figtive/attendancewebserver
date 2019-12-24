from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from .models import Attendance, Course, Meeting,Lecturer, CourseClass
from django.http import HttpResponse

def index(request):
    attendances = Attendance.objects.all()
    return render(request, 'index.html', {
        'attendances': attendances,
    })

def showMeeting(request, course_code):
    meetings = Meeting.objects.filter(course_class__course__code=course_code)
    course = Course.objects.get(code=course_code)
    print(meetings)
    return render(request, 'meetingsList.html', {
        'meetings': meetings,
        'course': course

    })

def showAttendance(request,course_code, pk):
    students = Attendance.objects.all().filter(meeting__pk=pk)
    meeting = Meeting.objects.get(pk=pk)
    return render(request, 'attendanceList.html', {
        'students': students,
        'meeting': meeting,
    })

def showLecturerCourses(request,lecturer_npm):
    courses = Course.objects.all().filter(lecturer__npm= lecturer_npm)
    lecturer = Lecturer.objects.get(npm=lecturer_npm)
    return render(request, 'lecturerCourseList.html', {
        "courses": courses,
        "lecturer": lecturer
    })


def showLecturer(request):
    lecturers = Lecturer.objects.all()
    return render(request, 'lecturersList.html', {
        "lecturers": lecturers
    })

def importPage(request):
    return render(request, 'importPage.html')

def showCoursesList(request):
    courses = Course.objects.all()
    course_class = CourseClass.objects.all()
    return render(request, 'coursesList.html', {
        "courses": courses,
        "course_class": course_class,
    })

