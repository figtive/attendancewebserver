#
# File: lcd.py
#
# lcd offers an interface to write into LCD display
# Copyright (c) 2019 KukFight Group
# Authors:
#   Nicolaus Christian Gozali
#   Michael Sudirman
#   Andre Satria
# This program is free script/software. This program is distributed in the 
# hope that it will be useful, but WITHOUT ANY WARRANTY; without even the 
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#

from RPLCD import CharLCD
import RPi.GPIO as GPIO
import threading

class Lcd:
    def __init__(self, rs_pin, e_pin, data_pins):
        GPIO.setwarnings(False)
        self.lcd = CharLCD(cols=16, rows=2, pin_rs=rs_pin, pin_e=e_pin, \
            pins_data=data_pins , numbering_mode=GPIO.BOARD)
        self.lcd.clear()
        self.lock = threading.Lock()
    def write(self, lines):
        with self.lock:
            self.lcd.clear()
            self.lcd.write_string(lines[0][:16].upper())
            if len(lines) == 2:
                self.lcd.cursor_pos = (1, 0) 
                self.lcd.write_string(lines[1][:16].upper())
