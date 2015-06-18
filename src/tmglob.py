#!/usr/bin/python
#
# tmon tools
#
""" tmon constants """

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
