# ledteho
A small python script to calculate power and energy from a pulsing 
led on your elecricity meter. Writes status data to /ramdisk.
You can change the save location by modifying the script to
your needs.

Example fstab line:

`tmpfs       /ramdisk tmpfs  defaults,size=20M,gid=33   0 0`

## Todo
- Add MQTT support
- Add configurable averaging function
