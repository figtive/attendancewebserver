#
# File: models.py
#
# modles defines tables and their fields in the database
# Copyright (c) 2019 KukFight Group
# Authors:
#   Nicolaus Christian Gozali
#   Aufa Wiandra Moenzil
#   Anggra Fazza Nugraha
# This program is free script/software. This program is distributed in the 
# hope that it will be useful, but WITHOUT ANY WARRANTY; without even the 
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#

from django.db import models
from django.utils import timezone
from datetime import datetime, date, timedelta

DAYS_OF_WEEK = (
    ('0', 'MON'),
    ('1', 'TUE'),
    ('2', 'WED'),
    ('3', 'THU'),
    ('4', 'FRI'),
    ('5', 'SAT'),
    ('6', 'SUN'),
)

MEETING_TYPE = (
    ('0', 'Normal'),
    ('1', 'Substitute')
)

class Student(models.Model):
    serial_number = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    npm = models.IntegerField()
    class Meta:
        unique_together = ["npm"]
    def __str__(self):
        return 'Student {}'.format(self.name)

class Lecturer(models.Model):
    serial_number = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    npm = models.IntegerField()
    class Meta:
        unique_together = ["npm"]
    def __str__(self):
        return 'Lecturer {}'.format(self.name)

class Course(models.Model):
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=50)
    lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE, related_name="lecturer")
    late_tolerance = models.IntegerField(default=10)
    class Meta:
        unique_together = ["code"]
    def __str__(self):
        return 'Course {}'.format(self.name)

class CourseClass(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="course")
    day = models.CharField(max_length=1, choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    @property
    def get_duration(self):
        return datetime.combine(date.min, self.end_time) - \
            datetime.combine(date.min, self.start_time)
    class Meta:
        unique_together = ["course", "day", "start_time"]
    def __str__(self):
        return 'Class {} {} {}-{}'.format(self.course.name, \
            self.get_day_display(), self.start_time, self.end_time)

class Record(models.Model):
    date_time = models.DateTimeField(auto_now_add=True)
    payload = models.TextField()
    @property
    def get_date_time(self):
        # gets timezone aware date time python object
        return timezone.localtime(self.date_time)
    def __str__(self):
        return 'Record {} {}'.format(self.date_time, self.payload)

class Meeting(models.Model):
    course_class = models.ForeignKey(CourseClass, on_delete=models.CASCADE, related_name="course_class")
    record = models.ForeignKey(Record, on_delete=models.CASCADE)
    meeting_type = models.CharField(max_length=1, choices=MEETING_TYPE, \
        default='0')
    def __str__(self):
        return 'Meeting {} {} {}'.format(self.course_class.course.name, \
            self.get_meeting_type_display(), self.record.date_time)

class Registration(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    def __str__(self):
        return 'Registration {} {}'.format(self.course.code, self.student.npm)

class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name="meeting")
    record = models.ForeignKey(Record, on_delete=models.CASCADE)
    @property
    def is_late(self):
        if self.record.date_time > self.meeting.record.date_time + \
            timedelta(minutes=self.meeting.course_class.course.late_tolerance):
            return True
        return False
    def __str__(self):
        return 'Attendance {} {} {}'.format(self.student.name, \
            self.meeting.course_class.course.name, self.record.date_time)
