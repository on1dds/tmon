""" tmon - temperature and contact watchdog

module for notifications handling
"""
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


class New(object):
    """ Notification class """
    def __init__(self):
        self.sensor_name = ""
        self.threshold = 0
        self.pinstate = sensors.STATUS_OPEN
        self.error = False
        self.sendto = ""
        self.subject = ""
        self.msgfault = ""
        self.msgrestore = ""
        self.issent = False

        
def sendsms(_n, body):
    """ does what it says """
    
    try:
        client = TwilioRestClient(account= account_sid, token= auth_token) 
        client.messages.create(
            to= _n.sendto, 
            from_= twilio_from, 
            body= config.hostname + " " + _n.sensor_name + " " + body,  
        )
    except twilio.rest.exceptions.TwilioRestException:
        logging.warning("number " + _n.sendto + \
            " is not a valid, SMS capable phone number")
        return False
    
    except twilio.rest.exceptions:
        logging.warning("twilio SMS error")
        return False

    return True

def sendemail(_n, body):
    """ does what it says """
    content = "From: " + config.hostname + " " + _n.sensor_name + \
        "<" + config.mail_address + ">\n"
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

def _sendmessage(msg_, body):
    """ does what it says """
    if re.match(r"[^@]+@[^@]+\.[^@]+", msg_.sendto):
        return sendemail(msg_, body)
    
    elif msg_.sendto[0] == '+' and msg_.sendto[1:].isalnum():
        return sendsms(msg_, body)

    return False  

def handle():
    """ handle all notifications """
    # go through notification list
    for _n in list_:
        # find corresponding sensor
        _sensor = sensors.find(_n.sensor_name)
        if _sensor:
            handle_contact_msg(_sensor, _n)
            handle_thermometer_msg(_sensor, _n)

        elif _n.pinstate == sensors.STATUS_DISCONNECTED:
            if _n.error:
                if not _n.issent:
                    _n.issent = _sendmessage(_n, _n.msgfault)
            else:
                _n.error = True
                _n.issent = False

def handle_contact_msg(_sensor, _n):
    """ send message when contact status causes/resets alert """
    if _sensor.type == sensors.TYPE_CONTACT:
        if str(_sensor.value) == str(_n.pinstate):
            if not _n.issent:
                _n.error = True
                _n.issent = _sendmessage(_n, _n.msgfault)
        elif _n.issent:
            _n.error = False
            _n.issent = not _sendmessage(_n, _n.msgrestore)   

def handle_thermometer_msg(_sensor, _n):
    """ send message when thermometer status causes/resets alert """
    if _sensor.type == sensors.TYPE_THERMOMETER:
        if (_n.pinstate != sensors.STATUS_DISCONNECTED):
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
        elif _n.error:
            _n.issent = _sendmessage(_n, _n.msgrestore)
            if _n.issent:
                _n.error = False
                _n.issent = False

