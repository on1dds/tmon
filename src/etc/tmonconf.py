#
# tmon configuration file
#

sensors = (
    {'thermometer': '10-00080256eeff',
        'name': 'dataroom',
        'resolution': 0.1,
        'interval': 10,
        'alerts': (
            [">27",   "+01234567890", ">25'C", "Ok, <25'C"],
            [">27",   "me@home.net", ">25'C", "Ok, <25'C"],
            ["fault", "me@home.net", "sensor fout", "Ok, sensor fout hersteld"]
        )
    },
    
    {'thermometer': '10-000802deb843',
        'name': 'rack',
        'buffer': 10,
        'resolution': 0.15,
        'alerts': (
            [">30",   "me@home.net", "BEWARE: >30'C", "Ok, <30'C"],
            []
        )
    },

    {'contact': '0',
        'name' : 'lokaaldeur',
        'attach': 'http://10.0.100.20:8080/snapshot.cgi?user=login&pwd=password',
        'interval' : 0.5,
        'alerts': (
            ["open",   "+01234567890", "deur is open", "Ok, deur is dicht"],       
            ["open",   "me@home.net", "deur is open", "Ok, deur is dicht"]
        )
    },
    
    {'thermometer': 'system',
        'buffer': 20,
        'resolution': 0.5,
        'alerts': (
            [">50",   "+01234567890", "WARNING: System overheating", "Ok, Systemp normalized"],
            []
        )
    },       
)


# database configuration
#
db_server       = "localhost"
db_name         = "tmon"
db_user         = "root"
db_pass         = "pi"
db_expire       = 24           # hours to keep log in database

# mail setup
hostname        = "tmon"
mail_address    = "tmon@gmail.com"
mail_server     = "smtp.gmail.com"
mail_user       = "tmon@gmail.com"
mail_pass       = "zbj6e3rZez6bNYvQcJM"
mail_tls	= True
mail_port	= 587

# SMS setup    
twilio_account_sid  = "AC********************************"
twilio_auth_token   = "05******************************"
twilio_number       = "+5553809123"


