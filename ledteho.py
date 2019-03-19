#!/usr/bin/env python3
import configparser
import os
import statistics
import time

import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO

# initialize config
config = configparser.ConfigParser()
config.read("ledteho.conf")
# read variables from config
ldrpin = config.getint('general', 'gpio')
meter_constant = config.getint('general', 'meter_constant')
powercap = config.getint('general', 'powercap')
sleeptime = config.getint('general', 'interval')
decimals = config.getint('general', 'decimals')
writetofilevar = config.getint('files', 'writetofile')
tehofile = config.get("files", "powerfile")
counterfile = config.get("files", "counterfile")
mqttaddress = config.get("mqtt", "address")
mqtttopic1 = config.get("mqtt", "ledtehotopic")
mqtttopic2 = config.get("mqtt", "ledtehocountertopic")
mqtttopic1m = config.get("mqtt", "ledtehomediantopic")

GPIO.setmode(GPIO.BCM)

# Global variables
global lastSignal, lastTime, power, difference, counter
lastSignal = False
lastTime = time.time()
power = 0
powerlist = []
difference = 0

# GPIO [ldrpin] set up as input, pulled down to avoid false detection.
# Automationphat may also be used pinout -> https://pinout.xyz/pinout/automation_phat
# Automation phat input connected to LDR with a paraller resistor
# of ~40 kohm. Or you can use for exaple pre-built arduino LDR-module wired
# directly to RPi GPIO.
GPIO.setup(ldrpin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Routine to calculate power and increase energy counter when pulse
# is detected.
def pulsecallback(channel):
    global lastSignal, lastTime, power, powerlist, difference, counter
    seconds_in_an_hour = 3600
    print ("falling edge detected on", ldrpin)
    newTime = time.time()
    difference = newTime - lastTime
    power = seconds_in_an_hour / (difference * meter_constant)
    powerlist.append(power)
    if power > powercap: power = ""
    lastTime = newTime
    print (power, difference)
    counter = int(counter) + 1
    print (counter)

# Routine to write stuff to file
# called in main loop on regular basis!
def writetofile():
    global power, counter
    global tehofile, counterfile

    teho = round(power, decimals)

    print ("files writing...")

    with open(tehofile, "w") as f:
        f.write(str(teho))

    with open(counterfile, "w") as f:
        f.write(str(counter))

# MQTT-sending
# Calculate median for measured power values and send median and latest values
# and counter value to MQTT broker
def mqttsend():
    global power, powerlist, counter
    teho = round(power, decimals)
    if len(powerlist) > 0:
      tehomedian = round(statistics.median(powerlist), decimals)
    else:
      tehomedian = 0
    powerlist = []
    client =mqtt.Client("ledteho")
    print (tehomedian)
    try:
      client.connect(mqttaddress)
      client.publish(mqtttopic1,teho)
      print("mqtt power sent")
      client.publish(mqtttopic1m,tehomedian)
      print("mqtt median power sent")
      client.publish(mqtttopic2,counter)
      print("mqtt counter sent")
      client.loop(2)
      client.disconnect()
      client.loop(2)
    except:
      print("MQTT connetion error")

# counter initialization

exists = os.path.isfile(counterfile)

if exists:
    with open(counterfile, "r") as f:
        counter = f.read()
else:
    counter = 0

# GPIO initialization:
# When a falling edge is detected on port [ldrpin],
# the function pulsecallback will be run
# try adjusting bouncetime if you get ghost signals
# also try adjusting paraller/series resistor and reading
# input status with
# $ GPIO READALL
GPIO.add_event_detect(ldrpin, GPIO.FALLING, callback=pulsecallback, bouncetime=300)

# main program loop.
# Call mqtt sending and optinally writing to file at interval configured
# in sleep function
print ("waiting for pulses in GPIO", ldrpin)
print ("Use ctrl+c to interrupt")
try:
    while True:
        time.sleep(sleeptime)
        if writetofilevar == 1:
          writetofile()
        mqttsend()

except KeyboardInterrupt:
    GPIO.cleanup()       # clean up GPIO on CTRL+C exit
    writetofile()
GPIO.cleanup()           # clean up GPIO on normal exit
writetofile()
