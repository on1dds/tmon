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
db = ({
        'server': "localhost",
        'name': "tmon",
        'user': "root",
        'pass': "pi",
        'expire': 24                # hours to keep log in database
    })

# mail setup
mail = ({
    'address' : "tmon@gmail.com",
    'server' : "smtp.gmail.com",
    'user' : "tmon@gmail.com",
    'pass' : "zbj6e3rjJz6bNYvQcJM",
    'tls' : True,
    'port' : 587
})

# SMS setup
twilio = ({
    'account_sid' : "AC********************************",
    'auth_token': "05******************************",
    'number': "+5553809123"
})
    


