## tmon##
tmon implements a Raspberry Pi based watchdog for temperature logging and intrusion detection in a dataroom and has the following features: 
- Multiple Dallas DS18S20 type thermometers support. These thermometers can be plugged in and removed on the fly
- System temperature monitoring
- Sensor address aliasing for user friendly operation
- Three door contact sensors
- Configuration using /etc/tmon.conf config file
- Threaded sensor reading for quick response
- Notifications (alerts) can be sent by e-mail and SMS (using Twilio account)
- Send notification when a sensor is triggers by threshold temperatures
- Send notification when a sensor values are restored
- Send notification when a sensor is removed from the RPi
- Each notification can be sent to another addressee
- notifications can be double, tripled, ...
- Error conditons are shown by an indicator LED and on 2x16 LCD display
- Blinking LED to show tmon is still running
- shows IP address on startup(helpfull in case of DHCP)
- temperature monitoring via 2x16 LCD display
- Cycle through error messages on LCD display using push button
- sensor status logging in MySQL database on the Pi
- Log can be viewed via webpage
- sensor data graphics shown on webpage using PHP

## Development##
- Developed on a Raspberry Pi Model B+ v1.2.
- you can build it on a breadboard
- OS used during development: Headless [Minibian 2015-02-18](https://minibianpi.wordpress.com/)
- Programming on Windows in Notepad++
- Uploaded files using samba
- Written for Python 2.7.3.

## GPIO ports used ##
- GPIO4: onewire hub for DS18B20 thermometers
- GPIO17+27+22: contact1+2+3
- GPIO26+12: LEDs red+green
- GPIO14+15+18+23: LCD DB4-7 datalines
- GPIO7+8: LCD RS+E
- GPIO9+10: 2 pushbuttons

## Schematic##
schematics are drawn with [Fritzing.0.9.1b](http://fritzing.org/)
![schematic](schema/tmon_schem.png?raw=true)

## Breadboard##
![breadboard](schema/tmon_bb.png?raw=true)

## Database##
- data are stored in MySQL database directly on the Raspberry Pi.
- database name = 'tmon'
- table 'log' has te be created manually for now:

                +----------+-------------+------+-------+---------------------+
                |Field     |Type         | Null | Key   | Default Extra       |
                +----------+-------------+------+-------+---------------------|
                |id        |int(11)      | NO   | PRI   | NULL auto_increment |
                |timestamp |datetime     | YES  | NULL  |                     |
                |type      |char(1)      | YES  | NULL  |                     |
                |sensor    |varchar(20)  | YES  | NULL  |                     |
                |value     |decimal(4,1) | YES  | NULL  |                     |
                +----------+-------------+------+-------+---------------------+

