#
# tmon configuration file
#

sensors = (
    {'address': '10-00080256eeff',
        'name': 'dataroom',
        'alerts': (
            [">27",   "+01234567890", ">25'C", "Ok, <25'C"],
            [">27",   "me@home.net", ">25'C", "Ok, <25'C"],
            ["fault", "me@home.net", "sensor fout", "Ok, sensor fout hersteld"]
        )
    },
    
    {'address': '10-000802deb843',
        'name': 'rack',
        'alerts': (
            [">30",   "me@home.net", "BEWARE: >30'C", "Ok, <30'C"],
            []
        )
    },

    {'address': '0',
        'name': 'lokaaldeur',
        'attach': 'http://10.0.100.20:8080/snapshot.cgi?user=login&pwd=password',
        'alerts': (
            ["open",   "+01234567890", "deur is open", "Ok, deur is dicht"],       
            ["open",   "me@home.net", "deur is open", "Ok, deur is dicht"]
        )
    },
    
    {'address': 'system',
        'alerts': (
            [">50",   "+01234567890", "WARNING: System overheating", "Ok, Systemp normalized"],
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
db_expire       = 24           # hours to keep log in database

# mail setup
hostname        = "tmon"
mail_address    = "tmon@gmail.com"
mail_server     = "smtp.gmail.com"
mail_user       = "tmon@gmail.com"
mail_pass       = "zbj6e3rZez6bNYvQcFM"
mail_tls	= True
mail_port	= 587

# SMS setup    
twilio_account_sid  = "AC********************************"
twilio_auth_token   = "05******************************"
twilio_number       = "+5553809123"


