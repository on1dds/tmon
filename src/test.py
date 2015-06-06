#!/usr/bin/python
#
# test 
#
import os
import sys
import RPi.GPIO as GPIO

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

# init GPIO ports
GPIO.setmode(GPIO.BCM)
GPIO.setup(9, GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(10, GPIO.IN,pull_up_down=GPIO.PUD_DOWN)

while(True):
    a = GPIO.input(9)
    b = GPIO.input(10)
    print("9=" + str(a) + ", 10=" + str(b))
