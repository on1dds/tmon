#!/usr/bin/python
""" tmon - configuration loader and interpreter """
#
import logging
import sensors
import messages

#
# tmon mail settings
hostname = ""  # config name of the device. Not used yet
mail_address = ""  # config sender address
mailuser = ""  # config username
mailpass = ""  # config password
smtp = ""  # config smtp servername

#
# database parameters
#
db_server = "localhost"  # config database server address
db_name = "tmon"  # config database name
db_user = "root"  # config database user
db_pass = "pi"  # config database password
db_logexpire = "10"  # config days to keep logs

aliases = []



def readconfig(filename):
    """ read config file and load into program """
    global mail_address, mailuser, mailpass, smtp
    global db_server, db_name, db_user, db_pass, db_logexpire, hostname
    
    _cfg = open(filename, 'r')  # open the config file
    rows = _cfg.readlines()  # and read all lines
    _cfg.close()
    for line in rows:  # parse lines one by one
        arg = _parse(line)
        if arg[0] and arg[0][:1] != '#':
            # sensor aliasses
            if arg[0] == "alias" and len(arg) == 3:
                _alias = sensors.Alias()
                _alias.address = arg[1]
                _alias.name = arg[2]
                sensors.aliases.append(_alias)

            # mailing configuration options
            elif arg[0] == "hostname": hostname = arg[1]
            elif arg[0] == "smtp": smtp = arg[1]
            elif arg[0] == "mail-address": mail_address = arg[1]
            elif arg[0] == "mailuser": mailuser = arg[1]
            elif arg[0] == "mailpass": mailpass = arg[1]

            # database configuration options
            elif arg[0] == "db_server": db_server = arg[1]
            elif arg[0] == "disable":  sensors.disabled_sensors.append(arg[1])
            elif arg[0] == "db_name":   db_name = arg[1]
            elif arg[0] == "db_user":   db_user = arg[1]
            elif arg[0] == "db_pass":   db_pass = arg[1]
            elif arg[0] == "db_expire":  db_logexpire = arg[1]
            elif arg[0] == "account_sid": messages.account_sid = arg[1]
            elif arg[0] == "auth_token": messages.auth_token = arg[1]
            elif arg[0] == "twilio_from": messages.twilio_from = arg[1]

            # notifications
            elif arg[0] == "notify":
                # thermometer notifications configuration
                if len(arg) == 7 and arg[2] == 'above':
                    _n = messages.New()
                    _n.sensor_name = arg[1]
                    _n.threshold = float(arg[3])
                    _n.sendto = arg[4]
                    _n.msgfault = arg[5]
                    _n.msgrestore = arg[6]
                    _n.issent = False
                    messages.list_.append(_n)

                # contact notifications configuration
                elif len(arg) == 6 and (arg[2] == 'closed' or arg[2] == 'open'):
                    _n = messages.New()
                    _n.sensor_name = arg[1]
                    if arg[2] == 'closed': _n.pinstate = sensors.STATUS_CLOSED
                    elif arg[2] == 'open': _n.pinstate = sensors.STATUS_OPEN
                    _n.sendto = arg[3]
                    _n.msgfault = arg[4]
                    _n.msgrestore = arg[5]
                    _n.issent = False
                    messages.list_.append(_n)
                    
                # disconnect notification configuration
                elif len(arg) == 6 and arg[2] == 'disconnected':
                    _n = messages.New()
                    _n.sensor_name = arg[1]
                    _n.pinstate = sensors.STATUS_DISCONNECTED
                    _n.sendto = arg[3]
                    _n.msgfault = arg[4]
                    _n.msgrestore = arg[5]
                    _n.error = False
                    _n.issent = False
                    messages.list_.append(_n)    
            else:
                logging.warning("unknown config parameter:" + arg[0])

def _parse(line):
    """ parse config lines """
    chars = []
    for _c in line:
        chars.append(_c)

    inquote = False
    for _x in range(0, len(chars)):
        if chars[_x] == '"' or chars[_x] == '\r':
            chars[_x] = '\n'
            inquote = not inquote
        if not inquote and (chars[_x] == ' ' or chars[_x] == '\t'):
            chars[_x] = '\n'

    _lastwasn = False
    _s = ""
    for _x in range(0, len(chars)):
        if chars[_x] != '\n':
            _s += chars[_x]
            _lastwasn = False
        elif chars[_x] == '\n':
            if not _lastwasn:
                _s += '\n'
                _lastwasn = True
    while _s[len(_s) - 1:] == '\n':
        _s = _s[:len(_s) - 1]
    return _s.split('\n')
