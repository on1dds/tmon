#!/usr/bin/python
#
# test 
#
import os
import sys
from twilio.rest import TwilioRestClient
import twilio
import config
import sensors
import smtplib
import logging
import re

account_sid = ""
auth_token = ""
twilio_from = ""

list_ = []


class New:
    """Notification class"""

    def __init__(self):
        self.sensor = ""
        self.threshold = 0
        self.pinstate = sensors.STATUS_OPEN
        self.error = False
        self.sendto = ""
        self.subject = ""
        self.msgfault = ""
        self.msgrestore = ""
        self.issent = False


def sendsms(_n, body):
    global account_sid, auth_token, twilio
    
    try:
        client = TwilioRestClient(account= account_sid, token= auth_token) 
        client.messages.create(
            to= _n.sendto, 
            from_= twilio_from, 
            body= config.hostname + " " + _n.sensor + " " + body,  
        )
    except twilio.rest.exceptions.TwilioRestException:
        logging.warning("number " + _n.sendto + " is not a valid, SMS capable phone number")
        return False
    
    except twilio.rest.exceptions:
        logging.warning("twilio SMS error")
        return False

    return True


def sendemail(_n, body):
    content = "From: " + config.hostname + " " + _n.sensor + "<" + config.mail_address + ">\n"
    content += "To: <" + _n.sendto + ">\n"
    content += "Subject: " + body + "\n\n"
    
    try:
        _mailserver = smtplib.SMTP(config.smtp)
        _mailserver.sendmail(config.mail_address, _n.sendto, content)
        _mailserver.quit()
        return True
    except smtplib.SMTPRecipientsRefused:
        logging.warning("invalid e-mail address")
        return False
    except smtplib.SMTPException:
        logging.warning("Unexpected error sending e-mail")
        return False

def _sendmessage(msg_,body):
    if re.match(r"[^@]+@[^@]+\.[^@]+",msg_.sendto):
        return sendemail(msg_,body)
    
    elif msg_.sendto[0] == '+' and msg_.sendto[1:].isalnum():
        return sendsms(msg_,body)

    return False
        
    

def handle():
    global list_
    # go through notification list
    for _n in list_:
        # find corresponding sensor
        _sensor = sensors.find(_n.sensor)
        if _sensor:
        
            # if it is a contact sensor
            if _sensor.type == sensors.TYPE_CONTACT:

                if str(_sensor.value) == str(_n.pinstate):
                    if not _n.issent:
                        _n.error = True
                        _n.issent = _sendmessage(_n, _n.msgfault)
                elif _n.issent:
                    _n.error = False
                    _n.issent = not _sendmessage(_n, _n.msgrestore)

            # if it is a thermometer, the temperature is above threshold and nothing is sent yet
            if (_sensor.type == sensors.TYPE_THERMOMETER) and _n.pinstate != sensors.STATUS_DISCONNECTED:
                temp = _sensor.value
                if temp >= _n.threshold:
                    if not _n.issent:
                        _n.error = True
                        _n.issent = _sendmessage(_n, _n.msgfault)

                # if temperature drops .5 degrees below threshold, send message2
                elif _n.issent and temp <= (_n.threshold - .5):
                    _n.error = False
                    _n.issent = not _sendmessage(_n, _n.msgrestore)

            # if thermometer is connected after error
            if (_sensor.type == sensors.TYPE_THERMOMETER) and _n.pinstate == sensors.STATUS_DISCONNECTED:            
                if _n.error == True:
                    _n.issent = _sendmessage(_n, _n.msgrestore)

                    if _n.issent == True:
                        _n.error = False
                        _n.issent = False
                    
        elif _n.pinstate == sensors.STATUS_DISCONNECTED:
            if _n.error == False:
                _n.error = True
                _n.issent == False
            if _n.error == True and _n.issent == False:
                _n.issent = _sendmessage(_n, _n.msgfault)
                
