import network
from time import sleep

#WIFI config
ssid = 'dlink_DWR-921'
password = '44590529'
ip = None

def network_connect(): #WIFI connection
    global ip
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while wlan.isconnected() == False:
        print('Waiting for connection...')
        sleep(1)
    ip = wlan.ifconfig()[0]
    print(f'Connected on {ip}')
    return ip

def get_ifconfig_ip():
    global ip
    return ip