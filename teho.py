#!/usr/bin/env python2.7
import RPi.GPIO as GPIO
import time
import os
GPIO.setmode(GPIO.BCM)

# Global variables
global lastSignal, lastTime, power, difference, powercap
lastSignal = False
lastTime = time.time()
power = 0
powercap = 100
difference = 0

# GPIO 26 set up as input, pulled down to avoid false detection.
# GPIO 26 connected to automationPhat input 1
# automation phat input 1 connected to LDR with a paraller resistor
# of ~40 kohm
GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# routine to calculate power and increase energy counter when pulse
# is detected
def pulsecallback(channel):
    global lastSignal, lastTime, power, difference
    oldcounter = 0
    counter = 0
    seconds_in_an_hour = 3600
    meter_constant = 1000
    print "falling edge detected on 26"
    newTime = time.time()
    difference = newTime - lastTime
    power = seconds_in_an_hour / (difference * meter_constant)
    if power > powercap: power = ""
    teho = round(power, 3)
    lastTime = newTime
    print power, difference

    tehofile = open("/ramdisk/teho.txt", "w")
    tehofile.write(str(teho))
    tehofile.close

    exists = os.path.isfile('/ramdisk/tehocounter.txt')

    if exists:
        counterfile = open("/ramdisk/tehocounter.txt", "r")
        oldcounter = counterfile.read()
        counterfile = open("/ramdisk/tehocounter.txt", "w")
    else:
        counterfile = open("/ramdisk/tehocounter.txt", "w")

    print oldcounter
    counter = int(oldcounter) + 1
    counterfile.write(str(int(oldcounter) + 1))
    counterfile.close


# when a falling edge is detected on port 26,
# the function pulsecallback will be run
# try adjusting bouncetime if you get ghost signals
# also try adjusting paraller/series resistor and reading
# input status with 
# $ GPIO READALL
GPIO.add_event_detect(26, GPIO.FALLING, callback=pulsecallback, bouncetime=300)

# main program loop.
# does nothing but sleeps all day
print "waiting for pulses in GPIO 26"
print "Use ctrl+z to interrupt"
try:
    while True:
        time.sleep(1e6)

except KeyboardInterrupt:
    GPIO.cleanup()       # clean up GPIO on CTRL+C exit
GPIO.cleanup()           # clean up GPIO on normal exit

