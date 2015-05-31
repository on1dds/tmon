## tmon##
tmon implements a Raspberry Pi based watchdog for temperature logging and intrusion detection in a dataroom and has the following features: 
- Multiple Dallas DS18S20 type thermometers support. These thermometers can be plugged in and removed on the fly
- System temperature monitoring
- Sensor address aliasing for user friendly operation
- Three door contact sensors
- Configuration using /etc/tmon.conf config file
- Threaded sensor reading for quick response
- Notifications can be sent by mail and SMS using Twilio account
- Send notification (alert) when sensor is triggers by threshold temperatures
- Send another notification when sensor values are restored
- Send another notification when a sensor is removed from the RPi
- Each notification can be sent to another addressee
- notifications can be double, tripled, ...
- Error conditons are shown by an indicator LED
- Blinking LED to show tmon is still running
- Can be used headless because of 2x16 LCD display which displays IP-address (helpfull in case of DHCP)
- temperature monitoring via 2x16 LCD display
- sensor logging in MySQL database on the Pi
- Log can be viewed via webpage
- sensor data graphics shown on webpage using PHP

## Development##
- Developed on a Raspberry Pi Model B+ v1.2.
- you can build it on a breadboard
- OS used during development: Headless [Minibian 2015-02-18](https://minibianpi.wordpress.com/)
- Programming on Windows in Notepad++
- Uploaded files using samba
- Written for Python 2.7.3.

## Schematic##
![schematic](schema/2015-05-24%20tmon_schem.png?raw=true)

## Breadboard##
![breadboard](schema/2015-05-24%tmon_bb.png?raw=true)

## Database##
MySQL Database on the Raspberry Pi with the 'log' table in this form:

    +----------+-------------+------+-------+---------------------+
    |Field     |Type         | Null | Key   | Default Extra       |
    +----------+-------------+------+-------+---------------------|
    |id        |int(11)      | NO   | PRI   | NULL auto_increment |
    |timestamp |datetime     | YES  | NULL  |                     |
    |type      |char(1)      | YES  | NULL  |                     |
    |sensor    |varchar(20)  | YES  | NULL  |                     |
    |value     |decimal(4,1) | YES  | NULL  |                     |
    +----------+-------------+------+-------+---------------------+

