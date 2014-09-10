#!/usr/bin/python

print "Begin imports"
import pifish
import logging as log
import RPi.GPIO as gpio

print "Loading logging configuration"
#log.basicConfig(filename="pifish.log", level=log.INFO)
log.basicConfig(level=log.INFO)

log.info("Starting...")
pifish.init()

log.info("Loading config...")
actions = pifish.loadConfigFile("config/grim_grinning_ghosts.conf")

print "Ready"
raw_input()
pifish.runCommand(actions)

#body = pifish.Motor(18, "Body")
#mouth = pifish.Motor(23, "Mouth")
#tail = pifish.Motor(24, "Tail")
#
#actions = [
#	pifish.SoundAction("sounds/music/grim_grinning_ghosts.mp3", 0.0)
#]
#actions.extend(pifish.createJitter(tail, 0.0, 0.25, 60.0))
##actions.extend(pifish.createJitter(tail, 0.0, 0.2, 3.0))
#
#pifish.runCommand(actions)

log.info("Goodbye")
