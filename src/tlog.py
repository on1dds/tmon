#!/usr/bin/python
""" tmon - temperature and contact watchdog 
    database access
"""
import datetime
import MySQLdb
import lcd
import sys
from globals import *

# disable warnings from MySQLdb to console
from warnings import filterwarnings
filterwarnings('ignore', category = MySQLdb.Warning)

class NewLog:
    """ TMon Log SQL Connector"""

    def __init__(self, db_server, db_user, db_pass):
        self.cursor = None
        self.db = None
        self.cursor = None

        # create database object
        try:
            self.db = MySQLdb.connect(db_server, db_user, db_pass)
            self.cursor = self.db.cursor() 
        except MySQLdb.Warning as e:
            lcd.show("DB open warning", "OK")
        except MySQLdb.Error as e:
            lcd.show("DB open failed:", "TMON Stopped")              
            sys.exit(1)

        # create database
        try:
            self.cursor.execute("CREATE DATABASE IF NOT EXISTS tmon")
            self.cursor.execute("USE tmon")
        except MySQLdb.Warning as e:
            lcd.show("DB create warn", "OK")
        except MySQLdb.Error as e:
            lcd.show("DB create fault:", "Failed")  
            self.db.rollback()
            self.db.close()
            sys.exit(1)

        # create log table
        try:
            self.cursor.execute((
                "CREATE TABLE IF NOT EXISTS log(" 
                "id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                "timestamp DATETIME,"
                "type CHAR(1),"
                "sensor VARCHAR(20),"
                "value DECIMAL(4,1)"
                ") "))        
        except MySQLdb.Warning as e:
            lcd.show("DB create table", "OK")              
        except MySQLdb.Error as e:
            lcd.show("DB new table", "Failed: Stopped")
            self.db.rollback()
            self.db.close()
            sys.exit(1)       

    def close(self):
        """ close database """
        self.db.close()

    def write(self, sensortype, name, value):
        """ log sensor information to database """
        now = datetime.datetime.now()
        query = "INSERT INTO log (timestamp, type, sensor, value) "
        query += "VALUES ('" + now.strftime("%Y-%m-%d %H:%M:%S") + "'"
        query += ", '" + sensortype + "'"
        query += ", '" + name + "'"
        query += ", " + str(round(1.0 * value, 1)) + ")"
        cursor = self.db.cursor()
        cursor.execute(query)
        self.db.commit()

    def clean(self, period):
        """ clean up old logs """
        period = str(period)
        query = "DELETE FROM log WHERE timestamp < (NOW() - INTERVAL " + \
            period + " day)"
        cursor = self.db.cursor()
        cursor.execute(query)
        self.db.commit()

    def contacts(self, sensor, now):
        """ log contact status changes to database """
        _s = sensor
        if ((_s.lasttime + UNSAVED_MAX) < now) or \
            (_s.value != _s.lastvalue):
            if _s.lastvalue != -100:
                self.write(_s.type, \
                    config_getname(_s.address), \
                    _s.lastvalue)
            _val = _s.value
            self.write(_s.type, config_getname(_s.address), _val)
            _s.lastvalue = _val
            _s.lasttime = now


    def temp_changes(self, sensor, now):
        """ write temperature changes to database """
        _s = sensor
        # save all temperatures at least once every UNSAVED_MAX seconds
        if (_s.lasttime + UNSAVED_MAX) < now:
            self.write(_s.type, config_getname(_s.address), _s.value)
            _s.lastvalue = _s.value
            _s.lasttime = now
            
        # handle system thermometer
        elif _s.address == 'system':
            if abs(_s.lastvalue - _s.value) > .3:
                self.write(_s.type, config_getname(_s.address), _s.value)
                _s.lastvalue = _s.value
                _s.lasttime = now
                
        # handle w1 thermometers
        elif ((abs(_s.lastvalue - _s.value) > .9) and
                (round(_s.lastvalue, 1) != round(_s.value, 1))):
            if (abs(_s.lastvalue - _s.value) > .52) and \
                    (now - _s.lasttime > 60 * 5):
                self.write(_s.type, \
                    config_getname(_s.address), \
                    _s.lastvalue)
            self.write(_s.type, \
                config_getname(_s.address), \
                _s.value)
            _s.lastvalue = _s.value
            _s.lasttime = now

        

        
        