from RPLCD import CharLCD
import RPi.GPIO as GPIO

class Lcd:
    def __init__(self):
        GPIO.setwarnings(False)
        self.lcd = CharLCD(cols=16, rows=2, pin_rs=37, pin_e=35, \
            pins_data=[40, 38, 36, 32, 33, 31, 29, 23] , \
            numbering_mode=GPIO.BOARD)
        self.lcd.clear()
    def write(self, lines):
        self.lcd.clear()
        self.lcd.write_string(lines[0][:16].upper())
        if len(lines) == 2:
            self.lcd.cursor_pos = (1, 0) 
            self.lcd.write_string(lines[1][:16].upper())
