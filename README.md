pifish
======

A simple library for controlling one or more Big Mouth Billy Bass.

This library was conceived from the idea of creating a Halloween prop in which one or more Big Mouth Billy Bass singing fish would be able to sing Halloween songs and play amusing or 'scary' Halloween sound effects. All the while, the fish themselves would be able to mimic the songs/sounds.

The basic configuration is using a Raspberry Pi with the GPIO pins controlling the motors. The fish's speakers are not used. However, the Pi's built in audio jack is.

Additional information on the wiring and construction can be found in the schematics/ folder.

Tools necessary to build a controllable Big Mouth Billy Bass (more detail needed):
1x Big Mouth Billy Bass (multiple can be controlled with this library)
1x Raspberry Pi (Model B or B+ preferred, but not required)
Single Core Wire (22 gauge or smaller is recommended)
Soldering Iron
Solder
3x ~217 milli-ohm resistors (one for each motor)

Optional:
GPIO breakout board for connecting the Raspberry Pi's GPIO pins to a breadboard
