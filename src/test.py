#!/usr/bin/python
#
# test 
#
import os
import sys
import RPi.GPIO as GPIO
import sensors
import time

os.system('modprobe w1-gpio')  # enable using filesystem for GPIO access
sensors.init()

while(1):
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        # sensors.terminate()           
        sys.exit()
