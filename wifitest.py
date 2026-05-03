import machine
import network
import socket
from time import sleep
from wifi_info import ssid, password


#led = machine.Pin(2, machine.Pin.OUT) #changed to 2



def connect():
    #Connect to WLAN
    seconds = 0;
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while wlan.isconnected() == False:
        print('Waiting for connection...')
        sleep(1)
        seconds += 1
        if (seconds > 10):
            raise ValueError("Could not find connection in 10 seconds. Check the SSID or Password.")
            machine.reset()
    ip = wlan.ifconfig()[0]
    print(f'Connected on {ip}')

try:
    connect()
except KeyboardInterrupt:
    machine.reset()