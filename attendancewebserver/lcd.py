from RPLCD import CharLCD
import RPi.GPIO as GPIO
import sys

GPIO.setwarnings(False)
lcd = CharLCD(cols=16, rows=2, pin_rs=37, pin_e=35,pins_data=[40, 38, 36, 32, 33, 31, 29, 23] , numbering_mode=GPIO.BOARD)
lcd.write_string(sys.argv[1])
