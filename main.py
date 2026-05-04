import machine
import network
import socket
from time import sleep
from wifi_info import ssid, password, pico_ip, subnet, gateway, dns
import sdcard
import uos

# Pin Configuration
"""
Pin List:
x2 Limit Switch [IN] (GPIO0, GPIO1) {NOTE: May require a low-value resistor for safe HIGH reading; make sure pins don't go above 3.3V otherwise}
L298N Motor Controller IN1, IN2 [OUT] (GPIO16, GPIO17)
Pressure Sensor Signal [IN, ADC (Analog)] (GPIO22) {NOTE: Check to make sure signal CANNOT go above 3.3V}
SD Card [SPI] (MISO: GPIO8, SCK: GPIO10, MOSI: GPIO11)
"""
CS = machine.Pin(9, machine.Pin.OUT) # Configure the Chip Select pin
spi = machine.SPI(1, # Initialize SPI1 with the *specified pins* and baud rate
                  baudrate=1000000,
                  polarity=0,
                  phase=0,
                  bits=8,
                  firstbit=machine.SPI.MSB,
                  sck=machine.Pin(10),
                  mosi=machine.Pin(11),
                  miso=machine.Pin(8))
sensor_pin = machine.Pin(22, machine.Pin.IN) # ANALOG Value
pressure_sensor = machine.ADC(sensor_pin)
limitsw_1 = machine.Pin(0, machine.Pin.IN, machine.Pin.PULL_DOWN)
limitsw_2 = machine.Pin(1, machine.Pin.IN, machine.Pin.PULL_DOWN)
motor_in1 = machine.Pin(16, machine.Pin.OUT)
motor_in2 = machine.Pin(17, machine.Pin.OUT)

# Connects to WLAN.
def connect():
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

    ip = wlan.ifconfig()[0]
    print(f'Connected on {ip}')
    return ip

# Opens a socket.
def open_socket(ip):
  address = (ip, 80)
  connection = socket.socket()
  connection.bind(address)
  connection.listen(1)
  return connection

# Returns an HTML page.
def webpage(state):
  html = f"""
      <!DOCTYPE html>
      <html>
      <form action="./submerge">
      <input type="submit" value="Submerge" />
      </form>
      <p>LED is {state}</p>
      </body>
      </html>
      """
  return str(html)

# Starts a web server.
def serve(connection):
  state = 'OFF'
  while True:
    client = connection.accept()[0]
    request = client.recv(1024)
    request = str(request)
    try:
      request = request.split()[1]
    except IndexError:
      pass
    if request == '/submerge?':
      state = 'ON'
      # Begin vertical profile & sever Wi-Fi connection
    html = webpage(state)
    client.send(html)
    client.close()

# Request a Wi-Fi connection.
# This function will likely need to be run twice.
# This is because once the submerge function is called, the Wi-Fi connection will be lost due to water.
# Once the float re-emerges, this function will be called again in order to transmit data.
def request_connection():
    try:
      ip = connect()
      connection = open_socket(ip)
      serve(connection)
    except KeyboardInterrupt: # Will not work remotely; flip the float's switch off and on again for a reset.
      machine.reset()
      
# Reads data from the pressure sensor's signal.
def sensor_read():
    # Note: We are not using a traditional water pressure sensor, so the values may have to be played with for accuracy
    water_density = 0.1
    sensor_inp = pressure_sensor.read_u16() # Returns a 16-bit value. (0 - 65535)
    voltage = sensor_inp * (3.3 / 65535)
    info = {} # Returns water pressure and temperature
    return info

def piston_down():
    pass

def piston_up():
    pass

# the hard part.
def find_neutral_buoyancy():
    pass

def vertical_profile():
    pass

# Main Function

# Initialize the SD card object
sd = sdcard.SDCard(spi, CS)
# Mount the FAT filesystem
vfs = uos.VfsFat(sd)
uos.mount(vfs, "/sd")
print("SD card mounted successfully!")

request_connection()