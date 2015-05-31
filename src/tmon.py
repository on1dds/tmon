#!/usr/bin/python
#
# tmon 
#
import os
import sys
import time
import logging

import RPi.GPIO as GPIO

# import sub programs
import config
import db
import sensors
import tools
import lcd
import messages

version_ = "v1.0"

def terminate(msg):
    logging.warning(msg)
    sys.exit()


def main():
    # initialize event intervals
    #
    now = time.time()
    lcdindex = 0

    DELAY_CLEARLOG = 60 * 60 * 1
    DELAY_BLINK = 1
    # DELAY_SYSTEMP = 5
    UNSAVED_MAX = 60 * 60 * 1
    DELAY_THERMPOLL = 5
    DELAY_DISPLAY = 3
    
    wait_thermpoll = now
    wait_clearlog = now
    wait_blink = now
    wait_display = now

    okledstatus = False

    # check for IP address
    ipaddress = tools.getipaddress()
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

        """ logging """
        # clean database
        if now > wait_clearlog:
            wait_clearlog += DELAY_CLEARLOG
            log.clean(config.keeplog)
            
        # log contacts changes
        for _sensor in sensors.getlist(sensors.TYPE_CONTACT):
            if ((_sensor.lasttime + UNSAVED_MAX) < now) or (_sensor.value != _sensor.lastvalue):
                if _sensor.lastvalue != -100:
                    log.write(_sensor.type, config.getalias(_sensor.address), _sensor.lastvalue)
                _val = _sensor.value
                log.write(_sensor.type, config.getalias(_sensor.address), _val)
                _sensor.lastvalue = _val
                _sensor.lasttime = now

        # log thermometer changes
        if now > wait_thermpoll:
            wait_thermpoll += DELAY_THERMPOLL
            for _sensor in sensors.getlist(sensors.TYPE_THERMOMETER):
                # save sensors at least once every UNSAVED_MAX seconds
                if (_sensor.lasttime + UNSAVED_MAX) < now:
                    log.write(_sensor.type, config.getalias(_sensor.address), _sensor.value)
                    _sensor.lastvalue = _sensor.value
                    _sensor.lasttime = now
                else:
                    if _sensor.address == 'system':
                        if abs(_sensor.lastvalue - _sensor.value) > .3:
                            log.write(_sensor.type, config.getalias(_sensor.address), _sensor.value)
                            _sensor.lastvalue = _sensor.value
                            _sensor.lasttime = now
                    else:
                        if ((abs(_sensor.lastvalue - _sensor.value) > .9) and
                                (round(1.0 * _sensor.lastvalue, 1) != round(1.0 * _sensor.value, 1))):
                            # dit zorgt er voor dat snelle stijgingen niet worden uitgesmeerd
                            if (abs(_sensor.lastvalue - _sensor.value) > .52) and \
                                    (now - _sensor.lasttime > 60 * 5):
                                log.write(_sensor.type, config.getalias(_sensor.address), _sensor.lastvalue)
                            log.write(_sensor.type, config.getalias(_sensor.address), _sensor.value)
                            _sensor.lastvalue = _sensor.value
                            _sensor.lasttime = now


        # send notifications by e-mail or sms
        messages.handle()
        
        # blink standby LED
        if now > wait_blink:
            wait_blink += DELAY_BLINK
            GPIO.output(LED_OK, not okledstatus)
            okledstatus = not okledstatus
        
        # control error LED
        e_ = 0
        for _n in messages.list_:
            if _n.error: e_ += 1
        GPIO.output(LED_ERROR, e_ > 0)

        # show thermometers on display
        if now > wait_display:
            wait_display += DELAY_DISPLAY
            _list = sensors.getlist(sensors.TYPE_THERMOMETER)
            if lcdindex < len(_list):
                _sensor = _list[lcdindex]
                _msg = str(round(_sensor.value, 1)) + chr(223) + " " + sensors.getname(_sensor)
                lcdindex += 1
            else:
                _msg = tools.getipaddress()
                lcdindex = 0
            lcd.writeline(_msg, 2)

LED_OK = 25
LED_ERROR = 12
errorled = 0

log = db.SQLLog()

# init GPIO
os.system('modprobe w1-gpio')  # enable using filesystem for GPIO access
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# init LCD display
lcd.init()
lcd.writeline("tmon " + version_, 1)
lcd.writeline("initializing ...", 2)

# init LEDs
GPIO.setup(LED_OK, GPIO.OUT)
GPIO.setup(LED_ERROR, GPIO.OUT)
GPIO.output(LED_ERROR,True)
GPIO.output(LED_OK,True)

config.readconfig("/etc/tmon.conf")

# create sensors list and start sensors updating threads
sensors.init()

try:
    # open mysql connection
    log.open(config.dbserver, config.dbuser, config.dbpass, config.dbname)
except MySQLError:
    lcd.writeline("err: opening db", 2)
    terminate("error opening database '" + config.dbname + "from server '" + config.dbserver + "'")

time.sleep(3)

try:
    main()
except:
    pass

log.close()
GPIO.output(LED_OK, False)
GPIO.output(LED_ERROR, False)
lcd.writeline("", 1)
lcd.writeline("", 2)
GPIO.cleanup()

sys.exit(0)
