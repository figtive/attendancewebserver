import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendancewebserver.settings")
import django
django.setup()

from index.models import Attendance, Students, Classes
from datetime import datetime, time

uid = '040c0fe2633080'
date_time_now = datetime.now()
weekday = date_time_now.weekday()
time_now = date_time_now.time()

student = Students.objects.filter(serial_number=uid)
class_ = Classes.objects.filter(day=weekday, time_start__lte=time_now, time_end__gte=time_now)

if not class_:
    print('no class')
    exit(1)
print('class: '.format(class_[0]))
if not student:
    print('student not found')
    exit(2)
print('student: '.format(student[0]))
if student:
    attendance = Attendance.objects.create(
        student=student[0],
        class_attend=class_[0],
        time_attend=date_time_now.strftime("%Y-%m-%d %H:%M:%S")
    )