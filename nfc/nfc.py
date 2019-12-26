#
# File: nfc.py
#
# nfc is the main function for reading data from NFC reader and controlling
#   the flow of system. There are 3 threads run in parallel:
#       -  display_date_time, displays current date time to LCD every second
#       -  start_nfc_poll_producer, repeatedly reads input from NFC reader and 
#            puts each line of its output to a thread safe queue
#       -  start_nfc_poll_consumer, reads from queue and handles all logic,
#            writing feedback through LCD, LED and buzzer, prompts for input using
#            keypad when necessary and performs all database operations
# Copyright (c) 2019 KukFight Group
# Authors:
#   Nicolaus Christian Gozali
# This program is free script/software. This program is distributed in the 
# hope that it will be useful, but WITHOUT ANY WARRANTY; without even the 
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#

import os
import sys
import django
import threading
import logging
import subprocess
import re
import queue
import time as sys_time
from datetime import datetime, time, timedelta, date
from asynchronousfilereader import AsynchronousFileReader
import evdev
import parse
import math
import string

import RPi.GPIO as GPIO
from lcd import Lcd
from led_buzzer import LedBuzzer

os.environ["BASE_DIR"] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.environ["BASE_DIR"])
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendancewebserver.settings")
django.setup()

from django.utils import timezone
from index.models import *

logging_format = "%(asctime)s: %(message)s"
logging.basicConfig(format=logging_format, level=logging.INFO, datefmt="%H:%M:%S")

def get_current_date_time():
    return timezone.localtime(timezone.now())

class LcdLock:
    '''
    A lock to ensure that display_date_time thread does not overwrite LCD
    when there is important information displayed
    '''
    WAIT_CHECK_INTERVAL = 0.1
    def __init__(self):
        self.queue = queue.Queue()
        self.locked = False
    def __enter__(self): 
        self.queue.put(1)
    def __exit__(self, a, b, c):
        self.queue.get()
    def set_locked(self):
        self.locked = True
        sys_time.sleep(0.1)
    def set_free(self):
        self.locked = False
    def wait_empty(self):
        while True:
            if self.queue.empty() and not self.locked:
                sys_time.sleep(LcdLock.WAIT_CHECK_INTERVAL)
                return
            sys_time.sleep(LcdLock.WAIT_CHECK_INTERVAL)

class SystemState:
    '''
    Checks whether system is currently idle or having an ongoing class
    '''
    IDLE = 0
    ON_GOING_CLASS = 1
    def __init__(self):
        self.current_state = SystemState.IDLE
        self.end_class_date_time = None
        self.meeting = None
    def is_idle(self):
        self.check_still_on_going()
        return self.current_state == SystemState.IDLE
    def is_on_going_class(self):
        self.check_still_on_going()
        return self.current_state == SystemState.ON_GOING_CLASS
    def set_idle(self):
        logging.info('system state set to idle')
        self.current_state = SystemState.IDLE
        self.end_class_date_time = None
        self.meeting = None
    def set_on_going_class(self, meeting, end_class_date_time):
        logging.info('system state set to on going class ending on {}'.format(end_class_date_time))
        self.current_state = SystemState.ON_GOING_CLASS
        self.end_class_date_time = end_class_date_time
        self.meeting = meeting
    def check_still_on_going(self):
        if self.end_class_date_time is not None and self.current_state == SystemState.ON_GOING_CLASS:
            if get_current_date_time() > self.end_class_date_time:
                logging.info('system state will set to idle as {} finished', self.meeting)
                self.set_idle()
    def get_meeting(self):
        return self.meeting

class Keypad:
    '''
    An interface to read input from USB numeric keypad
    '''
    MAPPING = {
        "0": "KEY_KP0",
        "1": "KEY_KP1",
        "2": "KEY_KP2",
        "3": "KEY_KP3",
        "4": "KEY_KP4",
        "5": "KEY_KP5",
        "6": "KEY_KP6",
        "7": "KEY_KP7",
        "8": "KEY_KP8",
        "9": "KEY_KP9",
        "B": "KEY_BACKSPACE", # backspace
        "E": "KEY_KPENTER" # enter
    }
    REVERSE_MAPPING = {
        'KEY_KP0': '0',
        'KEY_KP1': '1',
        'KEY_KP2': '2',
        'KEY_KP3': '3',
        'KEY_KP4': '4',
        'KEY_KP5': '5',
        'KEY_KP6': '6',
        'KEY_KP7': '7',
        'KEY_KP8': '8',
        'KEY_KP9': '9',
        'KEY_BACKSPACE': 'B',
        'KEY_KPENTER': 'E'
    }
    def __init__(self):
        self.input_handler = subprocess.check_output( \
            ["bash", os.path.join(os.environ["BASE_DIR"], "nfc", "get_keypad_input.sh")]).decode("utf-8").strip()
        self.device = evdev.InputDevice('/dev/input/{}'.format(self.input_handler))
    def read(self, keys):
        key_codes = list(map(lambda k: Keypad.MAPPING[k], keys))
        for event in self.device.read_loop():
            if event.type == evdev.ecodes.EV_KEY:
                _, _, pressed_key, direction = \
                    parse.parse("key event at {}, {} ({}), {}", \
                    str(evdev.categorize(event)))

                if direction == "up" and pressed_key in key_codes:
                    return Keypad.REVERSE_MAPPING[pressed_key]

def start_nfc_poll_producer(queue_to_put):
    logging.info('nfc poll producer started')
    while True:
        # repeatedly read output from NFC reader and put in queue
        process = subprocess.Popen(['unbuffer', 'nfc-poll'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout = AsynchronousFileReader(process.stdout, autostart=True)
        stderr = AsynchronousFileReader(process.stderr, autostart=True)
        while not stdout.eof() or not stderr.eof():
            for line in stdout.readlines():
                queue_to_put.put(line.decode('utf-8'))
            for line in stderr.readlines():
                queue_to_put.put(line.decode('utf-8'))
            sys_time.sleep(.1)
        stdout.join()
        stderr.join()
        process.stdout.close()
        process.stderr.close()
        sys_time.sleep(.1)

def start_nfc_poll_consumer(queue_to_read, keypad, lcd, led_buzzer, system_state, lcd_lock):
    logging.info('nfc poll consumer started')
    write_to_lcd_and_lock(lcd, ["attendance", "system"])
    while True:
        # wait until queue contains an item
        nfc_output_line = queue_to_read.get()
        uid_line_match = re.search("UID.*\\n", nfc_output_line)
        if uid_line_match is None:
            continue
        # record raw data
        record = Record.objects.create(payload=uid_line_match.group())
        uid = re.sub('( |\\n)', '',  uid_line_match.group().split(':')[1])
        logging.info("read uid {}".format(uid))
        if system_state.is_idle():
            logging.info("system idle")
            lecturer = Lecturer.objects.all().filter(serial_number=uid)
            if not lecturer.exists():
                logging.info("lecturer not found")
                write_to_lcd_and_lock_failure(lcd, ["invalid", "lecturer card"], led_buzzer)
                continue
            else:
                logging.info("lecturer {} found".format(repr(lecturer[0])))
                meeting_type_input = choice_menu(lcd, lcd_lock, keypad, ["normal", "substitute"])
                if meeting_type_input == "normal":
                    course_class = get_nearest_course_class_of_lectuerer(lecturer[0], record.get_date_time)
                    if course_class is None:
                        write_to_lcd_and_lock_failure(lcd, ["no class", "found for today"], led_buzzer)
                        continue
                    meeting = Meeting.objects.create( \
                        course_class=course_class, \
                        record=record, meeting_type="0")
                else:
                    course = choice_menu(lcd, lcd_lock, keypad, \
                        Course.objects.all().filter(lecturer=lecturer[0]), lambda e: e.name)
                    course_class = choice_menu(lcd, lcd_lock, keypad, \
                        CourseClass.objects.all().filter(course=course), \
                        lambda e: "{} {}".format(e.get_day_display(), str(e.start_time)))
                    meeting = Meeting.objects.create( \
                        course_class=course_class, \
                        record=record, meeting_type="1")
                logging.info("meeting {} created".format(repr(meeting)))
                write_to_lcd_and_lock_success(lcd, [
                    "{} {}".format(meeting.course_class.course.name[:12], meeting.course_class.get_day_display()), \
                    "{} {}".format(meeting.course_class.start_time, meeting.get_meeting_type_display()[:4])], \
                    led_buzzer \
                )
                system_state.set_on_going_class(meeting, record.get_date_time + \
                    meeting.course_class.get_duration)
        else:
            logging.info("system have on going class")
            lecturer = Lecturer.objects.all().filter(serial_number=uid)
            if lecturer.exists():
                logging.info("lecturer {} found".format(repr(lecturer[0])))
                logging.info("ending class")
                write_to_lcd_and_lock(lcd, ["class ended"])
                system_state.set_idle()
                continue
            student = Student.objects.all().filter(serial_number=uid)
            if not student.exists():
                logging.info("student not found")
                npm = int(input_menu(lcd, lcd_lock, keypad, "enter npm", 10))
                student = Student.objects.create(serial_number=uid, name="", npm=npm)
                student.name = "Stud #{}".format(student.id)
                student.save()
                logging.info("student {} created".format(repr(student)))
                attendance = Attendance(student=student, meeting=system_state.get_meeting(), record=record)
                logging.info("attendance {} created".format(repr(attendance)))
                write_to_lcd_and_lock_success(lcd, [student.name, str(student.npm)], led_buzzer)
            else:
                logging.info("student {} found".format(repr(student[0])))
                current_meeting = system_state.get_meeting()
                if Attendance.objects.all().filter(student=student[0], meeting=current_meeting).exists():
                    logging.info("duplicate attendance")
                    write_to_lcd_and_lock_failure(lcd, [student[0].name, "duplicate attend"], led_buzzer)
                else:
                    attendance = Attendance.objects.create(student=student[0], meeting=current_meeting, record=record)
                    logging.info("attendance {} created".format(repr(attendance)))
                    write_to_lcd_and_lock_success(lcd, [student[0].name, str(student[0].npm)], led_buzzer)

def choice_menu(lcd, lcd_lock, keypad, choices, display_func=lambda e: e):
    '''
    helper function to display choice based menu with LCD as display and keypad as input
    '''
    lcd_lock.set_locked()
    selection = list(enumerate(choices))
    submenu_count = math.ceil(len(choices)/2)
    current_submenu_index = 0
    keypad_keys = "EB" + \
        ''.join(list(map(lambda n: str(n),list(range(min(10, len(choices)))))))
    while True:
        index = current_submenu_index*2
        first_line = "{} {}".format(selection[index][0], display_func(selection[index][1]))
        second_line = "{} {}".format(selection[index+1][0], display_func(selection[index+1][1])) \
            if index + 1 < len(choices) else ""
        write_to_lcd(lcd, [first_line, second_line])
        keypad_input = keypad.read(keypad_keys)
        if keypad_input == "E" and current_submenu_index + 1 < submenu_count:
            current_submenu_index += 1
        if keypad_input == "B" and current_submenu_index - 1 >= 0:
            current_submenu_index -= 1
        if keypad_input in string.digits:
            result = choices[int(keypad_input)]
            logging.info("choice menu selects {}".format(result))
            lcd_lock.set_free()
            return result

def input_menu(lcd, lcd_lock, keypad, prompt_message, input_length):
    '''
    helper function to display input based prompt with LCD as display and keypad as input
    '''
    lcd_lock.set_locked()
    answer=""
    write_to_lcd(lcd, [prompt_message])
    while True:
        keypad_input = keypad.read(string.digits + "BE")
        if keypad_input in string.digits and len(answer) < 10:
            answer += keypad_input
            write_to_lcd(lcd, [prompt_message, answer])
        elif keypad_input == "B":
            answer = answer[:-1]
            write_to_lcd(lcd, [prompt_message, answer])
        elif keypad_input == "E" and len(answer) == input_length:
            logging.info("input menu inputs {}".format(answer))
            lcd_lock.set_free()
            return answer

def get_nearest_course_class_of_lectuerer(lecturer, date_time):
    '''
    helper function to automatically select nearest course class on same day for specified
    lecturer, is used when lecturer selects "normal" class on card tap
    '''
    day_of_week = str(date_time.weekday())
    time = date_time.time()
    print("time", time)
    course_classes = CourseClass.objects.all().filter( \
        course__lecturer=lecturer, day=day_of_week)
    if not course_classes.exists():
        logging.info("no normal class found today")
        return None
    result = min(course_classes, key=lambda el: \
        max(datetime.combine(date.min, el.start_time), datetime.combine(date.min, time)) - \
        min(datetime.combine(date.min, el.start_time), datetime.combine(date.min, time)) )
    logging.info("get nearest course class {}".format(repr(result)))
    return result

def write_to_lcd(lcd, message):
    lcd.write(message)

def write_to_lcd_and_lock(lcd, message):
    with lcd_lock:
        lcd.write(message)
        sys_time.sleep(5)

def write_to_lcd_and_lock_success(lcd, message, led_buzzer):
    led_buzzer.trigger_success()
    write_to_lcd_and_lock(lcd, message)

def write_to_lcd_and_lock_failure(lcd, message, led_buzzer):
    led_buzzer.trigger_failure()
    write_to_lcd_and_lock(lcd, message)

def display_date_time(lcd, lcd_lock):
    while True:
        lcd_lock.wait_empty()
        write_to_lcd(lcd, get_current_date_time().strftime("%Y-%m-%d %H:%M:%S").split(' '))
        sys_time.sleep(0.5)

if __name__ == "__main__":
    logging.info("nfc main func started")

    nfc_reader_output_queue = queue.Queue()
    keypad = Keypad()
    lcd = Lcd()
    led_buzzer = LedBuzzer()
    system_state = SystemState()
    lcd_lock = LcdLock()

    threads = []
    threads.append(threading.Thread(target=start_nfc_poll_producer, \
        args=(nfc_reader_output_queue,)))
    threads.append(threading.Thread(target=start_nfc_poll_consumer, \
        args=(nfc_reader_output_queue,keypad,lcd,led_buzzer,system_state,lcd_lock)))
    threads.append(threading.Thread(target=display_date_time, args=(lcd, lcd_lock)))
    
    for func in [lambda t: t.start(), lambda t: t.join()]:
        for thread in threads:
            func(thread)
