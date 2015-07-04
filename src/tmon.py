#!/usr/bin/python
""" tmon - temperature and contact watchdog 
"""
import sys
import time
import RPi.GPIO as GPIO
import collections
import os

# import local modules
import tlog
import sensors
import lcd
import alerts
from globals import *

__version__ = "v1.02"

message = collections.namedtuple('message','name msg')

# pointer in display message queue
error_index = 0         # current message in error queue
status_index = 0        # current message in status queue

okled = False

timer_thermpoll = 0     # delay between thermometer polls
timer_clearlog = 0      # delay between log cleans
timer_blink = 0         # delay for blinking the ok led
timer_lcd = 0           # delay for status changes on display
timer_errdisp = 0       # delay for errors on display after push button

def get_errorlist():
    """ return list of all triggered notifications """
    errorlist = []
    for _n in alerts.alerts_:
        _msg = message(name=_n.sensor_name, msg=_n.msgfault)
        if _n.error: 
            errorlist.append(_msg)
    return errorlist
        
def show_status():
    """ update display """
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
        _list = sensors.getlist(sensors.TYPE_THERMOMETER)
        if status_index < len(_list):
            _sensor = _list[status_index]
            _msg = str(round(_sensor.value, 1)) + \
                    chr(223) + " " + sensors.getname(_sensor)
            status_index += 1
        else:
            _msg = getipaddress()
            status_index = 0
        lcd.show("tmon " + __version__, _msg)

def mysql_is_running():
    tmp = os.popen("mysqladmin -u root -ppi ping").read() 
    return tmp == "mysqld is alive\n"
    
     

# initialize I/O        
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(LED_OK, GPIO.OUT)        # init OK LED
GPIO.output(LED_OK, True)
GPIO.setup(LED_ERROR, GPIO.OUT)     # init ERROR LED
GPIO.output(LED_ERROR, True)
GPIO.setup(BTN_INFO, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # init info button
btn_info_ispressed = False

# initialize LCD display
lcd.init()
lcd.show("tmon " + __version__, "initializing ...")

# create sensors list and start sensors updating threads
sensors.init()

# convert alerts from config into objects
alerts.read_from_config()

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
while GPIO.input(BTN_INFO):
    pass


# make sure mysql is running
# check for IP address
_count = 0
while not mysql_is_running():
    _count = _count+1
    time.sleep(1)
    lcd.show("start delayed","awaiting mysqld")
    if _count > 10:
        lcd.writeline("err: No DB", 2)
        terminate("No mysql running")

# open/create database for logging 
log = tlog.NewLog(cfg['db_server'], cfg['db_user'], cfg['db_pass'])

# initialize event intervals
#
now = time.time()
timer_thermpoll = now
timer_clearlog = now
timer_blink = now
timer_lcd = now
timer_errdisp = 0




for _s in sensors.list_:
    _s.lastvalue = -100
    _s.lasttime = 0

while True:
    now = time.time()

    # cleanup database
    if now > timer_clearlog:
        timer_clearlog += DELAY_CLEARLOG
        log.clean(cfg['db_expire'])

    # log contact sensor changes
    if now == now:
        for _s in sensors.getlist(sensors.TYPE_CONTACT):   
            log.contacts(_s, now)
        
    # log thermometer changes
    if now > timer_thermpoll:
        timer_thermpoll += DELAY_THERMPOLL
        for _s in sensors.getlist(sensors.TYPE_THERMOMETER):
            log.temp_changes(_s, now)
        
    # heartbeat led
    if now > timer_blink:
        timer_blink += DELAY_BLINK
        okled = not okled 
        GPIO.output(LED_OK, okled)
        
    # send alerts by e-mail or sms
    alerts.update()
        
    # show status error messages
    show_status()
    GPIO.output(LED_ERROR, len(get_errorlist())>0)

log.close()
GPIO.output(LED_OK, False)
GPIO.output(LED_ERROR, False)
lcd.show("", "")
GPIO.cleanup()

sys.exit(0)
