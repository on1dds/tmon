""" tmon - temperature and contact watchdog

module for notifications handling
"""
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


def send_sms(sensor, body):
    """ does what it says """

    try:
        client = TwilioRestClient(
            account= cfg['twilio_account_sid'],
            token= cfg['twilio_auth_token'])
        client.messages.create(
            to= sensor.sendto,
            from_= cfg['twilio_number'],
            body= cfg['hostname'] + " " + sensor.sensor_name + " " + body,
        )
    except twilio.rest.exceptions.TwilioRestException:
        lcd.show(sensor.sendto, "not SMS capable")
        return False

    except twilio.rest.exceptions:
        lcd.show("Error:","Twilio SMS fault")
        return False

    return True

def send_email(sensor, body):
    """ does what it says """

    msg = MIMEMultipart()
    msg['From'] = email.utils.formataddr((
                sensor.sensor_name + " " +
                cfg['hostname'],
                cfg['mail_address'] ))
    msg['To'] = "joachim.elen@telenet.be"
    msg['Subject'] = body
    msg.attach(MIMEText(body, 'plain'))

    # attach snapshot
    _addr = config_getaddress(sensor.sensor_name)
    _s = [s for s in cfg['sensors'] if 'address' in s and s['address'] == _addr]
    a = [a['attach'] for a in _s if 'attach' in a]
    if len(a) == 1:
        url = a[0]
        filename = strftime("%y%m%d_%H%M%S") + ".jpg"
        a = MIMEImage(urllib2.urlopen(url).read(),'jpeg')
        a.add_header('Content-Disposition', 'attachment', filename=filename)
        msg.attach(a)

    # try:
    _server = smtplib.SMTP(cfg['mail_server'], 587)
    _server.ehlo()
    _server.starttls()
    _server.ehlo()
    _server.login(cfg['mail_user'], cfg['mail_pass'])
    _server.sendmail(cfg['mail_address'], sensor.sendto, msg.as_string())
    _server.close()
    return True
    # except smtplib.SMTPRecipientsRefused:
    #     lcd.show("Error in","e-mail address")
    #     # self.sendtologging.warning()
    #     return False
    # except smtplib.SMTPException:
    #     lcd.show("Unexpected error","sending e-mail")
    #     return False

def send_message(sensor, body):
    """ does what it says """
    if regex.match(r"[^@]+@[^@]+\.[^@]+", sensor.sendto):
        return send_email(sensor, body)

    elif sensor.sendto[0] == '+' and sensor.sendto[1:].isalnum():
        return send_sms(sensor, body)

    return False



