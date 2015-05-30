#!/usr/bin/python
#
# tmon - tools library
#
import subprocess
import config
import sensors
import smtplib
import logging

def getipaddress():
    arg = 'ip route list'
    try:
        p = subprocess.Popen(arg, shell=True, stdout=subprocess.PIPE)
        data = p.communicate()
        split_data = data[0].split()
        return split_data[split_data.index('src') + 1]
    except OSError:
        return False


def sendemail(notification, body):
    msg = "From: <" + config.mail_address + ">\n"
    msg += "To: <" + notification.mailto + ">\n"
    msg += "Subject: " + body + "\n\n"
    # msg += body
    try:
        _mailserver = smtplib.SMTP(config.smtp)
        _mailserver.sendmail(config.mail_address, notification.mailto, msg)
        _mailserver.quit()
        return True
    except smtplib.SMTPException:
        logging.warning("Unexpected error sending e-mail")
        return False


def sendnotifications():
    # go through notification list
    for _n in config.notifications:
        # find corresponding sensor
        _sensor = sensors.find(_n.sensor)
        if _sensor:
        
            # if it is a contact sensor
            if _sensor.type == sensors.TYPE_CONTACT:

                if str(_sensor.value) == str(_n.pinstate):
                    if not _n.issent:
                        _n.error = True
                        _n.issent = sendemail(_n, _n.msgfault)
                elif _n.issent:
                    _n.error = False
                    _n.issent = not sendemail(_n, _n.msgrestore)

            # if it is a thermometer, the temperature is above threshold and nothing is sent yet
            if (_sensor.type == sensors.TYPE_THERMOMETER) and _n.pinstate != config.STATUS_DISCONNECTED:
                temp = _sensor.value
                if temp >= _n.threshold:
                    if not _n.issent:
                        _n.error = True
                        _n.issent = sendemail(_n, _n.msgfault)

                # if temperature drops .5 degrees below threshold, send message2
                elif _n.issent and temp <= (_n.threshold - .5):
                    _n.error = False
                    _n.issent = not sendemail(_n, _n.msgrestore)

            # if thermometer is connected after error
            if (_sensor.type == sensors.TYPE_THERMOMETER) and _n.pinstate == config.STATUS_DISCONNECTED:            
                if _n.error == True:
                    _n.issent = sendemail(_n, _n.msgrestore)

                    if _n.issent == True:
                        _n.error = False
                        _n.issent = False
                    
        elif _n.pinstate == config.STATUS_DISCONNECTED:
            if _n.error == False:
                _n.error = True
                _n.issent == False
            if _n.error == True and _n.issent == False:
                _n.issent = sendemail(_n, _n.msgfault)
                

                
                
              





