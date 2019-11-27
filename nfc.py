import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendancewebserver.settings")
import django
django.setup()

import sys
import subprocess
import asyncio
import random
import re
import time as sys_time

import RPi.GPIO as GPIO

from datetime import datetime, time
from index.models import Attendance, Students, Classes

async def produce(queue):
    print('nfc-poll producer started')
    while True:
        await asyncio.sleep(0.5)
        proc = subprocess.Popen(['nfc-poll'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, err = proc.communicate()
        item = out.decode('utf-8')
        
        match_error = re.search("nfc-poll: ERROR", item)
        if match_error is not None:
            print("nfc error")
            await queue.put(None)
            break

        await queue.put(item)
    print('nfc-poll producer stopped')

async def consume(queue):
    print('output consumer started')
    while True:
        item = await queue.get()
        if item is None:
            break
        print('payload: {}'.format(item))
        match = re.search("UID.*\\n ", item)
        match_timeout = re.search("nfc_initiator_poll_target: Success", item)
        
        if match_timeout is not None:
            print('timeout')
            continue
        elif match is not None:
            match_pattern = re.sub('( |\\n)', '',  match.group().split(':')[1])
            print('UID found {}'.format(match_pattern))
            record_attendace(match_pattern)
        else:
            print('cannot read UID')
            subprocess.run(['python', './lcd.py', "cant read UID"])
        await asyncio.sleep(0.5)
    print('output consumer stopped')

def record_attendace(uid):
    date_time_now = datetime.now()
    weekday = date_time_now.weekday()
    # time_now = date_time_now.time()
    time_now = time(14,2,2)

    student = Students.objects.filter(serial_number=uid)
    class_ = Classes.objects.filter(day=weekday, time_start__lte=time_now, time_end__gte=time_now)

    print('recording attendance')
    print(date_time_now)

    if not class_:
        print('no class')
        subprocess.run(['python', './lcd.py', "no ongoing class"])
        return
    print(class_[0])
    if not student:
        print('student not found')
        subprocess.run(['python', './lcd.py', "student not registered"])
        return
    print(student[0])
    if student:
        GPIO.output(4, GPIO.HIGH)
        subprocess.run(['python', './lcd.py', student[0].name[:14], str(student[0].npm)])
        attendance = Attendance.objects.create(
            student=student[0],
            class_attend=class_[0],
            time_attend=date_time_now.strftime("%Y-%m-%d %H:%M:%S")
        )
        sys_time.sleep(1)

    GPIO.output(4, GPIO.LOW)

def start_nfc():
    print("starting nfc..")
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(4,GPIO.OUT)
    loop = asyncio.get_event_loop()
    queue = asyncio.Queue(loop=loop)
    producer_coro = produce(queue)
    consumer_coro = consume(queue) 
    loop.run_until_complete(asyncio.gather(producer_coro, consumer_coro))
    loop.close()

if __name__ == "__main__":
    start_nfc()
