# -*- coding: utf-8 -*-
""" Test module 

This modules is made to keep pylint happy
"""

import os
import RPi.GPIO as GPIO

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

# init GPIO ports
GPIO.setmode(GPIO.BCM)
GPIO.setup(9, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(10, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

while(True):
    btn_up = GPIO.input(9)
    btn_dn = GPIO.input(10)
    print("9=" + str(btn_up) + ", 10=" + str(btn_dn))
