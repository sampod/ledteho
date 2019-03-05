#!/usr/bin/env python3
import configparser
import RPi.GPIO as GPIO
import time
import os
import paho.mqtt.client as mqtt

# initialize config
config = configparser.ConfigParser()
config.read("ledteho.conf")
#read variables from config
ledpin = config.getint('general', 'gpio')
meter_constant = config.getint('general', 'meter_constant')
powercap = config.getint('general', 'powercap')
sleeptime = config.getint('general', 'interval')
decimals = config.getint('general', 'decimals')
tehofile = config.get("files", "powerfile")
counterfile = config.get("files", "counterfile")
mqttaddress = config.get("mqtt", "address")
mqtttopic1 = config.get("mqtt", "ledtehotopic")
mqtttopic2 = config.get("mqtt", "ledtehocountertopic")

GPIO.setmode(GPIO.BCM)

# Global variables
global lastSignal, lastTime, power, difference, counter
lastSignal = False
lastTime = time.time()
power = 0
difference = 0

# files

# GPIO [ledpin] set up as input, pulled down to avoid false detection.
# GPIO [ledpin] connected to automationPhat input 1
# automation phat input 1 connected to LDR with a paraller resistor
# of ~40 kohm. Or you can use for exaple pre-built arduino LDR-module.
GPIO.setup(ledpin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# routine to calculate power and increase energy counter when pulse
# is detected
def pulsecallback(channel):
    global lastSignal, lastTime, power, difference, counter
    seconds_in_an_hour = 3600
    print ("falling edge detected on", ledpin)
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

    teho = round(power, decimals)

    print ("writing...")

    with open(tehofile, "w") as f:
        f.write(str(teho))

    with open(counterfile, "w") as f:
        f.write(str(counter))

# MQTT-sending
def mqttsend():
    global power, counter
    teho = round(power, decimals)
    client =mqtt.Client("ledteho")
    try:
      client.connect(mqttaddress)
      client.publish(mqtttopic1,teho)
      print("mqtt power sent")
      client.publish(mqtttopic2,counter)
      print("mqtt counter sent")
      client.loop(2)
      client.disconnect()
      client.loop(2)
    except:
      print("conn. error")

# counter initialization

exists = os.path.isfile(counterfile)

if exists:
    with open(counterfile, "r") as f:
        counter = f.read()
else:
    counter = 0

# when a falling edge is detected on port [ledpin],
# the function pulsecallback will be run
# try adjusting bouncetime if you get ghost signals
# also try adjusting paraller/series resistor and reading
# input status with 
# $ GPIO READALL
GPIO.add_event_detect(ledpin, GPIO.FALLING, callback=pulsecallback, bouncetime=300)

# main program loop.
# call mqtt sending and optinally writing to file at interval configured
# in sleep function
print ("waiting for pulses in GPIO", ledpin)
print ("Use ctrl+c to interrupt")
try:
    while True:
        time.sleep(sleeptime)
# uncomment to enable writing to files
#        writetofile()
        mqttsend()

except KeyboardInterrupt:
    GPIO.cleanup()       # clean up GPIO on CTRL+C exit
    writetofile()
GPIO.cleanup()           # clean up GPIO on normal exit
writetofile()
