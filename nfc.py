import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendancewebserver.settings")
os.environ["BASE_DIR"] = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "attendance_web")
import django
django.setup()

import sys
import threading
import logging
import subprocess
import re
import time as sys_time
import RPi.GPIO as GPIO
from datetime import datetime, time, timedelta

from index.models import Attendance, Students, Classes

loggin_format = "%(asctime)s: %(message)s"
logging.basicConfig(format=loggin_format, level=logging.INFO, datefmt="%H:%M:%S")
new_lock = threading.Lock()

def nfc():
    logging.info('nfc started')
    while True:
        logging.info('waiting for nfc-poll')
        proc = subprocess.Popen(['nfc-poll'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, err = proc.communicate()
        item = out.decode('utf-8')
        logging.info('got item {}'.format(item))
        
        match_error = re.search("error", item, re.IGNORECASE)
        if match_error is not None:
            logging.error("nfc error, retrying in 5s")
            failure_feedback("nfc error", "retrying in 5s")
            sys_time.sleep(2)
            continue

        match = re.search("UID.*\\n ", item)
        match_timeout = re.search("nfc_initiator_poll_target: Success", item)
        
        if match_timeout is not None:
            logging.info('timeout')
        elif match is not None:
            match_pattern = re.sub('( |\\n)', '',  match.group().split(':')[1])
            logging.info('UID found {}'.format(match_pattern))
            threading.Thread(target=record_attendace, args=(match_pattern,)).start()
        else:
            failure_feedback("cant read UID of card")
    logging.info('nfc ended')

def record_attendace(uid):
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(4,GPIO.OUT)
    date_time_now = datetime.now()
    weekday = date_time_now.weekday()
    time_now = date_time_now.time()

    student = Students.objects.filter(serial_number=uid)
    class_ = Classes.objects.filter(day=weekday, time_start__lte=time_now+timedelta(10,0), time_end__gte=time_now)

    logging.info('attempt to record attendance at {}'.format(date_time_now))

    if not class_:
        logging.info('no class')
        failure_feedback("no ongoing class")
    elif not student:
        logging.info('student not found')
        new_student = Students.objects.create(serial_number=uid, name="student", npm=1000000000)
        new_student.name="student {}".format(student.id)
        new_student.save()
        student = Students.objects.filter(serial_number=uid)
        logging.info('{} registered', student.name)
    
    if class_ and student:
        logging.info(class_[0])
        logging.info(student[0])
        GPIO.output(4, GPIO.HIGH)
        attendance = Attendance.objects.create(
            student=student[0],
            class_attend=class_[0],
            time_attend=date_time_now.strftime("%Y-%m-%d %H:%M:%S")
        )
        logging.info('attendance created successfully')
        success_feedback(student[0].name[:14], str(student[0].npm))
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
        logging.info("ignoring unlock released lock error")

def failure_feedback(message_first_line="", message_second_line=""):
    if new_lock.locked():
        new_lock.release()
    try:
        with new_lock:
            subprocess.run(['python', os.path.join(os.environ.get("BASE_DIR"), 'lcd.py'), message_first_line, message_second_line])
            subprocess.run(['python', os.path.join(os.environ.get("BASE_DIR"), 'led_buzzer.py'), "failure"])
            sys_time.sleep(3)
    except RuntimeError:
        logging.info("ignoring unlock released lock error")

def display_date_time_lcd():
    logging.info("lcd display time started")
    while True:
        try:
            with new_lock:
                current_date, current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S").split(' ')
                subprocess.run(['python', os.path.join(os.environ.get("BASE_DIR"), 'lcd.py'), current_date, current_time])
            sys_time.sleep(0.9)
        except RuntimeError:
            logging.info("ignoring unlock released lock error")
    logging.info("lcd display time ended")

nfc_thread = threading.Thread(target=nfc)
lcd_thread = threading.Thread(target=display_date_time_lcd)
nfc_thread.start()
lcd_thread.start()
nfc_thread.join()
lcd_thread.join()
