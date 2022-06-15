from __future__ import print_function
import logging

BAUDRATE = 115200 #9600
PIN = None

from gsmmodem.modem import GsmModem, SentSms

def send_sms(port, phone, message):
    #print('Initializing modem...')
    modem = GsmModem(port, BAUDRATE )
    modem.smsTextMode = False 
    modem.connect(PIN)
    modem.waitForNetworkCoverage(10)
    #print('Sending SMS to: {0}'.format(phone))

    try:
        response = modem.sendSms(phone, message)
        #print(type(response))
        #print(SentSms)
        if type(response) == SentSms:
            #print('SMS Delivered.')
            return True
        else:
            #print('SMS Could not be sent')
            return False

    finally:
        modem.close();

if __name__ == '__main__':
    send_sms()