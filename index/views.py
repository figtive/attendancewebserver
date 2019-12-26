#
# File: views.py
#
# views lists functions that are executed when an appointed url at index/urls.py
#   is accessed, it will contain any logic necessary to provide data and also
#   set which html file for rendered page
# Copyright (c) 2019 KukFight Group
# Authors:
#   Nicolaus Christian Gozali
#   Andre Satria
#   Michael Sudirman
# This program is free script/software. This program is distributed in the 
# hope that it will be useful, but WITHOUT ANY WARRANTY; without even the 
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#

import csv
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from .models import *
from django.http import HttpResponse

def showMeeting(request, course_code):
    meetings = Meeting.objects.filter(course_class__course__code=course_code)
    course = Course.objects.get(code=course_code)
    print(meetings)
    return render(request, 'meetingsList.html', {
        'meetings': meetings,
        'course': course
    })

def showAttendance(request,course_code, pk):
    attendances = Attendance.objects.all().filter(meeting__pk=pk)
    meeting = Meeting.objects.get(pk=pk)
    return render(request, 'attendanceList.html', {
        'attendances': attendances,
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
    response = {}
    if request.method == 'POST':
        print(request.POST["type"])
        print(request.FILES)
        if request.FILES['document'] is not None:
            uploaded_file = request.FILES['document']
            data = uploaded_file.read().decode("utf-8").split('\n')[1:]
            uploaded_name = uploaded_file.name
            if request.POST["type"] == 'Student':
                message = upload_students(data)
            elif request.POST["type"] == 'Lecturer':
                message = upload_lecturers(data)
            elif request.POST["type"] == 'Course':
                message = upload_courses(data)
            elif request.POST["type"] == 'Course Class':
                message = upload_course_classes(data)
            elif request.POST["type"] == 'Registration':
                message = upload_registrations(data)
        response["message"] = message
    return render(request, 'importPage.html', response)

def showCoursesList(request):
    courses = Course.objects.all()
    course_class = CourseClass.objects.all()
    return render(request, 'coursesList.html', {
        "courses": courses,
        "course_class": course_class,
    })

def export_csv(request):
    # Initiate csv writter
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance_summary.csv"'
    writer = csv.writer(response)
    # Call necessary database
    attendances = Attendance.objects.all()  
    courses = Course.objects.all()
    # Header 
    writer.writerow(['Course Name','NPM','Name','Attend','Absent','Total Meeting','%Attendance','Registered to Course'])
    
    for course in courses:
        meetings_in_course = Meeting.objects.all().filter(course_class__course = course)
        attendances_in_course = Attendance.objects.all().filter(meeting__in=meetings_in_course)
        student_to_attendance_count = {}
        course_name = "{} {}".format(course.code, course.name)
        total_meetings = len(meetings_in_course)
        # fill up all attendance list in a course
        for attendance in attendances_in_course:
            student_to_attendance_count[attendance.student.npm] = student_to_attendance_count.get(attendance.student.npm, 0) + 1
        # fill in course
        for student_npm, attendance_count in student_to_attendance_count.items():
            student = Student.objects.get(npm=student_npm)
            npm = student_npm
            name = student.name
            attend = attendance_count
            absent = total_meetings - attend
            attend_percentage = 100.0 * attend / total_meetings

            is_registered = Registration.objects.all().filter(course=course,student=student).exists()
            registered = 'Y' if is_registered else 'N'
    
            writer.writerow([course_name,npm,name,attend,absent,total_meetings,attend_percentage,registered])

    return response

def upload_students(data):
    print('uploading students')
    print(data)
    for line in data:
        fields = line.split(',')
        if len(fields) != 3:
            continue
        new_serial_number = fields[0]
        new_name = fields[1]
        new_npm = fields[2].strip("\r")
        try:
            item = Student.objects.get(npm=new_npm)
        except Student.DoesNotExist:
            Student.objects.create(npm=new_npm,serial_number=new_serial_number, name=new_name)
        else:
            item = Student.objects.filter(
                npm=new_npm
            ).update(
                serial_number=new_serial_number, name=new_name
            )
    print('upload students finished')
    return "upload students finished"

def upload_lecturers(data):
    print('uploading lecturers')
    print(data)
    for line in data:
        fields = line.split(',')
        if len(fields) != 3:
            continue
        new_serial_number = fields[0]
        new_name = fields[1]
        new_npm = fields[2].strip("\r")
        try:
            item = Lecturer.objects.get(npm=new_npm)
        except Lecturer.DoesNotExist:
            Lecturer.objects.create(npm=new_npm,serial_number=new_serial_number, name=new_name)
        else:
            item = Lecturer.objects.filter(
                npm=new_npm
            ).update(
                serial_number=new_serial_number, name=new_name
            )
    print('upload lecturers finished')
    return "upload lecturers finished"

def upload_courses(data):
    print('uploading courses')
    for line in data:
        fields = line.split(',')
        print(fields)
        if len(fields) != 4:
            continue
        new_code = fields[0]
        new_name = fields[1]
        new_lecturer_npm = fields[2].strip("\r")
        late_tolerance = fields[3].strip("\r")
        print(new_lecturer_npm)
        try:
            new_lecturers = Lecturer.objects.all().filter(npm=new_lecturer_npm)
        except Lecturer.DoesNotExist:
           continue
        else:
            new_lecturer = new_lecturers[0]
            try:
                item = Course.objects.get(code=new_code)
            except Course.DoesNotExist:
                Course.objects.create(code=new_code,name=new_name,lecturer=new_lecturer,late_tolerance=int(late_tolerance))
            else:
                item = Course.objects.filter(
                    code=new_code
                ).update(
                    name=new_name,lecturer=new_lecturer
                )
    print('upload courses finished')
    return "upload courses finished"

def upload_course_classes(data):
    print('uploading course classes')
    DAYS_OF_WEEK = {
        'Monday' : '0',
        'Tuesday' : '1',
        'Wednesday' : '2',
        'Thursday': '3',
        'Friday' : '4',
        'Saturday' : '5',
        'Sunday' : '6'
    }
    for line in data:
        fields = line.split(',')
        print(fields)
        if len(fields) != 4:
            continue
        new_code = fields[0]
        new_day = DAYS_OF_WEEK[fields[1]]
        new_start_time = fields[2]
        new_end_time = fields[3].strip("\r")
        try:
            new_courses = Course.objects.all().filter(code=new_code)
        except Course.DoesNotExist:
            continue
        else:
            new_course = new_courses[0]
            try:
                item = CourseClass.objects.get(course=new_course,day=new_day,start_time=new_start_time)
            except CourseClass.DoesNotExist:
                CourseClass.objects.create(course=new_course,day=new_day,start_time=new_start_time,end_time=new_end_time)
            else:
                item = CourseClass.objects.filter(
                    course=new_course,day=new_day,start_time=new_start_time
                ).update(
                    end_time=new_end_time
                )
    print('upload course classes finished')
    return "upload course classes finished"

def upload_registrations(data):
    print('uploading registrations')
    for line in data:
        fields = line.split(',')
        print(fields)
        if len(fields) != 2:
            print('does not exist')
            continue
        new_course_code = fields[0]
        new_student_npm = fields[1].strip("\r")
        try:
            new_courses = Course.objects.all().filter(code=new_course_code)
        except Course.DoesNotExist:
            continue
        try:
            new_students = Student.objects.all().filter(npm=new_student_npm)
        except Student.DoesNotExist:
            continue
        new_course = new_courses[0]
        new_student = new_students[0]
        try:
            item = Registration.objects.get(course=new_course,student=new_student)
        except Registration.DoesNotExist:
            Registration.objects.create(course=new_course,student=new_student)
    print('upload registrations finished')
    return "upload registrations finished"