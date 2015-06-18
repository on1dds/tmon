#!/usr/bin/python
""" tmon - temperature and contact watchdog """
import os
import sys
import time
import MySQLdb
import RPi.GPIO as GPIO

# import sub programs
import config
import db
import sensors
import lcd
import messages
from tmglob import *

version_ = "v1.0"

class Msg(object):
    """ error messages structure """
    def __init__(self):
        self.name = ""
        self.msg = ""

def log_contacts():
    """ if contact status changes, log to database """
    for _s in sensors.getlist(sensors.TYPE_CONTACT):
        if ((_s.lasttime + UNSAVED_MAX) < now) or \
            (_s.value != _s.lastvalue):
            if _s.lastvalue != -100:
                log.write(_s.type, \
                    sensors.getalias(_s.address), \
                    _s.lastvalue)
            _val = _s.value
            log.write(_s.type, sensors.getalias(_s.address), _val)
            _s.lastvalue = _val
            _s.lasttime = now
    return True

def log_temp_changes():
    """ write temperatures to database """

    for _s in sensors.getlist(sensors.TYPE_THERMOMETER):
        # save all temperatures at least once every UNSAVED_MAX seconds
        if (_s.lasttime + UNSAVED_MAX) < now:
            log.write(_s.type, \
                sensors.getalias(_s.address), \
                _s.value)
            _s.lastvalue = _s.value
            _s.lasttime = now
            
        # handle system thermometer
        elif _s.address == 'system':
            if abs(_s.lastvalue - _s.value) > .3:
                log.write(_s.type, \
                    sensors.getalias(_s.address), \
                    _s.value)
                _s.lastvalue = _s.value
                _s.lasttime = now
                
        # handle w1 thermometers
        elif ((abs(_s.lastvalue - _s.value) > .9) and
                (round(_s.lastvalue, 1) != round(_s.value, 1))):
            if (abs(_s.lastvalue - _s.value) > .52) and \
                    (now - _s.lasttime > 60 * 5):
                log.write(_s.type, \
                    sensors.getalias(_s.address), \
                    _s.lastvalue)
            log.write(_s.type, \
                sensors.getalias(_s.address), \
                _s.value)
            _s.lastvalue = _s.value
            _s.lasttime = now
    return True
    
def get_errorlist():
    """ return list of all triggered notifications """
    errorlist = []
    for _n in messages.list_:
        _msg = Msg()
        _msg.name = _n.sensor_name
        _msg.msg = _n.msgfault
        if _n.error: 
            errorlist.append(_msg)

    return errorlist
        
def show_status():
    """ update display """
    global btn_info_ispressed, errorindex
    global timer_display, timer_errdisp 
    global lcdindex
    
    # check press on up button
    if not btn_info_ispressed:
        if GPIO.input(BTN_INFO):
            btn_info_ispressed = True
            timer_errdisp = now
            errorindex += 1
    else:
        btn_info_ispressed = GPIO.input(BTN_INFO)

    # display errormessage
    if now < (timer_errdisp + DELAY_ERRDISP): 
        errorlist = get_errorlist()

        if len(errorlist) > 0:
            errorindex %= len(errorlist)
            lcd.writeline(errorlist[errorindex].name, 1)
            lcd.writeline(errorlist[errorindex].msg, 2)
    
    # show thermometers on display
    elif now > timer_display:
        errorindex = 0
        while now > timer_display:
            timer_display += DELAY_DISPLAY
        _list = sensors.getlist(sensors.TYPE_THERMOMETER)
        if lcdindex < len(_list):
            _sensor = _list[lcdindex]
            _msg = str(round(_sensor.value, 1)) + \
                    chr(223) + " " + sensors.getname(_sensor)
            lcdindex += 1
        else:
            _msg = getipaddress()
            lcdindex = 0
        lcd.writeline("tmon " + version_, 1)
        lcd.writeline(_msg, 2)


# init GPIO
os.system('modprobe w1-gpio')  # enable using filesystem for GPIO access

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(LED_OK, GPIO.OUT)        # init OK LED
GPIO.output(LED_OK, True)

GPIO.setup(LED_ERROR, GPIO.OUT)     # init ERROR LED
GPIO.output(LED_ERROR, True)

GPIO.setup(BTN_INFO, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # init info button

btn_info_ispressed = False

# init LCD display
lcd.init()
lcd.writeline("tmon " + version_, 1)
lcd.writeline("initializing ...", 2)

# error handling I/O
errorindex = 0

# init buttons


# read config
config.readconfig("/etc/tmon.conf")


# create sensors list and start sensors updating threads
sensors.init()

# open mysql connection
log = db.SQLLog()

log.create_db(config.db_server, config.db_user, config.db_pass)


try:
    log.open(config.db_server, config.db_user, config.db_pass, config.db_name)
except MySQLdb.MySQLError:
    lcd.writeline("err: opening db", 2)
    terminate("error opening database '" + \
        config.db_name + \
        "from server '" + \
        config.db_server + "'")

time.sleep(3)


# initialize event intervals
#
now = time.time()
lcdindex = 0

timer_thermpoll = now
timer_clearlog = now
timer_blink = now
timer_display = now
timer_errdisp = 0

okledstatus = False

# check for IP address
ipaddress = getipaddress()
if ipaddress: 
    lcd.writeline(ipaddress, 2)
else:
    lcd.writeline("err: No IP", 2)
    terminate("No IP address was found")

for sensor in sensors.list_:
    sensor.lastvalue = -100
    sensor.lasttime = 0

while True:
    now = time.time()

    # cleanup database
    if now > timer_clearlog:
        timer_clearlog += DELAY_CLEARLOG
        log.clean(config.db_logexpire)

    # log contact sensor changes
    if now == now:
        log_contacts()

    # log thermometer changes
    if now > timer_thermpoll:
        timer_thermpoll += DELAY_THERMPOLL
        log_temp_changes()
    
    # heartbeat led
    if now > timer_blink:
        timer_blink += DELAY_BLINK
        okledstatus = not okledstatus 
        GPIO.output(LED_OK, okledstatus)
        
    # send notifications by e-mail or sms
    messages.handle()
        
    # show status error messages
    show_status()
    GPIO.output(LED_ERROR, len(get_errorlist())>0)

log.close()
GPIO.output(LED_OK, False)
GPIO.output(LED_ERROR, False)
lcd.writeline("", 1)
lcd.writeline("", 2)
GPIO.cleanup()

sys.exit(0)
