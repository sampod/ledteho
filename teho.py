#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time
import os
import paho.mqtt.client as mqtt

GPIO.setmode(GPIO.BCM)

# Global variables
global lastSignal, lastTime, power, difference, powercap, counter
lastSignal = False
lastTime = time.time()
power = 0
powercap = 100
difference = 0

# files
tehofile = "/ramdisk/teho.txt"
counterfile = "/ramdisk/tehocounter.txt"

# GPIO 26 set up as input, pulled down to avoid false detection.
# GPIO 26 connected to automationPhat input 1
# automation phat input 1 connected to LDR with a paraller resistor
# of ~40 kohm
GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# routine to calculate power and increase energy counter when pulse
# is detected
def pulsecallback(channel):
    global lastSignal, lastTime, power, difference, counter
    seconds_in_an_hour = 3600
    meter_constant = 1000
    print ("falling edge detected on 26")
    newTime = time.time()
    difference = newTime - lastTime
    power = seconds_in_an_hour / (difference * meter_constant)
    if power > powercap: power = ""
    lastTime = newTime
    print (power, difference)
    counter = int(counter) + 1
    print (counter)

# routine to write stuff to file 
# called in main loop on regular basis!
def writetofile():
    global power, counter
    global tehofile, counterfile

    teho = round(power, 3)

    print ("writing...")

    with open(tehofile, "w") as f:
        f.write(str(teho))

    with open(counterfile, "w") as f:
        f.write(str(counter))

# MQTT-lähetys
def mqttsend():
    global power, counter
    teho = round(power, 3)
    client =mqtt.Client("ledteho")
    client.connect("192.168.1.13")
    client.publish("homeassistant/sensor/teho/state",teho)
    print("mqtt power sent")
    client.publish("homeassistant/sensor/tehocounter/state",counter)
    print("mqtt counter sent")
    time.sleep(1)
    client.disconnect()

# laskurin alustus

exists = os.path.isfile(counterfile)

if exists:
    with open(counterfile, "r") as f:
        counter = f.read()
else:
    counter = 0

# when a falling edge is detected on port 26,
# the function pulsecallback will be run
# try adjusting bouncetime if you get ghost signals
# also try adjusting paraller/series resistor and reading
# input status with 
# $ GPIO READALL
GPIO.add_event_detect(26, GPIO.FALLING, callback=pulsecallback, bouncetime=300)

# main program loop.
# does nothing but sleeps all day
print ("waiting for pulses in GPIO 26")
print ("Use ctrl+z to interrupt")
try:
    while True:
        time.sleep(10)
# uncomment to enable writing to files
#        writetofile()
        mqttsend()

except KeyboardInterrupt:
    GPIO.cleanup()       # clean up GPIO on CTRL+C exit
    writetofile()
GPIO.cleanup()           # clean up GPIO on normal exit
writetofile()
