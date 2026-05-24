import machine
import network
import socket
from time import sleep
from wifi_info import ssid, password, pico_ip, subnet, gateway, dns
#import sdcard
#import uos
from enum import Enum

# NOTE: Scrapping SD card idea

# Pin Configuration
"""
Pin List:
x2 Limit Switch [IN] (GPIO0, GPIO1) {NOTE: May require a low-value resistor for safe HIGH reading; make sure pins don't go above 3.3V otherwise}
L298N Motor Controller IN1, IN2 [OUT] (GPIO16, GPIO17)
Pressure Sensor Signal [IN, ADC (Analog)] (GPIO22) {NOTE: Check to make sure signal CANNOT go above 3.3V}
SD Card [SPI] (MISO: GPIO8, SCK: GPIO10, MOSI: GPIO11) (Deprecated)
"""

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
"""
sensor_pin = machine.Pin(22, machine.Pin.IN) # ANALOG Value
pressure_sensor = machine.ADC(sensor_pin)
limitsw_upper = machine.Pin(0, machine.Pin.IN, machine.Pin.PULL_DOWN)
limitsw_lower = machine.Pin(1, machine.Pin.IN, machine.Pin.PULL_DOWN)
motor_in1 = machine.Pin(16, machine.Pin.OUT)
motor_in2 = machine.Pin(17, machine.Pin.OUT)

# Global Variables
class Status(Enum):
    ACTIVE = 0 # Ready for profiling. Default state.
    COMPLETED = 1 # Profiling was successful.
    ABORTED = 2 # Profiling failed.
current_state = Status.ACTIVE
depth = 0
pressure = 0
depth_list = [] # List of depths taken across 5-second intervals. Will contain 7 entries max.
pressure_list = [] # List of pressure values taken across 5-second intervals. Will contain 7 entries max.

# Constants
# TODO: Decide units
WATER_DENSITY = 0.1 # The density of the water.
MARGIN = 1 # The margin of error for the target depth.
OFFSET = 1 # The offset of the sensor from the depth of the float, recorded from the top.
DEPTH_1 = 0 # Target depth #1.
DEPTH_2 = 0 # Target depth #2.

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
      # TODO: Make buttons for 2 separate vertical profiles (1 and 2)
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
      
# Records the water pressure and current height from the pressure sensor's signal.
# This will be called every half-second to check the float's depth.
# Once the float is at a given depth, the data from this function will be recorded every 5 seconds.
def sensor_read():
    # Note: We are not using a traditional water pressure sensor, so the values may have to be played with for accuracy
    # Note: Units need to be decided (SI could be used)
    sensor_inp = pressure_sensor.read_u16() # Returns a 16-bit value. (0 - 65535)
    voltage = sensor_inp * (3.3 / 65535)
    if sensor_inp == 0: # Default values (on surface)
        depth = 0
        pressure = 0
    else: # Calculate depth and pressure.
        pass


# Pushes the piston down, expelling water and causing the float to rise.
# This will fail if the lower switch is pushed.
def piston_down():
    if limitsw_lower != 1:
        motor_in1.high()
        motor_in2.low()

# Pushes the piston up, intaking water and causing the float to sink.
# This will fail if the upper switch is pushed.
def piston_up():
    if limitsw_upper != 1:
        motor_in1.low()
        motor_in2.high()

def piston_stop():
    motor_in1.low()
    motor_in2.low()

# the hard part.
def find_neutral_buoyancy(depth : int):
    pass
    

def vertical_profile(target_depth : int):
    # Note: maybe add a fail safe? 
    # Phase 1: Descent/Ascent
    if (depth < target_depth): # If the float's current depth is below target depth...
        while depth < (target_depth - MARGIN):
            if limitsw_upper != 1:
                piston_up()
            sensor_read()
            sleep(0.2)
    elif depth > target_depth: # If the float's current depth is above target depth...
        while depth > (target_depth + MARGIN):
            if limitsw_lower != 1:
                piston_down()
            sensor_read()
            sleep(0.2)
    # Phase 2: Adjustment for neutral buoyancy
    piston_stop()
    # TBD
    # Phase 3: Recording
    for i in range(6):
        depth_list.append(depth)
        pressure_list.append(pressure)
        sleep(5)
    depth_list.append(depth) # 7th entry
    pressure_list.append(pressure)
    # Phase 4: Surfacing

def task_4(depth1 : int, depth2 : int):
    depth = 0
    pressure = 0
    vertical_profile(depth1)
    pass

# Main Function

"""
# Initialize the SD card object
try:
    sd = sdcard.SDCard(spi, CS)
    # Mount the FAT filesystem
    vfs = uos.VfsFat(sd)
    uos.mount(vfs, "/sd")
    print("SD card mounted successfully!")
except:
    print("SD card missing.")
"""
request_connection()