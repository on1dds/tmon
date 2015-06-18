#!/usr/bin/python
""" tmon - temperature and contact watchdog 
    database access
"""
import datetime
import MySQLdb
import lcd
import sys
from warnings import filterwarnings

filterwarnings('ignore',category = MySQLdb.Warning)

class SQLLog:
    """ TMon Log SQL Connector"""

    def __init__(self):
        self.cursor = None
        self.db = None
        self.cursor = None
        
    def create_db(self, db_server, db_user, db_pass):
        """ open database """
    
        try:
            self.db = MySQLdb.connect(db_server, db_user, db_pass)
            cursor = self.db.cursor() 
        except MySQLdb.Warning, e:
            lcd.writeline("DB open warning",1)
            lcd.writeline("OK",2)
        except MySQLdb.Error, e:
            lcd.writeline("DB open failed:",1)
            lcd.writeline("TMON Stopped",2)            
            sys.exit(1)


        try:
            cursor.execute("CREATE DATABASE IF NOT EXISTS tmon")
            cursor.execute("USE tmon");
        except MySQLdb.Warning, e:
            lcd.writeline("DB create warn",1)
            lcd.writeline("OK",2)

        except MySQLdb.Error, e:
            lcd.writeline("DB create fault:",1)
            lcd.writeline("Failed",2)  
            self.db.rollback()
            self.db.close()
            sys.exit(1)


        try:
            # try creating log table
            cursor.execute((
                "CREATE TABLE IF NOT EXISTS log(" 
                "id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,"
                "timestamp DATETIME,"
                "type CHAR(1),"
                "sensor VARCHAR(20),"
                "value DECIMAL(4,1)"
                ") "))        
        except MySQLdb.Warning, e:
            lcd.writeline("DB create table",1)
            lcd.writeline("OK",2)
                
        except MySQLdb.Error, e:
            lcd.writeline("DB new table",1)
            lcd.writeline("Failed: Stopped",2)
            self.db.rollback()
            self.db.close()
            sys.exit(1)       

    def open(self, db_server, db_user, db_pass, db_name):
        """ open database """
        try:
            self.db = MySQLdb.connect(db_server, db_user, db_pass, db_name)
            return True
        except MySQLdb.Error:
            return False

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
        query = "DELETE FROM log WHERE timestamp < (NOW() - INTERVAL " + \
            period + " day)"
        cursor = self.db.cursor()
        cursor.execute(query)
        self.db.commit()
