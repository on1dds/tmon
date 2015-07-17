#!/usr/bin/python
""" tmon - temperature and contact watchdog
"""
import sys
import time
import RPi.GPIO as GPIO
import collections
import os

# import local modules
import db
import sensors
import lcd
from globals import *

__version__ = "0.1"

lcd_message = collections.namedtuple('lcd_message','name msg')

# pointer in display message queue
error_index = 0         # current message in error queue
status_index = 0        # current message in status queue

okled = False
btn_info_ispressed = False

timer_thermpoll = 0     # delay between thermometer polls
timer_clearlog = 0      # delay between log cleans
timer_blink = 0         # delay for blinking the ok led
timer_lcd = 0           # delay for status changes on display
timer_errdisp = 0       # delay for errors on display after push button

# *****************************************************
#  functions
# *****************************************************

def get_errorlist():
    """ return list of all triggered notifications """
    errorlist = []
    for _sensor in sensors.list_:
        for _alert in _sensor.alerts:
            _msg = lcd_message(name= _alert.sensor.name, msg= _alert.msg_trigger)
            if _alert.triggered:
                errorlist.append(_msg)
    return errorlist

def show_status():
    """ show sensors status or alerts on lcd display """
    global btn_info_ispressed, error_index
    global timer_lcd, timer_errdisp
    global status_index

    # check press on up button
    if not btn_info_ispressed:
        if GPIO.input(BTN_INFO):
            btn_info_ispressed = True
            timer_errdisp = now
            error_index += 1
    else:
        btn_info_ispressed = GPIO.input(BTN_INFO)

    # show errors on lcd
    if now < (timer_errdisp + DELAY_ERRDISP):
        errorlist = get_errorlist()

        if len(errorlist) > 0:
            error_index %= len(errorlist)
            lcd.show(errorlist[error_index].name, errorlist[error_index].msg)

    # show status on lcd
    elif now > timer_lcd:
        error_index = 0
        while now > timer_lcd:
            timer_lcd += DELAY_DISPLAY
        _list = sensors.getlist('Thermometer')
        if status_index < len(_list):
            _sensor = _list[status_index]
            _msg = str(round(_sensor.value, 1)) + \
                    chr(223) + " " + _sensor.name
            status_index += 1
        else:
            _msg = getipaddress()
            status_index = 0
        lcd.show("tmon " + __version__, _msg)

def mysql_is_running():
    """ check if mysql is running """
    db_cfg = cfg['db']
    tmp = os.popen("mysqladmin -u " + db_cfg['user'] + " -p" + db_cfg['pass'] + " ping").read()
    return tmp == "mysqld is alive\n"

def gpio_init():
    """ init GPIO for buttons, contact sensors and LEDs """
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(LED_OK, GPIO.OUT)        # init OK LED
    GPIO.output(LED_OK, True)
    GPIO.setup(LED_ERROR, GPIO.OUT)     # init ERROR LED
    GPIO.output(LED_ERROR, True)
    GPIO.setup(BTN_INFO, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # init info button


# *****************************************************
#  main
# *****************************************************

# initialize

# init GPIO for thermometers
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

gpio_init()
lcd.init()
lcd.show("tmon " + __version__, "initializing ...")
sensors.create()

# check for IP address
_count = 0
while not getipaddress():
    _count = _count+1
    time.sleep(1)
    lcd.show("start delayed","waiting for IP")
    if _count > 10:
        lcd.writeline("err: No IP", 2)
        terminate("No IP address was found")

lcd.writeline(getipaddress(), 2)

# hold execution while info button is pressed
# to enable reading the IP address
while GPIO.input(BTN_INFO):
    pass

# wait for mysql server when run on boot
db_cfg = False
if 'db' in cfg:
    db_cfg = cfg['db']
    if not all(x in ['server','name','user','pass','expire'] for x in db_cfg):
       terminate("database configuration incomplete")
else:
    terminate("database not configured")

_count = 0
while not mysql_is_running():
    _count = _count+1
    time.sleep(1)
    lcd.show("start delayed","awaiting mysqld")
    if _count > 10:
        lcd.writeline("err: No DB", 2)
        terminate("No mysql running")
    
        
# open/create database for logging
log = db.NewLog(db_cfg['server'], db_cfg['name'], db_cfg['user'], db_cfg['pass'], db_cfg['expire'])

# initialize event intervals
now = time.time()
timer_thermpoll = now
timer_clearlog = now
timer_blink = now
timer_lcd = now
timer_tick = now
timer_errdisp = 0

while True:
    now = time.time()

    # cleanup database
    if now > timer_clearlog:
        timer_clearlog = time.time() + DELAY_CLEARLOG
        log.clean()

    # log contact sensor changes
    if now == now:
        for _s in sensors.getlist('Contact'):
            log.write_contact(_s, now)

    # log thermometer changes
    if now > timer_thermpoll:
        timer_thermpoll = time.time() + DELAY_THERMPOLL
        for _s in sensors.getlist('Thermometer'):
            log.write_temperature(_s, now)

    # heartbeat led
    if now > timer_blink:
        timer_blink = time.time() + DELAY_BLINK
        okled = not okled
        GPIO.output(LED_OK, okled)

    if now > timer_tick:
        timer_tick = time.time() + 5
        # sys.stdout.write('.')
        # sys.stdout.flush()
        for s in sensors.list_:
            print s
        print
        
    # show status error messages
    show_status()
    GPIO.output(LED_ERROR, len(get_errorlist())>0)

    

log.close()
GPIO.output(LED_OK, False)
GPIO.output(LED_ERROR, False)
lcd.show("", "")
GPIO.cleanup()

sys.exit(0)
