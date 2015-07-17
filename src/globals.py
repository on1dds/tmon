#!/usr/bin/python
#
# tmon tools
#
""" tmon - temperature and contact watchdog
module for setting global variables and functions
"""
DELAY_CLEARLOG = 60 * 60 * 1
DELAY_BLINK = 1
# DELAY_SYSTEMP = 5
UNSAVED_MAX = 60 * 60 * 1
DELAY_THERMPOLL = 5
DELAY_DISPLAY = 3
DELAY_ERRDISP = 5


LED_OK = 25
LED_ERROR = 12
BTN_INFO =  10
# BTN_DOWN = 9

cfg = {}
execfile("/etc/tmon/tmonconf.py", cfg)


def getipaddress():
    """ does what it says """
    import subprocess
    arg = 'ip route list'
    try:
        p_ = subprocess.Popen(arg, shell=True, stdout=subprocess.PIPE)
        data = p_.communicate()
        split_data = data[0].split()
        return split_data[split_data.index('src') + 1]
    except OSError:
        return False


def terminate(msg):
    """ exit this software """
    import logging
    import sys
    logging.warning(msg)
    sys.exit()

def get_sensor_config(_name_):
    """ get sensor from configuration """
    _s = [_s for _s in cfg['sensors'] \
        if 'address' in _s and _s['address'] == _name_]
    if len(_s) == 1:
        return _s[0]
    _s = [_s for _s in cfg['sensors'] if 'name' in _s and _s['name'] == _name_]
    if len(_s) == 1:
        return _s[0]
    return False

def config_getdisabled():
    """ get disabled sensors from configuration """
    return [s['address'] \
        for s in cfg['sensors'] \
            if 'disable' in s and s['disable'] == True]

def config_sensor_get(_name_, _attrib):
    """ get attribute variable from sensor in config """
    _s = get_sensor_config(_name_)
    if _attrib in _s:
        return _s[_attrib]
    return False

def cfg_get_list_by_attrib(_attrib):
    """ get list of all sensors containing the given attribute """
    _sensor = [_s for _s in cfg['sensors'] if _attrib in _s]

def config_getname(_address_):
    """ get name (alias) for sensor address """
    _s = [s['name'] \
        for s in cfg['sensors'] \
            if 'name' in s and 'address' in s and s['address'] == _address_]
    if len(_s) == 1:
        return _s[0]
    return _address_

def config_getaddress(_name_):
    """ get sensor address from name """
    _s = [s['address'] \
        for s in cfg['sensors'] \
            if 'name' in s and 'address' in s and s['name'] == _name_]
    if len(_s) == 1:
        return _s[0]
    return _name_
