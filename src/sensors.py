""" sensors administration

find, inventorize, read and update sensors by type
"""
import os
import sys
import glob
from globals import *
import messaging
import time
import threading
import RPi.GPIO as GPIO

list_ = []

# *****************************************************
#  classes
# *****************************************************

class Sensor(threading.Thread):
    """ define sensor base class """

    def __init__(self, address):
        # run the parent thread init
        super(Sensor,self).__init__()

        # set default configuration
        self.address = address
        self.name = address

        self.daemon = True
        self.disabled = False
        self.value = False
        self.lastvalue = False
        self.lasttime = time.time()
        self.interval = 5
        self.lastvalue = False
        self.alerts = []
        self.error = False
        
    def run(self):
        """ update sensor values and trigger alerts """
        if not self.disabled:
            self.lasttime = time.time()
            print self.name

    def handle_alerts(self):
        """ run through and trigger all alerts """
        if not self.disabled:
            for alert in self.alerts:
                alert.handle()

    def __str__(self):
        return "%s: %s" % (self.name, self.value)

class Contact(Sensor):
    """ sensor for opening doors and push buttons """
    # set contact constants
    GPIO = (22, 27, 17)
    STATUS_OPEN = 0
    STATUS_CLOSED = 1
    STATUS_FAULT = 2
    STATUS = ("OPEN", "CLOSED", "FAULT")

    def __init__(self, address, gpiopin):
        super(Contact, self).__init__(address)

        # set hardware
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(gpiopin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        self.attach = None
        self.gpiopin = gpiopin
        self.interval = 0.5
        self.value = self.read()
        self.lastvalue = self.value

    def run(self):
        while True:
            if not self.disabled:
                # sys.stdout.write("S")
                self.value = self.read()
                super(Contact, self).handle_alerts()
                time.sleep(self.interval)
            else:
                time.sleep(100000)

    def read(self):
        return GPIO.input(self.gpiopin)

    def __str__(self):
        return "%s: %s" % (self.name, self.STATUS[self.value])

class Thermometer(Sensor):
    """ sensor for measuring temperature """
    SYSTEM_SENSOR = 'system'

    def __init__(self, address):
        super(Thermometer, self).__init__(address)
        self.interval = 5
        self.buffer = []
        self.buffersize =  1
        self.resolution = 0.5
        self.errorcount = 0

    def run(self):
        while True:
            if not self.disabled:
                # sys.stdout.write("T")
                self.value = self.read()
                super(Thermometer, self).handle_alerts()
                time.sleep(self.interval)
            else:
                time.sleep(100000)

    def read(self):
        """ read attached or on-board thermometer """
        _temperature = False
        if self.address == Thermometer.SYSTEM_SENSOR:
             # read the cpu temperature from system
            _f = open('/sys/class/thermal/thermal_zone0/temp', 'r')
            _lines = _f.readlines()
            _f.close()
            _temperature = float(_lines[0][:5]) / 1000.0
        else:
            # read w1 temperature from system
            _temperature = False
            _tfile = glob.glob('/sys/bus/w1/devices/' + self.address + '/w1_slave' )
            if len(_tfile) == 1:
                _f = open(_tfile[0], 'r')
                _lines = _f.readlines()
                _f.close()

                # CRC has to be correct
                if _lines[0].find('YES') > -1:
                    # temperature format has to be valid
                    temp_pos = _lines[1].find('t=')
                    if temp_pos != -1:
                        _value = float(_lines[1][temp_pos + 2:]) / 1000.0
                        if _value < 80:
                            _temperature = _value

        # set error when no temperature value
        self.error = _temperature == 0
        if self.error:
            return False

        # calculate average temperature from buffer
        self.buffer.append(_temperature)
        if len(self.buffer) > self.buffersize:
            self.buffer.pop(0)
        return sum(self.buffer) / len(self.buffer)

    def __str__(self):
        return "%s: %0.2f" % (self.name, self.value)
        
class Alert(object):
    """ send a message whenever a predefined condition is met/restored """

    # alert properties
    sensor = None
    triggerpoint = False
    triggered = False
    notified = False
    hysteresis = .5

    sendto = ""
    subject = ""
    msg_trigger = ""
    msg_restore = ""

    def __init__(self, parent, sendto, msg_trigger, msg_restore):
        self.sensor = parent
        self.sendto = sendto
        self.msg_trigger = msg_trigger
        self.msg_restore = msg_restore

    def handle(self):
        """ send message in case something is wrong """
        value = self.sensor.value
        if value >= self.triggerpoint:
            self.triggered = True
            if not self.notified:
                # print self.sensor, ":", self.sendto, self.msg_trigger
                self.notified = True
        elif self.triggered and value <= (self.triggerpoint - self.hysteresis):
            if self.notified:
                # print self.sensor, ":", self.sendto, self.msg_restore
                self.notified = False
            if not self.notified:
                self.triggered = False

# *****************************************************
#  functions
# *****************************************************

def cfg_to_sensor(sensor, conf):
    """ read given sensor configuration into sensor """
    if 'name' in conf: 
        sensor.name = conf['name'] 
    if 'disable' in conf: 
        sensor.disabled = conf['disable'] 
    if 'interval' in conf: 
        sensor.interval = conf['interval'] 

def cfg_to_contact(contact, conf):
    """ read given contact configuration into contact """
    cfg_to_sensor(contact, conf)
    if 'attach' in conf:
        contact.attach = conf['attach'] 
    if 'alerts' in conf:
        contact.alerts = []
        for _cfg in conf['alerts']:
            if len(_cfg) == 4:
                _alert = Alert(contact, _cfg[1], _cfg[2], _cfg[3])
                if _cfg[0] == 'closed':
                    _alert.triggerpoint = Contact.STATUS_CLOSED
                    contact.alerts.append(_alert)
                elif _cfg[0] == 'open':
                    _alert.triggerpoint = Contact.STATUS_OPEN
                    contact.alerts.append(_alert)

def cfg_to_thermometer(thermometer, conf):
    """ read given thermometer configuration into thermometer """
    cfg_to_sensor(thermometer, conf)

    if 'buffer' in conf:
        thermometer.buffersize = conf['buffer'] 
    if 'precision' in conf:
        thermometer.precision = conf['precision'] 
    if 'buffer' in conf:
        thermometer.buffersize = conf['buffer'] 
    if 'resolution' in conf:
        thermometer.resolution = conf['resolution'] 
    if 'alerts' in conf:
        thermometer.alerts = []
        for _cfg in conf['alerts']:
            if len(_cfg) == 4:
                _alert = Alert(thermometer, _cfg[1], _cfg[2], _cfg[3])
                if _cfg[0][0] == '>':
                    _alert.triggerpoint = float(_cfg[0][1:])
                    thermometer.alerts.append(_alert)
                elif _cfg[0] == 'fault':
                    _alert.triggerpoint = Contact.STATUS_FAULT
                    thermometer.alerts.append(_alert)

def create():
    """ Initialize sensors list and keep updated """

    # get list of configured thermometers
    thermometers_config = [_s for _s in cfg['sensors']
        if 'thermometer' in _s]
    for t_cfg in thermometers_config:
        t = Thermometer(t_cfg['thermometer'])
        cfg_to_thermometer(t, t_cfg)
        t.start()
        list_.append(t)

    # get list of configured contacts
    contacts_config = [_s for _s in cfg['sensors'] if 'contact' in _s]
    for c_cfg in contacts_config:
        pin = int(c_cfg['contact'])
        if 0 <= pin < 3:
            c = Contact(c_cfg['contact'], Contact.GPIO[pin])
            cfg_to_contact(c, c_cfg)
            c.start()
            list_.append(c)

    # get list of detected w1 thermometers
    t_list = glob.glob('/sys/bus/w1/devices/' + '10*')
    for i in range(len(t_list)):
        t_list[i] = t_list[i][20:]

    # start unconfigured w1 thermometers
    for t_id in t_list:
        if not get(t_id):
            t = Thermometer(t_id)
            t.start()
            list_.append(t)

def getlist(_type):
    """ collect list of all sensors of givent type """
    _sensors = []
    for _sensor in list_:
        if _sensor.__class__.__name__ == _type:
            _sensors.append(_sensor)
    return _sensors

def get(_address):
    """ find sensor by address or alias """
    # find by address
    for _sensor in list_:
        if _address == _sensor.address:
            return _sensor

    # find by name
    for _sensor in list_:
        if _address == _sensor.name:
            return _sensor

    # not found
    return False



