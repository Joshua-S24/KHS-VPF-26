import machine
import network
import socket
from time import sleep
from wifi_info import ssid, password, pico_ip, subnet, gateway, dns

led = machine.Pin("LED", machine.Pin.OUT) #changed to base led



def connect():
  #Connect to WLAN
    connection = False
        
    while connection == False:
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.ifconfig((pico_ip, subnet, gateway, dns))
        wlan.connect(ssid, password)
    
        for count in range(5):
            if wlan.isconnected() == True:
                connection = True
            else:
                print('Waiting for connection...', count, end='\r')
                sleep(1)

    ip = wlan.ifconfig()[0] #static ip (pico_ip, subnet, gateway, dns)
    print(f'Connected on {ip}')
    return ip

def open_socket(ip):
  # Open a socket
  address = (ip, 80)
  connection = socket.socket()
  connection.bind(address)
  connection.listen(1)
  return connection

def webpage(state):
  #Template HTML
  html = f"""
      <!DOCTYPE html>
      <html>
      <form action="./lighton">
      <input type="submit" value="Light on" />
      </form>
      <form action="./lightoff">
      <input type="submit" value="Light off" />
      </form>
      <p>LED is {state}</p>
      </body>
      </html>
      """
  return str(html)

def serve(connection):
  #Start a web server
  state = 'OFF'
  led.off()
  while True:
    client = connection.accept()[0]
    request = client.recv(1024)
    request = str(request)
    try:
      request = request.split()[1]
    except IndexError:
      pass
    if request == '/lighton?':
      led.on()
      state = 'ON'
    elif request =='/lightoff?':
      led.off()
      state = 'OFF'
    html = webpage(state)
    client.send(html)
    client.close()

try:
  ip = connect()
  connection = open_socket(ip)
  serve(connection)
except KeyboardInterrupt:
  machine.reset()