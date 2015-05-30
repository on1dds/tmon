#!/usr/bin/python
#
# tmon - configuration
#
import logging
import sensors

CONTACTSTATUS = ("OPEN", "CLOSED")
STATUS_OPEN = 0
STATUS_CLOSED = 1
STATUS_DISCONNECTED = 2


#
# tmon mail settings
#
deviceid = ""  # config name of the device. Not used yet
mail_address = ""  # config sender address
mailuser = ""  # config username
mailpass = ""  # config password
smtp = ""  # config smtp servername

#
# database parameters
#
dbserver = "localhost"  # config database server address
dbname = "tmon"  # config database name
dbuser = "root"  # config database user
dbpass = "pi"  # config database password
keeplog = "10"  # config days to keep logs

notifications = []
aliases = []


class Notification:
    """Notification class"""

    def __init__(self):
        self.sensor = ""
        self.threshold = 0
        self.pinstate = STATUS_OPEN
        self.error = False
        self.mailto = ""
        self.subject = ""
        self.msgfault = ""
        self.msgrestore = ""
        self.issent = False


def getalias(address):
    for _alias in sensors.aliases:
        if _alias.address == address:
            return _alias.name
    return address


def readconfig(filename):
    global deviceid, mail_address, mailuser, mailpass, smtp
    global dbserver, dbname, dbuser, dbpass, keeplog
    global notifications

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
            elif arg[0] == "smtp": smtp = arg[1]
            elif arg[0] == "mail-address": mail_address = arg[1]
            elif arg[0] == "mailuser": mailuser = arg[1]
            elif arg[0] == "mailpass": mailpass = arg[1]

            # database configuration options
            elif arg[0] == "dbserver": dbserver = arg[1]
            elif arg[0] == "disable":  sensors.disabled_sensors.append(arg[1])
            elif arg[0] == "dbname":   dbname = arg[1]
            elif arg[0] == "dbuser":   dbuser = arg[1]
            elif arg[0] == "dbpass":   dbpass = arg[1]
            elif arg[0] == "keeplog":  keeplog = arg[1]

            # notifications
            elif arg[0] == "notify":
                # thermometer notifications configuration
                if len(arg) == 7 and arg[2] == 'above':
                    _n = Notification()
                    _n.sensor = arg[1]
                    _n.threshold = float(arg[3])
                    _n.mailto = arg[4]
                    _n.msgfault = arg[5]
                    _n.msgrestore = arg[6]
                    _n.issent = False
                    notifications.append(_n)

                # contact notifications configuration
                elif len(arg) == 6 and (arg[2] == 'closed' or arg[2] == 'open'):
                    _n = Notification()
                    _n.sensor = arg[1]
                    if arg[2] == 'closed': _n.pinstate = STATUS_CLOSED
                    elif arg[2] == 'open': _n.pinstate = STATUS_OPEN
                    _n.mailto = arg[3]
                    _n.msgfault = arg[4]
                    _n.msgrestore = arg[5]
                    _n.issent = False
                    notifications.append(_n)

                # disconnect notification configuration
                elif len(arg) == 6 and arg[2] == 'disconnected':
                    _n = Notification()
                    _n.sensor = arg[1]
                    _n.pinstate = STATUS_DISCONNECTED
                    _n.mailto = arg[3]
                    _n.msgfault = arg[4]
                    _n.msgrestore = arg[5]
                    _n.error = False
                    _n.issent = False
                    notifications.append(_n)
            else:
                logging.warning("unknown config parameter:" + arg[0])


def _parse(line):
    chars = []
    for c in line:
        chars.append(c)

    inquote = False
    for x in range(0, len(chars)):
        if chars[x] == '"' or chars[x] == '\r':
            chars[x] = '\n'
            inquote = not inquote
        if not inquote and (chars[x] == ' ' or chars[x] == '\t'):
            chars[x] = '\n'

    _lastwasn = False
    s = ""
    for x in range(0, len(chars)):
        if chars[x] != '\n':
            s += chars[x]
            _lastwasn = False
        elif chars[x] == '\n':
            if not _lastwasn:
                s += '\n'
                _lastwasn = True
    while s[len(s) - 1:] == '\n':
        s = s[:len(s) - 1]
    return s.split('\n')
