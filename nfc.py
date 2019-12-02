import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendancewebserver.settings")
os.environ["BASE_DIR"] = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "attendance_web")
import django
django.setup()

import sys
import threading
import subprocess
import re
import time as sys_time
import RPi.GPIO as GPIO
from datetime import datetime, time

from index.models import Attendance, Students, Classes

new_lock = threading.Lock()

def nfc():
    print('nfc started')
    while True:
        proc = subprocess.Popen(['nfc-poll'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, err = proc.communicate()
        item = out.decode('utf-8')
        print('got item {}'.format(item))
        
        match_error = re.search("error", item, re.IGNORECASE)
        if match_error is not None:
            print("nfc error")
            failure_feedback("nfc error", "retrying in 5s")
            sys_time.sleep(2)
            continue

        match = re.search("UID.*\\n ", item)
        match_timeout = re.search("nfc_initiator_poll_target: Success", item)
        
        if match_timeout is not None:
            print('timeout')
        elif match is not None:
            match_pattern = re.sub('( |\\n)', '',  match.group().split(':')[1])
            print('UID found {}'.format(match_pattern))
            threading.Thread(target=record_attendace, args=(match_pattern,)).start()
        else:
            failure_feedback("cant read UID of card")
    print('nfc ended')

def record_attendace(uid):
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(4,GPIO.OUT)
    date_time_now = datetime.now()
    weekday = date_time_now.weekday()
    time_now = date_time_now.time()

    student = Students.objects.filter(serial_number=uid)
    class_ = Classes.objects.filter(day=weekday, time_start__lte=time_now, time_end__gte=time_now)

    print('attempt to record attendance at {}'.format(date_time_now))

    if not class_:
        print('no class')
        failure_feedback("no ongoing class")
    elif not student:
        print('student not found')
        failure_feedback("student not registered")
    elif student:
        print(class_[0])
        print(student[0])
        GPIO.output(4, GPIO.HIGH)
        success_feedback(student[0].name[:14], str(student[0].npm))
        attendance = Attendance.objects.create(
            student=student[0],
            class_attend=class_[0],
            time_attend=date_time_now.strftime("%Y-%m-%d %H:%M:%S")
        )
        print('attendance created successfully')
    GPIO.output(4, GPIO.LOW)

def success_feedback(message_first_line="", message_second_line=""):
    if new_lock.locked():
        new_lock.release()
    try:
        with new_lock:
            subprocess.run(['python', os.path.join(os.environ.get("BASE_DIR"), 'lcd.py'), message_first_line, message_second_line])
            subprocess.run(['python', os.path.join(os.environ.get("BASE_DIR"), 'led_buzzer.py'), "success"])
            sys_time.sleep(3)
    except RuntimeError:
        print("ignoring unlock released lock error")

def failure_feedback(message_first_line="", message_second_line=""):
    if new_lock.locked():
        new_lock.release()
    try:
        with new_lock:
            subprocess.run(['python', os.path.join(os.environ.get("BASE_DIR"), 'lcd.py'), message_first_line, message_second_line])
            subprocess.run(['python', os.path.join(os.environ.get("BASE_DIR"), 'led_buzzer.py'), "failure"])
            sys_time.sleep(3)
    except RuntimeError:
        print("ignoring unlock released lock error")

def display_date_time_lcd():
    print("lcd display time started")
    while True:
        try:
            with new_lock:
                current_date, current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S").split(' ')
                subprocess.run(['python', os.path.join(os.environ.get("BASE_DIR"), 'lcd.py'), current_date, current_time])
            sys_time.sleep(0.9)
        except RuntimeError:
            print("ignoring unlock released lock error")
    print("lcd display time ended")

if __name__ == "__main__":
    nfc_thread = threading.Thread(target=nfc)
    lcd_thread = threading.Thread(target=display_date_time_lcd)
    nfc_thread.start()
    lcd_thread.start()
    nfc_thread.join()
    lcd_thread.join()
