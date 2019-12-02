import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendancewebserver.settings")
os.environ["BASE_DIR"] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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
    lcd_lock = asyncio.Lock()
    asyncio.create_task(display_date_time_lcd(lcd_lock))

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
            asyncio.create_task(record_attendace(match_pattern, lcd_lock))
        else:
            print('cannot read UID')
            if lcd_lock.locked():
                lcd_lock.release()
            async with lcd_lock:
                subprocess.run(['python', os.path.join(os.environ.get("BASE_DIR"), 'lcd.py'), "cant read UID"])
                await asyncio.sleep(3)
        await asyncio.sleep(0.5)
    print('output consumer stopped')

async def record_attendace(uid, lcd_lock):
    date_time_now = datetime.now()
    weekday = date_time_now.weekday()
    time_now = date_time_now.time()

    student = Students.objects.filter(serial_number=uid)
    class_ = Classes.objects.filter(day=weekday, time_start__lte=time_now, time_end__gte=time_now)

    print('recording attendance')
    print(date_time_now)

    if lcd_lock.locked():
        lcd_lock.release()
    async with lcd_lock:
        if not class_:
            print('no class')
            subprocess.run(['python', os.path.join(os.environ.get("BASE_DIR"), 'lcd.py'), "no ongoing class"])
            print(class_[0])
        elif not student:
            print('student not found')
            subprocess.run(['python', os.path.join(os.environ.get("BASE_DIR"), 'lcd.py'), "student not registered"])
            print(student[0])
        elif student:
            GPIO.output(4, GPIO.HIGH)
            subprocess.run(['python', os.path.join(os.environ.get("BASE_DIR"), 'lcd.py'), student[0].name[:14], str(student[0].npm)])
            attendance = Attendance.objects.create(
                student=student[0],
                class_attend=class_[0],
                time_attend=date_time_now.strftime("%Y-%m-%d %H:%M:%S")
            )
        GPIO.output(4, GPIO.LOW)
        await asyncio.sleep(3)

async def display_date_time_lcd(lcd_lock):
    while True:
        async with lcd_lock:
            subprocess.run(['python', os.path.join(os.environ.get("BASE_DIR"), 'lcd.py'), datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        await asyncio.sleep(1)

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
