""" sensors administration

find, inventorize, read and update sensors by type
"""
import os
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
        self.disabled = False
        self.value = False
        self.lastvalue = False
        self.lasttime = time.time()
        self.interval = 5
        self.lastvalue = False
        self.alerts = []
        self.error = False

        # load custom configuration
        sensor_config = get_sensor_config(self.address)

        if sensor_config:
            if 'name' in sensor_config:
                self.name = sensor_config['name']
            if 'disable' in sensor_config:
                self.disabled = sensor_config['disable']
            if 'interval' in sensor_config:
                self.interval = sensor_config['interval']
            if 'buffer' in sensor_config:
                self.buffersize = sensor_config['buffer']
            if 'precision' in sensor_config:
                self.precision = sensor_config['precision']

            if 'alerts' in sensor_config:
                self.alerts = []
                for _cfg in sensor_config['alerts']:
                    if len(_cfg) == 4:
                        _alert = Alert(self)
                        _alert.sendto = _cfg[1]
                        _alert.msg_trigger = _cfg[2]
                        _alert.msg_restore = _cfg[3]

                        if _cfg[0][0] == '>':
                            _alert.triggerpoint = float(_cfg[0][1:])
                            self.alerts.append(_alert)

                        elif _cfg[0] == 'closed':
                            _alert.triggerpoint = Contact.STATUS_CLOSED
                            self.alerts.append(_alert)

                        elif _cfg[0] == 'open':
                            _alert.triggerpoint = Contact.STATUS_OPEN
                            self.alerts.append(_alert)

                        elif _cfg[0] == 'fault':
                            _alert.triggerpoint = Contact.STATUS_FAULT
                            self.alerts.append(_alert)

    def run(self):
        """ update sensor values and trigger alerts """
        self.lasttime = time.time()

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
    CONTACT = (22, 27, 17)
    STATUS_OPEN = 0
    STATUS_CLOSED = 1
    STATUS_FAULT = 2
    STATUS = ("OPEN", "CLOSED", "FAULT")

    def __init__(self, address):
        super(Contact, self).__init__(address)
        self.interval = 0.5
        self.value = self.read()

    def run(self):
        while True:
            self.value = self.read()
            super(Contact, self).handle_alerts()
            time.sleep(self.interval)

    def read(self):
        return GPIO.input(Contact.CONTACT[int(self.address)])

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

        self.lastvalue = self.value

        sensor_config = get_sensor_config(self.address)
        if sensor_config:
            if 'buffer' in sensor_config:
                self.buffersize = sensor_config['buffer']
            if 'resolution' in sensor_config:
                self.resolution = sensor_config['resolution']
        self.value = self.read()

    def run(self):
        while True:
            self.value = self.read()
            super(Thermometer, self).handle_alerts()
            time.sleep(self.interval)

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

class Alert(object):
    """ send a message whenever a predefined condition is met/restored """
    def __init__(self, parent):
        self.sensor = parent
        self.triggerpoint = False
        self.triggered = False
        self.notified = False
        self.hysteresis = .5

        self.sendto = ""
        self.subject = ""
        self.msg_trigger = ""
        self.msg_restore = ""

    def handle(self):
        """ send message in case something is wrong """
        value = self.sensor.value
        if value >= self.triggerpoint:
            self.triggered = True
            if not self.notified:
                print self.sensor, ":", self.sendto, self.msg_trigger
                self.notified = True
        elif self.triggered and value <= (self.triggerpoint - self.hysteresis):
            if self.notified:
                print self.sensor, ":", self.sendto, self.msg_restore
                self.notified = False
            if not self.notified:
                self.triggered = False

# *****************************************************
#  functions
# *****************************************************

def create():
    """ Initialize sensors list and keep updated """

    # init GPIO for thermometers
    os.system('modprobe w1-gpio')
    os.system('modprobe w1-therm')

    # init GPIO for contacts
    GPIO.setmode(GPIO.BCM)
    for _switch in range(3):
        GPIO.setup(Contact.CONTACT[_switch], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    # create non-existing contacts
    for _address in range(3):
        sensor = get(str(_address))
        if not sensor:
            # start threads to keep list up-to-date
            thread = Contact(str(_address))
            thread.daemon = True
            thread.start()
            list_.append(thread)

    # get list of thermometers
    _thermometerlist = glob.glob('/sys/bus/w1/devices/' + '10*')
    for i in range(len(_thermometerlist)):
        _thermometerlist[i] = _thermometerlist[i][20:]
    _thermometerlist.append(Thermometer.SYSTEM_SENSOR)

    # create non-existing thermometer
    for _address in _thermometerlist:
        sensor = get(str(_address))
        if not sensor:
            # start threads to keep list up-to-date
            thread = Thermometer(_address)
            thread.daemon = True
            thread.start()
            list_.append(thread)

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



