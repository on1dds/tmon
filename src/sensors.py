#!/usr/bin/python
#
# sensors class
#
import os
import glob
import logging
import threading

import RPi.GPIO as GPIO

INTERVAL_LIST = 60
DELAY_CONTACTS = 1
DELAY_THERMOMETERS = 5

TYPE = ("CONTACT", "THERMOMETER")
TYPE_CONTACT = 'C'
TYPE_THERMOMETER = 'T'

CONTACTSTATUS = ("OPEN", "CLOSED")
STATUS_OPEN = 0
STATUS_CLOSED = 1
STATUS_DISCONNECTED = 2

CONTACT = (22, 27, 17)

list_ = []
_systemp = []
threads = []
aliases = []
disabled_sensors = []


class Sensor:
    """ sensor definition """
    def __init__(self, address):
        self.address = address
        self.type = -1
        self.enabled = True
        self.value = 0
        self.lasttime = 0.0
        self.lastvalue = -100.0


class Alias:
    """ alternative names for sensor addresses """
    def __init__(self):
        self.address = ""
        self.name = ""


def init():
    """ Initialize sensors list and keep updated """
    
    os.system('modprobe w1-gpio')
    os.system('modprobe w1-therm')

    # init GPIO ports
    GPIO.setmode(GPIO.BCM)
    for _contact in range(3):
        GPIO.setup(CONTACT[_contact], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    # clear the sensors list
    del list_[:]

    # start threads to keep list up-to-date
    thread = UpdateContacts()
    thread.name = 'UpdateContacts'
    thread.daemon = True
    thread.start()
    threads.append(thread)
    
    thread = UpdateThermometers()
    thread.name = 'UpdateThermometers'
    thread.daemon = True
    thread.start()
    threads.append(thread)
    return True


def getlist(type_):
    global list_
    _sensors = []
    for _sensor in list_:
        if _sensor.type == type_:
            _sensors.append(_sensor)
    return _sensors


def remove_(_address):
    """ remove sensor with given address from sensorlist """
    _sensor = find(_address)
    if _sensor:
        list_.remove(_sensor)
        return True
    return False

    
def isdisabled(_name):
    """ check if sensor with given name is disabled by configuration """
    global disabled_sensors

    if _name in disabled_sensors:
        return True

    for _alias in aliases:
        if _name == _alias.name or _name == _alias.address:
            if _alias.name in disabled_sensors:
                return True
            if _alias.address in disabled_sensors:
                return True
    return False

    
def getname(_sensor):
    """ find alias for """
    for s in aliases:
        if _sensor.address == s.address:
            return s.name
    return _sensor.address


def find(address): 
    """ find sensor by address or alias """
    
    # convert alias to address
    for _alias in aliases:
        if _alias.name == address:
            address = _alias.address
            break
    
    # find address
    for _sensor in list_:
        if address == _sensor.address:
            return _sensor

    return False


def terminate():
    global threads
    for thread in threads:
        thread.join()


class UpdateContacts(threading.Thread):
    """ thread for keeping contacts up-to-date"""  
    
    def __init__(self):
        import threading
        self.go = False
        threading.Thread.__init__(self)
    
    def run(self):
        import time
        global list_

        for _address in range(3):
            if not isdisabled(str(_address)):
                _s = Sensor(str(_address))
                _s.type = TYPE_CONTACT
                list_.append(_s)
                
        while True:
            for _sensor in getlist(TYPE_CONTACT):
                _sensor.value = GPIO.input(CONTACT[int(_sensor.address)])
            time.sleep(DELAY_CONTACTS)


class UpdateThermometers(threading.Thread):
    """ thread for keeping thermometers up-to-date"""
    
    def __init__(self):
        import threading
        self.go = False
        threading.Thread.__init__(self)

    def run(self):
        import time
        global list_, _systemp
        while True:
            # update connected 1-wire thermometers
            _thermometerlist = glob.glob('/sys/bus/w1/devices/' + '10*')           
            for _t in _thermometerlist:
                _address = _t[20:]             # extract thermometer address
                if not isdisabled(_address):
                    # read thermometer
                    _f = open(_t+'/w1_slave', 'r')
                    _lines = _f.readlines()
                    _f.close()
                    if _lines[0].find('YES') != -1:
                        equal_pos = _lines[1].find('t=')
                        if equal_pos != -1:
                            _value = float(_lines[1][equal_pos + 2:]) / 1000.0
                            
                            # Write thermometer data. create new sensor if none exists
                            _sensor = find(_address)
                            if _value < 80:
                                if not _sensor: 
                                    _sensor = Sensor(_address)
                                    _sensor.type = TYPE_THERMOMETER
                                    list_.append(_sensor)
                                _sensor.value = _value
                            else:
                                remove_(_address)
                        else:
                            remove_(_address)
                    else:
                        remove_(_address)
                else:
                    remove_(_address)

            # remove undetected sensors
            for i in range(len(_thermometerlist)):
                _thermometerlist[i] = _thermometerlist[i][20:]  # extract thermometer address               
            for _sensor in getlist(TYPE_THERMOMETER):
                if _sensor.address not in _thermometerlist:
                    if _sensor.address != 'system':
                        list_.remove(_sensor)
                                 
            # Update system thermometer. append if not exists
            _sensor = find('system')
            if not _sensor:
                _sensor = Sensor('system')
                _sensor.type = TYPE_THERMOMETER
                list_.append(_sensor)
                
            _f = open('/sys/class/thermal/thermal_zone0/temp', 'r')
            _lines = _f.readlines()
            _f.close()
            _val = float(_lines[0][:5]) / 1000.0
            _systemp.append(_val)
            if len(_systemp) > 20:
                _systemp.pop(0)
            _sensor.value = sum(_systemp) / len(_systemp)
            
            time.sleep(DELAY_THERMOMETERS)
            self.go = True
