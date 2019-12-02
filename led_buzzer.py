import RPi.GPIO as GPIO
import time
import sys

success = 15
failure = 18

def initialize_gpio():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    for num in [success,failure]:
        GPIO.setup(num, GPIO.OUT)

def do_success_indicator():
    initialize_gpio()
    for i in range(2):
        GPIO.output(success, GPIO.HIGH)
        time.sleep(0.2)
        GPIO.output(success, GPIO.LOW)
        time.sleep(0.2)
    
def do_failure_indicator():
    initialize_gpio()
    GPIO.output(failure, GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output(failure, GPIO.LOW)

initialize_gpio()
if sys.argv[1] == "success":
    do_success_indicator()
elif sys.argv[1] == "failure":
    do_failure_indicator()
