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
new_lock = threading.Lock()

def get_current_date_time():
    return timezone.localtime(timezone.now())

class SystemState:
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
            ["bash", "nfc/get_keypad_input.sh"]).decode("utf-8").strip()
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

def start_nfc_poll_consumer(queue_to_read):
    logging.info('nfc poll consumer started')
    keypad = Keypad()
    lcd = Lcd()
    led_buzzer = LedBuzzer()
    system_state = SystemState()
    lcd.write(["attendance", "system"])
    while True:
        nfc_output_line = queue_to_read.get()
        uid_line_match = re.search("UID.*\\n", nfc_output_line)
        if uid_line_match is None:
            continue
        record = Record.objects.create(payload=uid_line_match.group())
        uid = re.sub('( |\\n)', '',  uid_line_match.group().split(':')[1])
        logging.info("read uid {}".format(uid))#CHECKED
        if system_state.is_idle():
            logging.info("system idle")
            lecturer = Lecturer.objects.all().filter(serial_number=uid)
            if not lecturer.exists():
                logging.info("lecturer not found")#CHECKED
                lcd.write(["invalid", "lecturer card"])
                led_buzzer.trigger_failure()
                continue
            else:
                logging.info("lecturer {} found".format(repr(lecturer[0])))
                lcd.write(["0 normal", "1 substitute"])
                class_input = keypad.read("01")
                if class_input == "0":
                    course_class = get_nearest_course_class_of_lectuerer(lecturer[0], record.get_date_time())
                    if course_class is None:#CHECKED
                        lcd.write(["no class", "found for today"])
                        led_buzzer.trigger_failure()
                        continue
                    meeting = Meeting.objects.create( \
                        course_class=course_class, \
                        record=record, meeting_type="0")
                else:#CHECKED
                    course = choice_menu(lcd, keypad, \
                        Course.objects.all().filter(lecturer=lecturer[0]), lambda e: e.name)
                    course_class = choice_menu(lcd, keypad, \
                        CourseClass.objects.all().filter(course=course), \
                        lambda e: "{} {}".format(e.get_day_display(), str(e.start_time)))
                    meeting = Meeting.objects.create( \
                        course_class=course_class, \
                        record=record, meeting_type="1")
                logging.info("meeting {} created".format(repr(meeting)))
                lcd.write(["{} {}".format(meeting.course_class.course.name[:12], meeting.course_class.get_day_display()), \
                    "{} {}".format(meeting.course_class.start_time, meeting.get_meeting_type_display()[:4])])
                led_buzzer.trigger_success()
                system_state.set_on_going_class(meeting, record.get_date_time() + \
                    (datetime.combine(date.min, course_class.end_time) - datetime.combine(date.min, course_class.start_time)))
        else:
            logging.info("system have on going class")
            lecturer = Lecturer.objects.all().filter(serial_number=uid)
            if lecturer.exists():#CHECKED
                logging.info("lecturer {} found".format(repr(lecturer[0])))
                logging.info("ending class")
                lcd.write(["class ended"])
                system_state.set_idle()
                continue
            student = Student.objects.all().filter(serial_number=uid)
            if not student.exists():
                logging.info("student not found")
                npm = int(input_menu(lcd, keypad, "enter npm", 10))
                student = Student.objects.create(serial_number=uid, name="", npm=npm)
                student.name = "Stud #{}".format(student.id)
                student.save()
                logging.info("student {} created".format(repr(student)))
                attendance = Attendance(student=student, meeting=system_state.get_meeting(), record=record)
                logging.info("attendance {} created".format(repr(attendance)))
                lcd.write([student.name, str(student.npm)])
                led_buzzer.trigger_success()
            else:
                logging.info("student {} found".format(repr(student[0])))
                current_meeting = system_state.get_meeting()
                if Attendance.objects.all().filter(student=student[0], meeting=current_meeting).exists():
                    logging.info("duplicate attendance")
                    lcd.write([student[0].name, "duplicate attend"])
                    led_buzzer.trigger_failure()
                else:
                    attendance = Attendance.objects.create(student=student[0], meeting=current_meeting, record=record)
                    logging.info("attendance {} created".format(repr(attendance)))
                    lcd.write([student[0].name, str(student[0].npm)])
                    led_buzzer.trigger_success()

def choice_menu(lcd, keypad, choices, display_func=lambda e: e):
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
        lcd.write([first_line, second_line])
        keypad_input = keypad.read(keypad_keys)
        if keypad_input == "E" and current_submenu_index + 1 < submenu_count:
            current_submenu_index += 1
        if keypad_input == "B" and current_submenu_index - 1 >= 0:
            current_submenu_index -= 1
        if keypad_input in string.digits:
            result = choices[int(keypad_input)]
            logging.info("choice menu selects {}".format(result))
            return result

def input_menu(lcd, keypad, prompt_message, input_length):
    answer=""
    lcd.write([prompt_message])
    while True:
        keypad_input = keypad.read(string.digits + "BE")
        if keypad_input in string.digits and len(answer) < 10:
            answer += keypad_input
            lcd.write([prompt_message, answer])
        elif keypad_input == "B":
            answer = answer[:-1]
            lcd.write([prompt_message, answer])
        elif keypad_input == "E" and len(answer) == input_length:
            logging.info("input menu inputs {}".format(answer))
            return answer

def get_nearest_course_class_of_lectuerer(lecturer, date_time):
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

if __name__ == "__main__":
    logging.info("nfc main func started")
    nfc_reader_output_queue = queue.Queue()

    threads = []
    threads.append(threading.Thread(target=start_nfc_poll_producer, \
        args=(nfc_reader_output_queue,)))
    threads.append(threading.Thread(target=start_nfc_poll_consumer, \
        args=(nfc_reader_output_queue,)))
    
    for func in [lambda t: t.start(), lambda t: t.join()]:
        for thread in threads:
            func(thread)

# =============================================================================
# PREVIOUS CODE FOR NFC.PY
# =============================================================================

# import os
# import sys
# import django
# import threading
# import logging
# import subprocess
# import re
# import time as sys_time
# from datetime import datetime, time, timedelta
# import RPi.GPIO as GPIO
# from asynchronousfilereader import AsynchronousFileReader

# os.environ["BASE_DIR"] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path.insert(0, os.environ["BASE_DIR"])
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendancewebserver.settings")
# django.setup()

# from index.models import Attendance, Student, Classes

# logging_format = "%(asctime)s: %(message)s"
# logging.basicConfig(format=logging_format, level=logging.INFO, datefmt="%H:%M:%S")
# new_lock = threading.Lock()

# def nfc():
#     logging.info('nfc started')
#     while True:
#         logging.info('waiting for nfc-poll')
#         proc = subprocess.Popen(['nfc-poll'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
#         out, err = proc.communicate()
#         item = out.decode('utf-8')
#         logging.info('got item {}'.format(item))
        
#         match_error = re.search("error", item, re.IGNORECASE)
#         if match_error is not None:
#             logging.error("nfc error, retrying in 5s")
#             failure_feedback("nfc error", "retrying in 5s")
#             sys_time.sleep(2)
#             continue

#         match = re.search("UID.*\\n ", item)
#         match_timeout = re.search("nfc_initiator_poll_target: Success", item)
        
#         if match_timeout is not None:
#             logging.info('timeout')
#         elif match is not None:
#             match_pattern = re.sub('( |\\n)', '',  match.group().split(':')[1])
#             logging.info('UID found {}'.format(match_pattern))
#             threading.Thread(target=record_attendace, args=(match_pattern,)).start()
#         else:
#             failure_feedback("cant read UID of card")
#     logging.info('nfc ended')

# def record_attendace(uid):
#     GPIO.setmode(GPIO.BCM)
#     GPIO.setwarnings(False)
#     GPIO.setup(4,GPIO.OUT)
#     date_time_now = datetime.now()
#     weekday = date_time_now.weekday()
#     time_now = date_time_now.time()

#     student = Students.objects.filter(serial_number=uid)
#     class_ = Classes.objects.filter(day=weekday, time_start__lte=time_now+timedelta(10,0), time_end__gte=time_now)

#     logging.info('attempt to record attendance at {}'.format(date_time_now))

#     if not class_:
#         logging.info('no class')
#         failure_feedback("no ongoing class")
#     elif not student:
#         logging.info('student not found')
#         new_student = Students.objects.create(serial_number=uid, name="student", npm=1000000000)
#         new_student.name="student {}".format(student.id)
#         new_student.save()
#         student = Students.objects.filter(serial_number=uid)
#         logging.info('{} registered', student.name)
    
#     if class_ and student:
#         logging.info(class_[0])
#         logging.info(student[0])
#         GPIO.output(4, GPIO.HIGH)
#         attendance = Attendance.objects.create(
#             student=student[0],
#             class_attend=class_[0],
#             time_attend=date_time_now.strftime("%Y-%m-%d %H:%M:%S")
#         )
#         logging.info('attendance created successfully')
#         success_feedback(student[0].name[:14], str(student[0].npm))
#     GPIO.output(4, GPIO.LOW)

# def success_feedback(message_first_line="", message_second_line=""):
#     if new_lock.locked():
#         new_lock.release()
#     try:
#         with new_lock:
#             subprocess.run(['python', os.path.join(os.environ.get("BASE_DIR"), 'lcd.py'), message_first_line, message_second_line])
#             subprocess.run(['python', os.path.join(os.environ.get("BASE_DIR"), 'led_buzzer.py'), "success"])
#             sys_time.sleep(3)
#     except RuntimeError:
#         logging.info("ignoring unlock released lock error")

# def failure_feedback(message_first_line="", message_second_line=""):
#     if new_lock.locked():
#         new_lock.release()
#     try:
#         with new_lock:
#             subprocess.run(['python', os.path.join(os.environ.get("BASE_DIR"), 'lcd.py'), message_first_line, message_second_line])
#             subprocess.run(['python', os.path.join(os.environ.get("BASE_DIR"), 'led_buzzer.py'), "failure"])
#             sys_time.sleep(3)
#     except RuntimeError:
#         logging.info("ignoring unlock released lock error")

# def display_date_time_lcd():
#     logging.info("lcd display time started")
#     while True:
#         try:
#             with new_lock:
#                 current_date, current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S").split(' ')
#                 subprocess.run(['python', os.path.join(os.environ.get("BASE_DIR"), 'lcd.py'), current_date, current_time])
#             sys_time.sleep(0.9)
#         except RuntimeError:
#             logging.info("ignoring unlock released lock error")
#     logging.info("lcd display time ended")

# nfc_thread = threading.Thread(target=nfc)
# lcd_thread = threading.Thread(target=display_date_time_lcd)
# nfc_thread.start()
# lcd_thread.start()
# nfc_thread.join()
# lcd_thread.join()
