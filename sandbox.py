#!/usr/bin/python

print "Begin imports"
import pifish
import logging as log
import RPi.GPIO as gpio
import time
import os.path

print "Loading logging configuration"
#log.basicConfig(filename="pifish.log", level=log.INFO)
log.basicConfig(level=log.INFO)

log.info("Starting...")
pifish.init()

log.info("Loading config...")
actions = []
#actions.append(pifish.loadConfigFile("config/grim_grinning_ghosts.conf"))
#actions.append(pifish.loadConfigFile("config/vincent_price_evil_laugh.conf"))
#actions.append(pifish.loadConfigFile("config/addams_family.conf"))
#actions.append(pifish.loadConfigFile("config/dog_barking.conf"))
#actions.append(pifish.loadConfigFile("config/laughing_kookaburra.conf"))
#actions.append(pifish.loadConfigFile("config/laughing01.conf"))
#actions.append(pifish.loadConfigFile("config/laughing02.conf"))
#actions.append(pifish.loadConfigFile("config/laughing03.conf"))
#actions.append(pifish.loadConfigFile("config/laughing04.conf"))
#actions.append(pifish.loadConfigFile("config/wilhelm_scream.conf"))
#actions.append(pifish.loadConfigFile("config/scream01.conf"))

oldConfig = ""
while True:
	try:
		config = raw_input("Config: ")
		if config == "exit":
			break
		
		if config == "":
			config = oldConfig
		else:
			oldConfig = config
	
		if os.path.isfile("config/" + config + ".conf"):
			config = "config/" + config + ".conf"
		elif os.path.isfile("config/" + config):
			config = "config/" + config
		elif os.path.isfile(config + ".conf"):
			config = confi + ".conf"
		elif not os.path.isfile(config):
			print "Invalid config [%s]: file not found" % config
			continue
	
		actions = pifish.loadConfigFile(config)
		pifish.runCommand(actions)
	except e:
		print e

#print "Ready"
#raw_input()
##wait_time = 5
##for i in range(0,wait_time):
##	print wait_time - i
##	time.sleep(1)
#
#for action in actions:
#	pifish.runCommand(action)
#	if action != actions[-1]:
#		time.sleep(2)

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
