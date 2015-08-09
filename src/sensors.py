""" sensors administration

find, inventorize, read and update sensors by type
"""
import sys
import glob
from globals import *
import time
import threading
import RPi.GPIO as GPIO

from twilio.rest import TwilioRestClient
import twilio
import smtplib
import lcd
import re as regex
import urllib2
from time import strftime

from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
import email.utils

list_ = []

# *****************************************************
#  classes
# *****************************************************

class Sensor_data():
    # set default configuration.address = address
    address = ""
    type = ""
    name = address
    disabled = False
    value = False
    lasttime = time.time()
    interval = 5
    error = False

class Sensor(threading.Thread):
    """ define sensor base class """
    hostname = 'tmon'
    exitapp = False

    def __init__(self, address):
        super(Sensor, self).__init__()
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
        # run the parent thread init

    def run(self):
        """ update sensor values and trigger alerts """
        if not self.disabled:
            self.lasttime = time.time()
            #print self.name

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

    STATUS = ("OPEN", "CLOSED", "FAULT")

    def __init__(self, address, gpiopin, config= None):
        super(Contact, self).__init__(address)
        # set hardware
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(gpiopin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        self.attach = None
        self.gpiopin = gpiopin
        self.interval = 0.5
        self.value = self.read()
        self.lastvalue = self.value
        cfg_to_contact(self, config)
        list_.append(self)
        self.start()

    def run(self):
        while True:
            if self.exitapp:
                break
            if not self.disabled and \
                time.time() > self.lasttime + self.interval:
                self.lasttime = time.time()
                # sys.stdout.write("C")
                self.value = self.read()
                super(Contact, self).handle_alerts()
            else:
                time.sleep(.1)

    def read(self):
        """ get current value from hardware """
        return GPIO.input(self.gpiopin)

    def __str__(self):
        return "%s: %s" % (self.name, self.STATUS[self.value])

class Thermometer(Sensor):
    """ sensor for measuring temperature """
    SYSTEM_SENSOR = 'system'
    STATUS_FAULT = -100

    def __init__(self, address, config= None):
        super(Thermometer, self).__init__(address)
        self.interval = 5
        self.buffer = []
        self.buffersize =  1
        self.resolution = 0.5
        self.errorcount = 0
        self.value = self.read()
        self.lastvalue = self.value
        cfg_to_thermometer(self, config)
        list_.append(self)
        self.start()

    def run(self):
        while True:
            if self.exitapp:
                break
            if not self.disabled and \
                time.time() > self.lasttime + self.interval:
                self.lasttime = time.time()
                # sys.stdout.write("T")
                self.value = self.read()
                super(Thermometer, self).handle_alerts()
            else:
                time.sleep(1)

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
            _tfile = glob.glob('/sys/bus/w1/devices/' + \
                self.address + '/w1_slave' )
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
                        if _value < 85:
                            _temperature = _value
                        else:
                            _temperature = False

        # set error when no temperature value
        self.error = _temperature == False
        if self.error:
            self.value = False
            return False

        # calculate average temperature from buffer

        self.buffer.append(_temperature)
        if len(self.buffer) > self.buffersize:
            self.buffer.pop(0)
        return sum(self.buffer) / len(self.buffer)

    def __str__(self):
        if self.value:
            return "%s: %0.2f" % (self.name, self.value)
        else:
            return "%s: Error" % (self.name)

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

        if self.sensor.__class__.__name__ == 'Contact':
            value = self.sensor.value
            if value == self.triggerpoint:
                self.triggered = True
                if not self.notified:
                    send_alert(self, self.msg_trigger)
                    # print self.sensor, ":", self.sendto, self.msg_trigger
                    self.notified = True
            elif self.notified:
                self.triggered = False
                send_alert(self, self.msg_restore)
                # print self.sensor, ":", self.sendto, self.msg_restore
                self.notified = False

        elif self.sensor.__class__.__name__ == 'Thermometer':
            value = self.sensor.value
            if value:
                if value >= self.triggerpoint:
                    self.triggered = True
                    if not self.notified:
                        send_alert(self, self.msg_trigger)
                        # print self.sensor, ":", self.sendto, self.msg_trigger
                        self.notified = True
                elif self.notified and value <= (self.triggerpoint - .5):
                    self.triggered = False
                    send_alert(self, self.msg_restore)
                    # print self.sensor, ":", self.sendto, self.msg_restore
                    self.notified = False
            else:
                pass

# *****************************************************
#  functions to send messages
# *****************************************************
def send_sms(to, message):
    """ does what it says """
    twilio = cfg['twilio']
    if DEBUG:
        print("ERROR: " + to + ":"+message)
        return True
        
    try:
        account = twilio['account_sid']
        token= twilio['auth_token']
        client = TwilioRestClient(account,token)
        
        client.messages.create(
            to= to, 
            from_= twilio['number'], body= message)
    except twilio.rest.exceptions.TwilioRestException:
        lcd.show(to, "not SMS capable")
        return False

    except twilio.rest.exceptions:
        lcd.show("Error:","Twilio SMS fault")
        return False

    return True

def send_email(alert, message):
    #print("email verzenden")
    
    mail = cfg['mail']
    host_ = cfg['hostname']
    from_ = mail['address']
    name_ = alert.sensor.name
    smtp_ = mail['server']
    login_ = mail['user']
    pass_ = mail['pass']
    port_ = mail['port']

    # attach subject
    msg = MIMEMultipart()
    msg['From'] = email.utils.formataddr((name_ + "@" + host_, from_ ))
    msg['To'] = alert.sendto
    msg['Subject'] = message
    # msg.attach(MIMEText(message, 'plain'))

    # attach snapshot
    if hasattr(alert.sensor,'attach') and alert.sensor.attach:
    # if alert.sensor.attach:
        url = alert.sensor.attach
        filename = strftime("%y%m%d_%H%M%S") + ".jpg"
        a = MIMEImage(urllib2.urlopen(url).read(),'jpeg')
        a.add_header('Content-Disposition', 'attachment', filename=filename)
        msg.attach(a)

    # try:
    _server = smtplib.SMTP(smtp_, port_)
    _server.ehlo()
    _server.starttls()
    _server.ehlo()
    _server.login(login_, pass_)
    _server.sendmail(from_, alert.sendto, msg.as_string())
    _server.close()
    return True

def send_alert(alert, message):
    """ does what it says """
    to = alert.sendto
 
    # print "I should send a message here,", alert, message

    if regex.match(r"[^@]+@[^@]+\.[^@]+", to):
        return send_email(alert, message)

    elif to[0] == '+' and to[1:].isalnum():
        message = alert.sensor.name + ":" + message
        return send_sms(to, message)
    return True


# *****************************************************
#  functions to read sensors config
# *****************************************************

def cfg_to_sensor(sensor, conf):
    """ read given sensor configuration into sensor """
    if conf:
        if 'name' in conf:
            sensor.name = conf['name']
        if 'disable' in conf:
            sensor.disabled = conf['disable']
        if 'interval' in conf:
            sensor.interval = conf['interval']

def cfg_to_contact(contact, conf):
    """ read given contact configuration into contact """
    if conf:
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
    if conf:
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
                        _alert.triggerpoint = Thermometer.STATUS_FAULT
                        thermometer.alerts.append(_alert)

# *****************************************************
#  functions to create and find sensors in list
# *****************************************************

def create():
    """ Initialize sensors list and keep updated """
    if 'hostname' in cfg:
        Sensor.hostname = cfg['hostname']

    # get list of configured thermometers
    thermometers_config = [_s for _s in cfg['sensors']
        if 'thermometer' in _s]
    for config in thermometers_config:
        if not get(config['thermometer']):
            Thermometer(config['thermometer'], config)

    # get list of configured contacts
    contacts_config = [_s for _s in cfg['sensors'] if 'contact' in _s]
    for config in contacts_config:
        if not get(config['contact']):
            pin = int(config['contact'])
            if 0 <= pin < 3:
                Contact(config['contact'], Contact.GPIO[pin], config)

    # get list of detected w1 thermometers
    t_list = glob.glob('/sys/bus/w1/devices/' + '10*')
    for address in t_list:
        if not get(address[20:]):
            Thermometer(address[20:])

def getlist(_type):
    """ collect list of all sensors of givent type """
    sensors = []
    for sensor in list_:
        if sensor.__class__.__name__ == _type:
            sensors.append(sensor)
    return sensors

def get(address):
    """ find sensor by address or alias """
    # find by address
    for sensor in list_:
        if address == sensor.address:
            return sensor

    # find by name
    for sensor in list_:
        if address == sensor.name:
            return sensor

    # not found
    return False



