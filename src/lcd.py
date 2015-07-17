#!/usr/bin/python
"""
# --------------------------------------
#    ___  ___  _ ____
#   / _ \/ _ \(_) __/__  __ __
#  / , _/ ___/ /\ \/ _ \/ // /
# /_/|_/_/  /_/___/ .__/\_, /
#                /_/   /___/
#
#  lcd_16x2.py
#  16x2 LCD Test Script
#
# Author : Matt Hawkins
# Date   : 06/04/2015
# Edited for tmon by Joachim Elen
# Date   : 19/05/2015
#
# http://www.raspberrypi-spy.co.uk/
#
# --------------------------------------

# The wiring for the LCD is as follows:
# 1 : GND
# 2 : 5V
# 3 : Contrast (0-5V)*
# 4 : RS (Register Select)
# 5 : R/W (Read Write)       - GROUND THIS PIN
# 6 : Enable or Strobe
# 7 : Data Bit 0             - NOT USED
# 8 : Data Bit 1             - NOT USED
# 9 : Data Bit 2             - NOT USED
# 10: Data Bit 3             - NOT USED
# 11: Data Bit 4
# 12: Data Bit 5
# 13: Data Bit 6
# 14: Data Bit 7
# 15: LCD Backlight +5V**
# 16: LCD Backlight GND
"""

import time
import RPi.GPIO as GPIO

# Define GPIO to LCD mapping
LCD_RS = 7
LCD_E = 8
LCD_D4 = 23
LCD_D5 = 18
LCD_D6 = 15
LCD_D7 = 14

# Define some device constants
LCD_WIDTH = 16  # Maximum characters per line
LCD_CHR = True
LCD_CMD = False

LCD_LINE = (0x80, 0xC0, 0x90, 0xD0)


# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005

def init():
    """ setup GPIO """
    # GPIO.setmode(GPIO.BCM)       # Use BCM GPIO numbers
    GPIO.setup(LCD_E, GPIO.OUT)  # E
    GPIO.setup(LCD_RS, GPIO.OUT)  # RS
    GPIO.setup(LCD_D4, GPIO.OUT)  # DB4
    GPIO.setup(LCD_D5, GPIO.OUT)  # DB5
    GPIO.setup(LCD_D6, GPIO.OUT)  # DB6
    GPIO.setup(LCD_D7, GPIO.OUT)  # DB7

    # Initialise display
    cmd(0x33)  # 110011 Initialise
    cmd(0x32)  # 110010 Initialise
    cmd(0x06)  # 000110 Cursor move direction
    cmd(0x0C)  # 001100 Display On,Cursor Off, Blink Off
    cmd(0x28)  # 101000 Data length, number of lines, font size
    cmd(0x01)  # 000001 Clear display
    time.sleep(E_DELAY)


def clear():
    """ clear display """
    char(0x01)


def cmd(data):
    """ send command to display """
    GPIO.output(LCD_RS, LCD_CMD)
    writedigit(data)


def char(data):
    """ send character to display """
    GPIO.output(LCD_RS, LCD_CHR)
    writedigit(data)


def writedigit(data):
    """ write databyte to display """
    # High bits
    GPIO.output(LCD_D4, data & 0x10 != 0)
    GPIO.output(LCD_D5, data & 0x20 != 0)
    GPIO.output(LCD_D6, data & 0x40 != 0)
    GPIO.output(LCD_D7, data & 0x80 != 0)
    lcd_toggle_enable()

    # Low bits
    GPIO.output(LCD_D4, data & 0x01 != 0)
    GPIO.output(LCD_D5, data & 0x02 != 0)
    GPIO.output(LCD_D6, data & 0x04 != 0)
    GPIO.output(LCD_D7, data & 0x08 != 0)
    lcd_toggle_enable()


def lcd_toggle_enable():
    """ Toggle enable """
    time.sleep(E_DELAY)
    GPIO.output(LCD_E, True)
    time.sleep(E_PULSE)
    GPIO.output(LCD_E, False)
    time.sleep(E_DELAY)


def writeline(message, line):
    """ Send string to display """
    message = message.ljust(LCD_WIDTH, " ")
    cmd(LCD_LINE[line - 1])
    for i in range(LCD_WIDTH):
        char(ord(message[i]))

def show(line1, line2):
    """ Print 2 lines on the display """
    writeline(line1, 1)
    writeline(line2, 2)
