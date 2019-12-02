import RPi.GPIO as GPIO
import time

success = 15
failure = 18

def init_GPIO():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    for num in [success,failure]:
        GPIO.setup(num,GPIO.OUT)

def success_GPIO():
    for i in range(2):
        GPIO.output(success, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(success, GPIO.LOW)
        time.sleep(0.1)
        print("done")
    
def failure_GPIO():
    GPIO.output(failure, GPIO.HIGH)
    time.sleep(0.3)
    GPIO.output(failure, GPIO.LOW)