import subprocess
import asyncio
import random
import re
import RPi.GPIO as GPIO
import time

async def produce(queue):
    print('nfc-poll producer started')
    while True:
        await asyncio.sleep(0.5)
        proc = subprocess.Popen(['nfc-poll'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, err = proc.communicate()
        print(out)
        item = out.decode('utf-8')
        await queue.put(item)


async def consume(queue):
    print('output consumer started')
    while True:
        item = await queue.get()
        match = re.search("UID.*\\n ", item)
        if match is not None:
            print('UID found')
            match_pattern = re.sub('( |\\n)', '',  match.group().split(':')[1])
            print(match_pattern)
            subprocess.run(['python', './attendancewebserver/lcd.py', match_pattern])
            GPIO.output(4, GPIO.HIGH)
            time.sleep(1)
            GPIO.output(4, GPIO.LOW)
        else:
            print('cannot read UID')
            GPIO.output(4, GPIO.LOW)
        await asyncio.sleep(0.5)

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
