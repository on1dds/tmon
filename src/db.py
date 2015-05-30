#!/usr/bin/python

import datetime
import MySQLdb
import sensors


class SQLLog:
    """TMon Log SQL Connector"""

    def __init__(self):
        self.db = None

    def open(self, dbserver, dbuser, dbpass, dbname):
        try:
            self.db = MySQLdb.connect(dbserver, dbuser, dbpass, dbname)
            return True
        except MySQLdb.Error:
            return False

    def close(self):
        self.db.close()

    def write(self, sensortype, name, value):
        v = round(1.0 * value, 1)
        now = datetime.datetime.now()
        query = "INSERT INTO log (timestamp, type, sensor, value) "
        query += "VALUES ('" + now.strftime("%Y-%m-%d %H:%M:%S") + "'"
        query += ", '" + sensortype + "'"
        query += ", '" + name + "'"
        query += ", " + str(v) + ")"
        cursor = self.db.cursor()
        cursor.execute(query)
        self.db.commit()

    def clean(self, period):
        query = "DELETE FROM log WHERE timestamp < (NOW() - INTERVAL " + period + " day)"
        cursor = self.db.cursor()
        cursor.execute(query)
        self.db.commit()
