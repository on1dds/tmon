#!/usr/bin/python
#
# test 
#
import os
import sys
from twilio.rest import TwilioRestClient

ACCOUNT_SID = "AC8ea0cd070e2264607023c953bfa5d90e"
AUTH_TOKEN = "05e87d88da3893c846226dcb5d557d2c"
TEXT_FROM = "+32460201234"
TEXT_TO = "+32484440957"

client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN) 

client.messages.create(
    to= TEXT_TO, 
    from_=TEXT_FROM, 
    body="Hello there",  
)