#
# File: led_buzzer.py
#
# led_buzzer offers an interface to display success or failure feedback involving
#   buzzer and green, red LED
# Copyright (c) 2019 KukFight Group
# Authors:
#   Nicolaus Christian Gozali
#   Michael Sudirman
#   Andre Satria
# This program is free script/software. This program is distributed in the 
# hope that it will be useful, but WITHOUT ANY WARRANTY; without even the 
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#

import RPi.GPIO as GPIO
import time

class LedBuzzer:
    SUCCESS_PIN = 10
    FAILURE_PIN = 12

    def __init__(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(LedBuzzer.SUCCESS_PIN, GPIO.OUT)
        GPIO.setup(LedBuzzer.FAILURE_PIN, GPIO.OUT)
    def trigger_success(self):
        for i in range(2):
            GPIO.output(LedBuzzer.SUCCESS_PIN, GPIO.HIGH)
            time.sleep(0.2)
            GPIO.output(LedBuzzer.SUCCESS_PIN, GPIO.LOW)
            time.sleep(0.2)
    def trigger_failure(self):
        GPIO.output(LedBuzzer.FAILURE_PIN, GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(LedBuzzer.FAILURE_PIN, GPIO.LOW)

