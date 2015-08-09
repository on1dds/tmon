#!/usr/bin/python
""" tmon - temperature and contact watchdog
"""
import sys
import time
import RPi.GPIO as GPIO
from collections import namedtuple
import os
import signal
import threading
import pickle

# import local modules
import db
import sensors
import lcd
from globals import *

__version__ = "0.1"

cfg = {}
execfile("/etc/tmon/tmonconf.py", cfg)

lcd_message = namedtuple('lcd_message', ['name', 'msg'])

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
    for sensor in sensors.list_:
        for alert in sensor.alerts:
            if alert.triggered:
                errorlist.append(lcd_message(alert.sensor.name, alert.msg_trigger))
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
    _db_cfg = cfg['db']
    tmp = os.popen("mysqladmin -u " + _db_cfg['user'] + \
        " -p" + _db_cfg['pass'] + \
        " ping").read()
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

def signal_handler(sig, frame):
    """ cleanup on exit """
    print('You pressed Ctrl+C!')
    if log:
        log.close()
    sensors.Sensor.exitapp = True
    print "awaiting threads to stop"
    while threading.active_count() > 1:
        time.sleep(0.1)
    GPIO.output(LED_OK, False)
    GPIO.output(LED_ERROR, False)
    lcd.show("", "")
    GPIO.cleanup()

    sys.exit(0)

def check_cfg():
    a = check_config(('db', ['server','name','user','pass','expire']))
    if a:
        terminate("error in", a)

    a = check_config(('twilio', ['account_sid','auth_token','number']))
    if a:
        terminate("error in", a)

    a = check_config(('mail', ['address','server','user','pass','tls','port']))
    if a:
        terminate("error in", a)
        
    return True

def check_config(check):  
    if check[0] in cfg:
        for cmd in check[1]:
            if not cmd in cfg[check[0]]:
                return check[0] + ":" + cmd
        else:
            return False
    else:
        return check[0]
    
            
# *****************************************************
#  main
# *****************************************************

# initialize
check_cfg()

# init GPIO for thermometers
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

signal.signal(signal.SIGINT, signal_handler)

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
# check configuration file

# wait for mysql server when run on boot  
# and terminate if not detected after 10 seconds  
_count = 0
while not mysql_is_running():
    _count = _count+1
    time.sleep(1)
    lcd.show("start delayed","awaiting mysqld")
    if _count > 10:
        lcd.writeline("err: No DB", 2)
        terminate("No mysql running")

        
# open/create database for logging
db_cfg = cfg['db']
log = db.NewLog(db_cfg['server'], db_cfg['name'], \
    db_cfg['user'], db_cfg['pass'], db_cfg['expire'])

# initialize event intervals
now = time.time()
timer_thermpoll = now
timer_clearlog = now
timer_blink = now
timer_lcd = now
timer_tick = now
timer_print = now
timer_checknew = now
timer_errdisp = 0

while True:
    now = time.time()

    # cleanup database
    if now > timer_clearlog:
        timer_clearlog = time.time() + DELAY_CLEARLOG
        log.clean()

    # read 
    if now > timer_checknew:
        timer_checknew = time.time() + DELAY_CHECKNEW
        sensors.create()
        
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
       timer_tick = time.time() + .2
        
    if now > timer_print:
        timer_print = time.time() + 5
        lcd.show("tmon " + __version__, "Alerts: " + str(len(get_errorlist())))
        f = open('/tmp/tmon.log','w')
        for sensor in sensors.list_:
            s = sensors.Sensor_data()
            s.address = sensor.address
            s.type = sensor.__class__.__name__
            s.name = sensor.name
            s.disabled = sensor.disabled
            s.value = sensor.value
            s.lasttime = sensor.lasttime
            s.interval = sensor.interval
            s.error = sensor.error
            print (pickle.dumps(s))
            print "-----------"
        f.close()


    # show status error messages
    #show_status()
    GPIO.output(LED_ERROR, len(get_errorlist())>0)

