# ledteho
A small python script to calculate power and energy from a pulsing 
led on your elecricity meter. Sends measurement data by MQTT allowing easy integration
to a system supporting MQTT such as [Home Assistant](https://www.home-assistant.io/).
Optionally writes status data to files.
You can change the save location by modifying the config file to
your needs.

Example fstab line for ramdisk:

`tmpfs       /ramdisk tmpfs  defaults,size=20M,gid=33   0 0`

## Todo
- Add configurable averaging function
- Make config handling better

## inspired by

- https://raspi.tv/2013/how-to-use-interrupts-with-python-on-the-raspberry-pi-and-rpi-gpio
- https://github.com/sjmelia/pi-electricity-monitor
