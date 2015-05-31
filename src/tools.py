#!/usr/bin/python
#
# tmon - tools library
#
import subprocess

def getipaddress():
    arg = 'ip route list'
    try:
        p = subprocess.Popen(arg, shell=True, stdout=subprocess.PIPE)
        data = p.communicate()
        split_data = data[0].split()
        return split_data[split_data.index('src') + 1]
    except OSError:
        return False


                
                
              





