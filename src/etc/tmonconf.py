#
# tmon configuration file
#

sensors = (
    {'address': '10-0008256eeff',
        'name': 'dataroom',
        'disable': True,
        'alerts': (
            [">25",   "+123456789012",      ">25'C", "Ok, <25'C"],
            [">25",   "me@myprovider.be", ">25'C", "Ok, <25'C"],
            [">25",   "me@myprovider.be", ">25'C", "Ok, <25'C"],
            ["fault", "+123456789012",      "sensor fault", "Ok, sensor restored"]
        )
    },
    
    {'address': '10-000802deb843',
        'name': 'rack',
        'alerts': (
            [">30",   "me@myprovider.be", "BEWARE: >30'C", "Ok, <30'C"],
            []
        )
    },

    {'address': '0',
        'name': 'roomdoor',
        'attach': 'http://192.168.1.45/snapshot.cgi?user=login&pwd=password',
        'alerts': (
            ["open",   "+123456789012", "door is open", "Ok, door is closed"],       
            ["open",   "me@myprovider.be", "door is open", "Ok, door is closed"]
        )
    },
    
    {'address': 'system',
        'alerts': (
            [">50",   "+123456789012", "WARNING: System overheating", "Ok, System temp normalized"],
            []
        )
    },       

    {'address': '1', 'disable': True },
    {'address': '2', 'disable': True }
)


# database configuration
#
db_server       = "localhost"
db_name         = "tmon"
db_user         = "root"
db_pass         = "pi"
db_expire       = 240           # hours to keep log in database

# mail setup
hostname        = "tmon"
mail_address    = "tmon@provider.com"
mail_server     = "smtp.provider.com"
mail_user       = "login"
mail_pass       = "password"

# SMS setup    
twilio_account_sid  = "AC8*******************************"
twilio_auth_token   = "05****************************2c"
twilio_number       = "+1***********"


