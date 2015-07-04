""" tmon - temperature and contact watchdog

module for notifications handling
"""
from twilio.rest import TwilioRestClient
import twilio
import sensors
import smtplib
import tlog
import lcd
import re as regex
import urllib2
from time import strftime
from globals import *


from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
import email.utils

alerts_ = []

class Alert(object):
    """ send a message whenever a predefined condition is met/restored """
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

    def send_contact_msg(self):
        """ send message when contact status causes/resets alert """
        _sensor = sensors.find(self.sensor_name)
        if _sensor.type == sensors.TYPE_CONTACT:
            if str(_sensor.value) == str(self.pinstate):
                if not self.issent:
                    self.error = True
                    self.issent = self.send_message(self.msgfault)
            elif self.issent:
                self.error = False
                self.issent = not self.send_message(self.msgrestore)   

    def send_thermometer_msg(self):
        """ send message when thermometer status causes/resets alert """
        _sensor = sensors.find(self.sensor_name)
        if _sensor.type == sensors.TYPE_THERMOMETER:
            if (self.pinstate != sensors.STATUS_FAULT):
                temp = _sensor.value
                if temp >= self.threshold:
                    if not self.issent:
                        self.error = True
                        self.issent = self.send_message(self.msgfault)

                # if temperature drops .5 degrees below threshold, send message2
                elif self.issent and temp <= (self.threshold - .5):
                    self.error = False
                    self.issent = not self.send_message(self.msgrestore)

                    # if thermometer is connected after error
            elif self.error:
                self.issent = self.send_message(self.msgrestore)
                if self.issent:
                    self.error = False
                    self.issent = False        
 
    def update(self):
        """ send message in case something is wrong """
        _sensor = sensors.find(self.sensor_name)
        if _sensor:
            self.send_contact_msg()
            self.send_thermometer_msg()

        elif self.pinstate == sensors.STATUS_FAULT:
            if self.error:
                if not self.issent:
                    self.issent = self.send_message(self.msgfault)
            else:
                self.error = True
                self.issent = False      

    def send_sms(self, body):
        """ does what it says """
        
        try:
            client = TwilioRestClient(account= cfg['twilio_account_sid'], token= cfg['twilio_auth_token']) 
            client.messages.create(
                to= self.sendto, 
                from_= cfg['twilio_number'], 
                body= cfg['hostname'] + " " + self.sensor_name + " " + body,  
            )
        except twilio.rest.exceptions.TwilioRestException:
            lcd.show(self.sendto, "not SMS capable")  
            return False
        
        except twilio.rest.exceptions:
            lcd.show("Error:","Twilio SMS fault")
            return False

        return True

    def send_email(self, body):
        """ does what it says """
        
        msg = MIMEMultipart()
        msg['From'] = email.utils.formataddr(( 
                    self.sensor_name + " " + 
                    cfg['hostname'], 
                    cfg['mail_address'] ))
        msg['To'] = "joachim.elen@telenet.be"
        msg['Subject'] = body
        msg.attach(MIMEText(body, 'plain'))

        # attach snapshot
        _addr = config_getaddress(self.sensor_name)
        _s = [s for s in cfg['sensors'] if 'address' in s and s['address'] == _addr]
        a = [a['attach'] for a in _s if 'attach' in a]
        if len(a) == 1:
            url = a[0]
            filename = strftime("%y%m%d_%H%M%S") + ".jpg"
            a = MIMEImage(urllib2.urlopen(url).read(),'jpeg')
            a.add_header('Content-Disposition', 'attachment', filename=filename)
            msg.attach(a)
        
        # try:
        _server = smtplib.SMTP(cfg['mail_server'],587)
        _server.ehlo()
        _server.starttls()
        _server.ehlo()
        _server.login(cfg['mail_user'],cfg['mail_pass'])
        _server.sendmail(cfg['mail_address'], self.sendto, msg.as_string())
        _server.close()
        return True
        # except smtplib.SMTPRecipientsRefused:
        #     lcd.show("Error in","e-mail address")
        #     # self.sendtologging.warning()
        #     return False
        # except smtplib.SMTPException:
        #     lcd.show("Unexpected error","sending e-mail")
        #     return False

    def send_message(self, body):
        """ does what it says """
        if regex.match(r"[^@]+@[^@]+\.[^@]+", self.sendto):
            return self.send_email(body)
        
        elif self.sendto[0] == '+' and self.sendto[1:].isalnum():
            return self.send_sms(body)

        return False  


def update():
    """ handle all notifications """
    # go through notification list
    for _alert in alerts_:
        # find corresponding sensor
        _alert.update()
        

def read_from_config():
    """ read config file and load into program """

    for s in cfg['sensors']:
        if 'alerts' in s:
            for alert in s['alerts']:
                if len(alert) == 4:
                    _n = Alert()
                    _n.sensor_name = config_getname(s['address'])
                    _n.sendto = alert[1]
                    _n.msgfault = alert[2]
                    _n.msgrestore = alert[3]
                    _n.issent = False
                    _n.error = False
                    
                    if alert[0][0] == '>':
                        _n.threshold = float(alert[0][1:])
                        alerts_.append(_n)

                    # contact notification configuration
                    elif alert[0] == 'closed':
                        _n.pinstate = sensors.STATUS_CLOSED
                        alerts_.append(_n)

                    elif alert[0] == 'open':
                        _n.pinstate = sensors.STATUS_OPEN
                        alerts_.append(_n)

                    elif alert[0] == 'fault':
                        _n.pinstate = sensors.STATUS_FAULT
                        alerts_.append(_n)    

