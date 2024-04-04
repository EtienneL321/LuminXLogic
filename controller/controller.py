#!/usr/bin/env python3

import logging
import signal

import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service
from dbus import ByteArray

from ble import (
    Advertisement,
    Characteristic,
    Service,
    Application,
    find_adapter,
    Descriptor,
    Agent,
)

import array
from enum import Enum
import threading
lock = threading.Lock()
###############################################################################################
import serial
import time
from PIL import Image
import RPi.GPIO as GPIO
import colorsys
import ephem
import datetime

#set up photoresistor
from gpiozero import PWMLED, MCP3008
adc = MCP3008(channel=0)  

#power state
#rgbw status
#mode




#mode dictates what mode the light is in
# 0 - Off
# 1 - Colour reproduction mode
# 2 - Sunrise/Sunset mode
# 3 - Analagous Colour mode
mode = 0 
state = 0 #on/off
scale = 100 #brightness scale

r = 0
g = 0
b = 0
w = 0
#Functions for sunrise and sunset
def is_30_min_before(latitude, longitude, sunrise):
    
    current_time = datetime.datetime.now()

    # Check if the current time is 30 minutes before sunrise
    if current_time - sunrise <= datetime.timedelta(minutes=30):
        return True
    else:
        return False

def get_sunrise_sunset(latitude, longitude):
    observer = ephem.Observer()
    observer.lat = str(latitude)
    observer.lon = str(longitude)

    # Get current UTC time
    now_utc = datetime.datetime.utcnow()

    # Set the observer date and time
    observer.date = now_utc

    # Compute sunrise and sunset
    sunrise = observer.previous_rising(ephem.Sun())
    sunset = observer.next_setting(ephem.Sun())

    # Convert to local time
    sunrise_local = ephem.localtime(sunrise)
    sunset_local = ephem.localtime(sunset)

    return sunrise_local, sunset_local


#set up time and get sunset and sunrise times
#Will get from app
latitude = 51.0447
longitude = -114.0719

sunrise,sunset = get_sunrise_sunset(latitude,longitude)

print(sunrise)
print(sunset)




#set up GPIO pins
redPin = 18              # PWM pin connected to LED
greenPin = 12
bluePin = 19
whitePin = 13
frequency = 1000         # PWM frequency in Hz

GPIO.setmode(GPIO.BCM)
GPIO.setup(redPin, GPIO.OUT)
GPIO.setup(greenPin, GPIO.OUT)
GPIO.setup(bluePin, GPIO.OUT)
GPIO.setup(whitePin, GPIO.OUT)
rpwm = GPIO.PWM(redPin, frequency)
gpwm = GPIO.PWM(greenPin, frequency)
bpwm = GPIO.PWM(bluePin, frequency)
wpwm = GPIO.PWM(whitePin, frequency)

ser = serial.Serial("/dev/ttyS0", baudrate=9600, timeout=1, stopbits=serial.STOPBITS_ONE, bytesize=8, parity=serial.PARITY_NONE)



rpwm.start(0)  # Start PWM with 0% duty cycle
gpwm.start(0)
bpwm.start(0)
wpwm.start(0)


# functions for GPIO

#See if two values are within 80% of eachother
#used to see whether it should or should not update the led for small changes
def within_percent(num1, num2):
    # Calculate 80% of num1
    threshold = num1 * 0.8
    # Check if num2 is within 90% of num1
    return num2 >= threshold and num2 <= num1 * 1.1 

#Turns rgb into hue, saturation, value
def rgb_to_hsv(rgb):
    r, g, b = rgb
    return colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)

#Turns hsv back into rgb
def hsv_to_rgb(hsv):
    h, s, v = hsv
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return int(r * 255), int(g * 255), int(b * 255)

#after converting rgb to hsv, maxes out the value so it can maintain colour data no matter the length from the colour sensor
def adjust_saturation_and_value(rgb, saturation_factor, value_factor):
    h, s, v = rgb_to_hsv(rgb)
    s = 1
    v = 1
    return hsv_to_rgb((h, s, v))

#Reads serial port
def read_sensor_data():
    print("Reading")
    response = b''  # Initialize an empty bytes object
    while True:
        char = ser.read(1)
        response += char
        if char == b'\r':
            break
    print("Read")
    return response

#gets rgb values from serial
def parse_rgb_values(rgb_bytes):
    # Remove the b' at the beginning and \r' at the end, and split the values
    values = rgb_bytes.decode('utf-8')
    values = values.split(',')

    rgb_values = [(int(value) if value else 0) for value in values]

    # Assign the values to individual variables
    red, green, blue = rgb_values

    return red, green, blue

def rgb_to_hsl(rgb):
    # Convert RGB to HSL
    h, l, s = colorsys.rgb_to_hls(*[x / 255.0 for x in rgb])
    return h, s, l

def hsl_to_rgb(hsl):
    # Convert HSL to RGB
    r, g, b = colorsys.hls_to_rgb(*hsl)
    return int(r * 255), int(g * 255), int(b * 255)

def calculate_analogous_colors(rgb):
    hsl = colorsys.rgb_to_hls(rgb[0],rgb[1],rgb[2])

    # Calculate new hue
    new_hue = (hsl[0] + 30 / 360.0) % 1.0

    # Convert back to RGB
    analogous_color = colorsys.hls_to_rgb(new_hue, hsl[1], hsl[2])

    return analogous_color

def ambient_light_percentage():
    analog_value = adc.value
    print("Analog Value:", analog_value)

    return analog_value

def control():
    global r
    global g
    global b
    global w
    ser.write(b'c,1\r\n') #turn on continuous mode
    time.sleep(0.1)
    data = read_sensor_data()
    data = read_sensor_data()
    data = read_sensor_data()
    data = read_sensor_data()
    data = read_sensor_data()
    
    print(data)
    # data = read_sensor_data()
    

    try:
        prev_red = 0
        prev_blue = 0
        prev_green = 0
        
        while True:
            
            # time.sleep(5)
            # rpwm.ChangeDutyCycle(50)
            # gpwm.ChangeDutyCycle(0)
            # bpwm.ChangeDutyCycle(50)
            # time.sleep(5)
            # rpwm.ChangeDutyCycle(50)
            # gpwm.ChangeDutyCycle(50)
            # bpwm.ChangeDutyCycle(0)
            # time.sleep(5)
            
            #Off mode
            if state == 0:
                r = 0
                g = 0
                b = 0
                w = 0
                rpwm.ChangeDutyCycle(0)
                gpwm.ChangeDutyCycle(0)
                bpwm.ChangeDutyCycle(0)
                wpwm.ChangeDutyCycle(0)
                
                
            #Device on
            elif state == 1:
            
            #Colour reproduction moode
                if mode == 0:            
                    data = read_sensor_data()
                    if data:
                        red, green, blue = parse_rgb_values(data)
                        
                        #Scale green and blue signals, ans blue tends to overpower green
                        green = green*1.1
                        blue = blue*0.75
                        
                        #frind predominant colour
                        predom = max(red, green, blue)
                        
                        #avoid div by 0
                        if predom == 0:
                            predom = 1
                            
                        #normalize rgb values to 0-255
                        red = red/predom*255
                        green = green/predom*255
                        blue = blue/predom*255
                        
                        
                        whitePairs = [(red,green),(red,blue),(green,blue)]
                        #if rgb are within 20% of eachother, produce white
                        for pair in whitePairs:
                            num1, num2 = pair
                            if not within_percent(num1, num2):
                                print("not white")
                                all_within_percent = False
                                break
                        if all_within_percent:
                            red = 200
                            green = 200
                            blue = 200
                        
                            
                            
                        #have white as the minimum of the 3 rgb components with minimum value of 100
                        white = min(red, green, blue)
                        white = max(white, 100)
                        
                        
                    #Check to see if numbers are within 20% of previous values, if all are, keep the same colour
                        pairs = [(red,prev_red),(blue,prev_blue),(green,prev_green)]
                        all_within_percent = True

                        for pair in pairs:
                            num1, num2 = pair
                            if not within_percent(num1, num2):
                                all_within_percent = False
                                break

                        if all_within_percent:
                            red = prev_red
                            green = prev_green
                            blue = prev_blue
                            white = prev_white
                            
                            prev_colour = True
                        else:
                            prev_colour = False
                            print("Not all pairs are within 90% of each other.")
                        
                        all_within_percent = True

                        new_rgb_color = (red,green,blue)
                        
                        with lock:
                            #global variables to send data to app
                            r = red
                            g = green
                            b = blue
                            w = white
                        
                        
                        #normalize to 0-100 for pwm output
                        maximum = max(new_rgb_color[0],new_rgb_color[1],new_rgb_color[2], white)

                        if maximum == 0:
                            maximum = 1
                        nred = new_rgb_color[0] / maximum * 100
                        ngreen = new_rgb_color[1] / maximum * 100
                        nblue = new_rgb_color[2] / maximum * 100
                        nwhite = white/maximum *100
                        
                        #scale for more vibrant colours
                        if nred<10:
                            nred = 0
                        elif nred <30 :
                            nred = nred*0.5
                        elif nred <50 :
                            nred = nred*0.6
                        elif nred <70 :
                            nred = nred*0.8
                        if ngreen < 10:
                            ngreen = 0
                        elif ngreen <30 :
                            ngreen = ngreen*0.5
                        elif ngreen <50 :
                            ngreen = ngreen*0.6
                        elif ngreen <70 :
                            ngreen = ngreen*0.8
                        if nblue < 10:
                            nblue = 0
                        elif nblue <30 :
                            nblue = nblue*0.5
                        elif nblue <50 :
                            nblue = nblue*0.6
                        elif nblue <70 :
                            nblue = nblue*0.8
                        
                    #if it is not the previous colour, update to new colour
                        ambient_scale =  ambient_light_percentage()
                        
                        ambient_scale= ambient_scale*(scale/100)
                        
                        print(nred,ngreen,nblue,nwhite)
                        wpwm.ChangeDutyCycle((nwhite*ambient_scale))
            
                        rpwm.ChangeDutyCycle((nred*ambient_scale))
                    
                        gpwm.ChangeDutyCycle((ngreen*ambient_scale))
                        
                        bpwm.ChangeDutyCycle((nblue*ambient_scale))
                    
                        
                        
                    else:
                        print("Error: No data received from the sensor")
                
            
                                   
                    prev_red = new_rgb_color[0]
                    prev_green = new_rgb_color[1]
                    prev_blue = new_rgb_color[2]
                    prev_white = white
                    
                elif mode == 1:
                    sunrise = datetime.datetime.now() + datetime.timedelta(minutes=30)
                    while mode ==1:
                
                    #sunrise contingency
                        if is_30_min_before(latitude,longitude,sunrise):
                            if mode != 1:
                                    break
                            for i in range(int(20)):
                                if mode != 1:
                                    break
                                with lock:
                                    r = int(241 - 51 * i /20)
                                    g = int(56 + 84 * i/20)
                                    b = int(16 + 159 * i/20)
                                    w = 0

                            # Update PWM duty cycles
                                rpwm.ChangeDutyCycle((r / 255) * (33*i/20))
                                print((r / 255) * (33*i/20))
                                gpwm.ChangeDutyCycle((g / 255) * (33*i/20))
                                print((g / 255) * (33*i/20))
                                bpwm.ChangeDutyCycle((b / 255) * (33*i/20))
                                print((b / 255) * (33*i/20))
                                wpwm.ChangeDutyCycle(0)

                                time.sleep(1)
                        
                            for i in range(int(20)):
                                if mode != 1:
                                    break
                                with lock:
                                    r = int(190 + 60 * i /20)
                                    g = int(140 + 75 * i/20)
                                    b = int(175 - 15 * i/20)
                            

                            # Update PWM duty cycles
                                rpwm.ChangeDutyCycle((r / 255) * 33+(33*i/20))
                                print((r / 255) * 33+(33*i/20))
                                gpwm.ChangeDutyCycle((g / 255) * 33+(33*i/20))
                                print((g / 255) * 33+(33*i/20))
                                bpwm.ChangeDutyCycle((b / 255) * 33+(33*i/20))
                                print((b / 255) * 33+(33*i/20))

                                time.sleep(1)
                            if mode != 1:
                                break
                            for i in range(int(20)):
                                if mode != 1:
                                    break
                                with lock:
                                    r = int(250 + 5 * i /20)
                                    g = int(215 + 40 * i/20)
                                    b = int(160 + 95 * i/20)

                            # Update PWM duty cycle
                                rpwm.ChangeDutyCycle((r / 255) * 66+(34*i/20))
                                print((r / 255) * 66+(33*i/20))
                                gpwm.ChangeDutyCycle((g / 255) * 66+(34*i/20))
                                print((r / 255) * 66+(33*i/20))
                                bpwm.ChangeDutyCycle((b / 255) * 66+(34*i/20))
                                print((r / 255) * 66+(33*i/20))

                                time.sleep(1)
                            print("finished")
                    
                    
                    
                if mode == 2:
                    sunset = datetime.datetime.now() + datetime.timedelta(minutes=30)
                    while mode == 2:
                    #sunset
                        if is_30_min_before(latitude,longitude,sunset):
                            for i in range(int(30)):
                                if mode != 2:
                                    break
                                with lock:
                                    r = int(255 - 15 * i /(30))
                                    g = int(255 - 49 * i/(30))
                                    b = int(255 - 76 * i/(30))
                                    w = 0

                            # Update PWM duty cycles
                                rpwm.ChangeDutyCycle((r / 255) * (100-(10*(i/30))))
                                print(r)
                                gpwm.ChangeDutyCycle((g / 255) * (100-(10*(i/30))))
                                print(g)
                                bpwm.ChangeDutyCycle((b / 255) *(100-(10*(i/30))))
                                wpwm.ChangeDutyCycle(0)
                                print(b)

                                time.sleep(1)
                        
                            for i in range(int(30)):
                                if mode != 2:
                                    break
                                with lock:
                                    r = int(240 + 3 * i /(30))
                                    g = int(206 - 45 * i/(30))
                                    b = int(179 - 82 * i/(30))

                            # Update PWM duty cycles
                                rpwm.ChangeDutyCycle((r / 255) * (90-(10*(i/30))))
                                print(r)
                                gpwm.ChangeDutyCycle((g / 255) * (90-(10*(i/30))))
                                print(g)
                                bpwm.ChangeDutyCycle((b / 255) * (90-(10*(1/30))))
                                print(b)

                                time.sleep(1)
                        
                            for i in range(int(30)):
                                if mode != 2:
                                    break
                                with lock:
                                    r = int(243 - 68 * i /(30))
                                    g = int(161 - 68 * i/(30))
                                    b = int(97 - 66 * i/(30))

                            # Update PWM duty cycles
                                rpwm.ChangeDutyCycle((r / 255) * (80-(15*(i/30))))
                                print(r)
                                gpwm.ChangeDutyCycle((g / 255) * (80-(15*(i/30))))
                                print(g)
                                bpwm.ChangeDutyCycle((b / 255) * (80-(15*(i/30))))
                                print((b / 255) * 80-(15*(i/30)))

                                time.sleep(1)
                        
                            for i in range(int(30)):
                                if mode != 2:
                                    break
                                with lock:
                                    r = int(175 - 44 * i /(30))
                                    g = int(93 - 29 * i/(30))
                                    b = int(31 - 18 * i/(30))

                                # Update PWM duty cycles
                                rpwm.ChangeDutyCycle(max(0,(r / 255) * (65-(15*(i/30)))))
                                print(r)
                                gpwm.ChangeDutyCycle(max(0,(g / 255) * (65-(15*(i/30)))))
                                print(g)
                                bpwm.ChangeDutyCycle(max(0,(b / 255) * (65-(15*(1/30)))))
                                print(b)

                                time.sleep(1)
                                
                            
                if mode == 3:            
                    data = read_sensor_data()
                    if data:
                        red, green, blue = parse_rgb_values(data)
                        
                        #Scale green and blue signals, ans blue tends to overpower green
                        green = green*1.1
                        blue = blue*0.75
                        
                        #frind predominant colour
                        predom = max(red, green, blue)
                        
                        #avoid div by 0
                        if predom == 0:
                            predom = 1
                            
                        #normalize rgb values to 0-255
                        red = red/predom*255
                        green = green/predom*255
                        blue = blue/predom*255
                        
                        
                        whitePairs = [(red,green),(red,blue),(green,blue)]
                        #if rgb are within 20% of eachother, produce white
                        for pair in whitePairs:
                            num1, num2 = pair
                            if not within_percent(num1, num2):
                                print("not white")
                                all_within_percent = False
                                break
                        if all_within_percent:
                            red = 200
                            green = 200
                            blue = 200
                        
                            
                            
                        #have white as the minimum of the 3 rgb components with minimum value of 100
                        white = min(red, green, blue)
                        white = max(white, 100)
                        
                        
                    #Check to see if numbers are within 20% of previous values, if all are, keep the same colour
                        pairs = [(red,prev_red),(blue,prev_blue),(green,prev_green)]
                        all_within_percent = True

                        for pair in pairs:
                            num1, num2 = pair
                            if not within_percent(num1, num2):
                                all_within_percent = False
                                break

                        if all_within_percent:
                            red = prev_red
                            green = prev_green
                            blue = prev_blue
                            prev_colour = True
                        else:
                            prev_colour = False
                            print("Not all pairs are within 90% of each other.")
                        
                        all_within_percent = True

                        new_rgb_color = (red,green,blue)
                        print(new_rgb_color)
                        new_rgb_color = calculate_analogous_colors(new_rgb_color)
                        print(new_rgb_color)
                        #global variables to send data to app
                        
                        with lock:
                            r = new_rgb_color[0]
                            g = new_rgb_color[1]
                            b = new_rgb_color[2]
                            w = white

                        
                        #normalize to 0-100 for pwm output
                        maximum = max(new_rgb_color[0],new_rgb_color[1],new_rgb_color[2], white)

                        if maximum == 0:
                            maximum = 1
                        nred = new_rgb_color[0] / maximum * 100
                        ngreen = new_rgb_color[1] / maximum * 100
                        nblue = new_rgb_color[2] / maximum * 100
                        nwhite = white/maximum *100
                        
                        #scale for more vibrant colours
                        if nred<10:
                            nred = 0
                        elif nred <30 :
                            nred = nred*0.5
                        elif nred <50 :
                            nred = nred*0.6
                        elif nred <70 :
                            nred = nred*0.8
                        if ngreen < 10:
                            ngreen = 0
                        elif ngreen <30 :
                            ngreen = ngreen*0.5
                        elif ngreen <50 :
                            ngreen = ngreen*0.6
                        elif ngreen <70 :
                            ngreen = ngreen*0.8
                        if nblue < 10:
                            nblue = 0
                        elif nblue <30 :
                            nblue = nblue*0.5
                        elif nblue <50 :
                            nblue = nblue*0.6
                        elif nblue <70 :
                            nblue = nblue*0.8
                        
                        ambient_scale =  ambient_light_percentage()
                        
                        ambient_scale= ambient_scale*(scale/100)
                        
                        print(nred,ngreen,nblue,nwhite)
                        wpwm.ChangeDutyCycle((nwhite*ambient_scale))
            
                        rpwm.ChangeDutyCycle((nred*ambient_scale))
                    
                        gpwm.ChangeDutyCycle((ngreen*ambient_scale))
                        
                        bpwm.ChangeDutyCycle((nblue*ambient_scale))
                    
                        
                        
                    else:
                        print("Error: No data received from the sensor")
                
                
                    
                    prev_red = new_rgb_color[0]
                    prev_green = new_rgb_color[1]
                    prev_blue = new_rgb_color[2]
                    
                if mode == 4:
                    with lock:
                        r = 255
                        g = 255
                        b = 255
                        w = 255
                    ambient_scale =  ambient_light_percentage()
                    
                    ambient_scale= ambient_scale*(scale/100)
                    
                    print(nred,ngreen,nblue,nwhite)
                    wpwm.ChangeDutyCycle((100*ambient_scale))
        
                    rpwm.ChangeDutyCycle((100*ambient_scale))
                
                    gpwm.ChangeDutyCycle((100*ambient_scale))
                    
                    bpwm.ChangeDutyCycle((100*ambient_scale))

                

                
                
    #shutdown protocol
    except KeyboardInterrupt:
        ser.write(b'sleep\r\n')
        ser.close()
        for duty_cycle in range(10, -1, -1):
            gpwm.ChangeDutyCycle(duty_cycle)
            rpwm.ChangeDutyCycle(duty_cycle)
            bpwm.ChangeDutyCycle(duty_cycle)
            time.sleep(0.05)
        rpwm.stop()  # Stop PWM before cleanup
        gpwm.stop()
        bpwm.stop()
        print("Exiting...")







###############################################################################################
MainLoop = None
try:
    from gi.repository import GLib

    MainLoop = GLib.MainLoop
except ImportError:
    import gobject as GObject

    MainLoop = GObject.MainLoop

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logHandler = logging.StreamHandler()
filelogHandler = logging.FileHandler("logs.log")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logHandler.setFormatter(formatter)
filelogHandler.setFormatter(formatter)
logger.addHandler(filelogHandler)
logger.addHandler(logHandler)

mainloop = None

BLUEZ_SERVICE_NAME = "org.bluez"
GATT_MANAGER_IFACE = "org.bluez.GattManager1"
LE_ADVERTISEMENT_IFACE = "org.bluez.LEAdvertisement1"
LE_ADVERTISING_MANAGER_IFACE = "org.bluez.LEAdvertisingManager1"


class InvalidArgsException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.freedesktop.DBus.Error.InvalidArgs"

class NotSupportedException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.bluez.Error.NotSupported"

class NotPermittedException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.bluez.Error.NotPermitted"

class InvalidValueLengthException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.bluez.Error.InvalidValueLength"

class FailedException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.bluez.Error.Failed"


"""
------------------------------------------------------------------------
----------------------------- DESCRIPTOR -------------------------------
------------------------------------------------------------------------
"""

class CharacteristicUserDescriptionDescriptor(Descriptor):
    """
    Writable CUD descriptor.
    """

    CUD_UUID = "2802"

    def __init__(
        self, bus, index, characteristic,
    ):

        self.value = array.array("B", characteristic.description)
        self.value = self.value.tolist()
        Descriptor.__init__(self, bus, index, self.CUD_UUID, ["read"], characteristic)

    def ReadValue(self, options):
        return self.value

    def WriteValue(self, value, options):
        if not self.writable:
            raise NotPermittedException()
        self.value = value


"""
------------------------------------------------------------------------
-------------------------- CHARACTERISTICS -----------------------------
------------------------------------------------------------------------
"""

class PowerControlCharacteristic(Characteristic):
    """
    VALID VALUES
    0 - power off
    1 - power on
    
    """
    uuid = "7c4d8002-0013-0012-0011-7c4d00010001"
    description = b"Get/set light power state"

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index, self.uuid, ["encrypt-read", "encrypt-write"], service,
        )

        self.value = [0x00]
        self.add_descriptor(CharacteristicUserDescriptionDescriptor(bus, 1, self))

    def ReadValue(self, options):
        logger.debug("power Read: " + repr(self.value))
        return self.value

    def WriteValue(self, value, options):
        logger.debug("power Write: " + repr(value))
        val = list(value)
        val = int(val[0])
        logger.debug(val)
        global state
        with lock:
            state = val
        self.value = value
        

class ModeControlCharacteristic(Characteristic):
    """
    VALID VALUES
    0 - Colour Sensing
    1 - Sunrise
    2 - Sunset
    3 - Analagous Colour
    4 - White
    
    All other values are undefined
    
    """
    uuid = "7c4d8002-0013-0012-0011-7c4d00010002"
    description = b"Get/set light mode"

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index, self.uuid, ["encrypt-read", "encrypt-write"], service,
        )

        self.value = [0x00]
        self.add_descriptor(CharacteristicUserDescriptionDescriptor(bus, 2, self))

    def ReadValue(self, options):
        logger.debug("mode Read: " + repr(self.value))
        return self.value

    def WriteValue(self, value, options):
        logger.debug("mode Write: " + repr(value))
        val = list(value)
        val = int(val[0])
        logger.debug(val)
        global mode
        with lock:
            mode = val
        self.value = value


class RGBWColourCharacteristic(Characteristic):
    """
    VALID VALUES
    
    """
    uuid = "7c4d8002-0013-0012-0011-7c4d00020005"
    description = b"Get/set colour"

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index, self.uuid, ["encrypt-read", "encrypt-write"], service,
        )

        self.value = [0x00,0x01,0x02,0x03]
        self.add_descriptor(CharacteristicUserDescriptionDescriptor(bus, 4, self))

    def ReadValue(self, options):
        global r
        global g
        global b
        global w
        # print(r,g,b,w)
        with lock:
        
            arr = [r,g,b,w]
            print(arr)
            self.value = arr
            logger.debug("[red, green, blue, white] Read: [" + repr(self.value[0]) + ", " + repr(self.value[1]) + ", " + repr(self.value[2]) + ", " + repr(self.value[3]) + "]")

        
        return self.value

    def WriteValue(self, value, options):
        logger.debug("[red, green, blue, white] Write: [" + repr(value[0]) + ", " + repr(value[1]) + ", " + repr(value[2]) + ", " + repr(value[3]) + "]")
        for v in value:
            colour = int(v)
            print("test")
            print("colour is: " + colour)
        # val = list(repr(value))
        # logger.log(repr(value[0]))
        # logger.log(int(val[0]))  
        print("test")    
        self.value = value 


class IntensityCharacteristic(Characteristic):
    """
    VALID VALUES
    1-100

    0 should be interpreted as 1
    101-255 should be interpreted as 100
    
    """
    uuid = "7c4d8002-0013-0012-0011-7c4d00020006"
    description = b"Get/set intensity"

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index, self.uuid, ["encrypt-read", "encrypt-write"], service,
        )

        self.value = [0x64]
        self.add_descriptor(CharacteristicUserDescriptionDescriptor(bus, 5, self))

    def ReadValue(self, options):
        logger.debug("intensity Read: " + repr(self.value) + "%")
        return self.value

    def WriteValue(self, value, options):
        logger.debug("intensity Write: " + repr(value) + "%")
        logger.debug(f"intensity Percentage: {int(value[0])}%")
        global scale
        with lock:
            scale = int(value[0])
        self.value = value


"""
------------------------------------------------------------------------
----------------------------- SERVICES ---------------------------------
------------------------------------------------------------------------
"""

class LightControlService(Service):
    """
    LightControlService controls the following characteristics:
    - PowerControlCharaceristic
    - ModeControlCharacteristic

    """

    LIGHT_SVC_UUID = "7c4d8001-0013-0012-0011-7c4d80010001"

    def __init__(self, bus, index):
        Service.__init__(self, bus, index, self.LIGHT_SVC_UUID, True)
        self.add_characteristic(PowerControlCharacteristic(bus, 0, self))
        self.add_characteristic(ModeControlCharacteristic(bus, 1, self))


class LEDColourService(Service):
    """
    LEDColourService controls the following characteristics:
    - RGBWColourCharacteristic
    - IntensityCharacteristic

    """

    LED_SVC_UUID = "7c4d8001-0013-0012-0011-7c4d80010002"

    def __init__(self, bus, index):
        Service.__init__(self, bus, index, self.LED_SVC_UUID, True)
        self.add_characteristic(RGBWColourCharacteristic(bus, 4, self))
        self.add_characteristic(IntensityCharacteristic(bus, 5, self))

def register_app_cb():
    logger.info("GATT application registered")

def register_app_error_cb(error):
    logger.critical("Failed to register application: " + str(error))
    mainloop.quit()


"""
------------------------------------------------------------------------
--------------------------- ADVERTISEMENT ------------------------------
------------------------------------------------------------------------
"""

class LuminXLogicAdvertisement(Advertisement):
    def __init__(self, bus, index):
        Advertisement.__init__(self, bus, index, "peripheral")
        self.add_manufacturer_data(
            0xdddd, [0x70, 0x74],
        )
        self.add_service_uuid(LightControlService.LIGHT_SVC_UUID)
        # self.add_service_uuid(LEDColourService.LED_SVC_UUID)

        self.add_local_name("LuminXLogic")
        self.include_tx_power = True

def register_ad_cb():
    logger.info("Advertisement registered")

def register_ad_error_cb(error):
    logger.critical("Failed to register advertisement: " + str(error))
    mainloop.quit()


AGENT_PATH = "/com/luminXGattServer/agent"


def terminate(signum, frame):
    ser.write(b'sleep\r\n')
    ser.close()
    for duty_cycle in range(10, -1, -1):
        gpwm.ChangeDutyCycle(duty_cycle)
        rpwm.ChangeDutyCycle(duty_cycle)
        bpwm.ChangeDutyCycle(duty_cycle)
        time.sleep(0.05)
    rpwm.stop()  # Stop PWM before cleanup
    gpwm.stop()
    bpwm.stop()
    print("Exiting...")
    logger.critical("Terminating program")
    ad_manager.UnregisterAdvertisement()
    service_manager.UnregisterApplication()
    mainloop.quit()
    return True
signal.signal(signal.SIGTERM, terminate)

def main():
    global mainloop

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    # get system bus
    bus = dbus.SystemBus()
    # get the ble controller
    adapter = find_adapter(bus)

    if not adapter:
        logger.critical("GattManager1 interface not found")
        return

    """
    --------------------------------------------------------------------
    ------------------------------ OBJECT ------------------------------
    --------------------------------------------------------------------
    """
    logger.info("------------------------------ OBJECT ------------------------------")

    adapter_obj = bus.get_object(BLUEZ_SERVICE_NAME, adapter)
    logger.info(f"adapter_obj created with path {adapter}")

    obj = bus.get_object(BLUEZ_SERVICE_NAME, "/org/bluez")
    logger.info(f"object was create with path {obj.__dbus_object_path__}")

    adapter_props = dbus.Interface(adapter_obj, "org.freedesktop.DBus.Properties")
    adapter_props.Set("org.bluez.Adapter1", "Powered", dbus.Boolean(1))
    logger.info(f"adapter_props created with interface {adapter_props.dbus_interface}")

    """
    --------------------------------------------------------------------
    ------------------------------ AGENT -------------------------------
    --------------------------------------------------------------------
    """
    logger.info("----------------------------- AGENT -------------------------------")

    # create agent manager
    agent_manager = dbus.Interface(obj, "org.bluez.AgentManager1")

    # create agent
    agent = Agent(bus, AGENT_PATH)
    logger.info(f"agent created with path {agent.__dbus_object_path__}")

    # register agent
    agent_manager.RegisterAgent(AGENT_PATH, "NoInputNoOutput")
    logger.info(f"agent_manager created with interface {agent_manager.dbus_interface}")

    agent_manager.RequestDefaultAgent(AGENT_PATH)

    """
    --------------------------------------------------------------------
    -------------------------- ADVERTISEMENTS --------------------------
    --------------------------------------------------------------------
    """
    logger.info("-------------------------- ADVERTISEMENTS --------------------------")

    # create add manager
    global ad_manager
    ad_manager = dbus.Interface(adapter_obj, LE_ADVERTISING_MANAGER_IFACE)
    logger.info(f"ad_manager created with interface {ad_manager.dbus_interface}")

    # create advertisement
    global advertisement
    advertisement = LuminXLogicAdvertisement(bus, 0)
    logger.info(f"advertisement created with path {advertisement.path} and type {advertisement.ad_type}")

    # register advertisement
    logger.info("Registering advertisement")
    ad_manager.RegisterAdvertisement(advertisement.path, {},
                                        reply_handler=register_ad_cb,
                                        error_handler=register_ad_error_cb)

    """
    --------------------------------------------------------------------
    ------------------------------ SERVICE -----------------------------
    --------------------------------------------------------------------
    """
    logger.info("------------------------------ SERVICE -----------------------------")

    # create service manager
    global service_manager
    service_manager = dbus.Interface(adapter_obj, GATT_MANAGER_IFACE)
    logger.info(f"service_manager created with interface {service_manager.dbus_interface}")

    # create application
    global app
    app = Application(bus)
    app.add_service(LightControlService(bus, 2))
    app.add_service(LEDColourService(bus, 3))
    logger.info("application created with services")

    # register service
    logger.info("Registering GATT application")
    service_manager.RegisterApplication(
        app.get_path(),
        {},
        reply_handler=register_app_cb,
        error_handler=register_app_error_cb,
    )
 

    control_thread = threading.Thread(target=control)
    control_thread.daemon = True  # Daemonize the thread so it exits when the main thread exits
    control_thread.start()
    logger.info("Run main loop")
    
    mainloop = MainLoop()
    mainloop.run()
    

if __name__ == "__main__":
    main()
    