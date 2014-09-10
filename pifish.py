#!/usr/bin/python

import atexit
import logging as log
import re
import RPi.GPIO as gpio
import time
import pygame

motors = []
initialized = False

# Register the exit listener first in case any of the following code fails to compile or run
def __onExit():
	global initialized
	global motors
	if initialized == True:
		print "cleaning up..."
		for motor in motors:
			log.info("Downing motor [" + motor.getName() + "]")
			motor.setPosition(gpio.LOW)
		gpio.cleanup()
	log.info("Cleanup complete. Exiting.")

atexit.register(__onExit)

def init():
	global initialized
	if initialized:
		log.warn("Already initialized pifish")
		return
	log.info("Initializing pifish...")
	gpio.setmode(gpio.BCM)
	pygame.mixer.init()
	initialized = True
	log.info("Initialization complete")

class IllegalArgumentException(ValueError):
	pass

class Motor(object):
	def __init__(self, pin, name="undefined name"):
		global motors
		self.__pin = pin
		self.__name = name
		gpio.setup(pin, gpio.OUT, pull_up_down=gpio.PUD_UP)
		motors.append(self)
	
	def getName(self):
		return self.__name
	
	def setPosition(self, position):
		gpio.output(self.__pin, position)

class _Action(object):
	def __init__(self, time, name=""):
		if type(name) is not str:
			raise IllegalArgumentException("Expected type [%s] but was [%s]"
					% (str, type(name)))
		if type(time) is not float:
			raise IllegalArgumentException("Expected type [%s] but was [%s]"
					% (float, type(time)))
		if name == "":
			self.name = self.__class__.__name__
		else:
			self.name = name
		self.time = time
	
	def getTime(self):
		return self.time
	
	def getName(self):
		return self.name
	
	def getDescription(self):
		return ""

	def run(self):
		raise Exception("Cannot run abstract Action")

	def __lt__(self, other):
		return self.time < other.time
	
	def __gt__(self, other):
		return self.time > other.time

	def __eq__(self, other):
		return self.time == other.time
	
	def __ne__(self, other):
		return self.time != other.time

class MotorAction(_Action):
	def __init__(self, motor, position, time):
		if type(motor) is not Motor:
			raise IllegalArgumentException("Expected type [%s] but was [%s]"
					% (Motor, type(motor)))
		if type(position) is not int:
			raise IllegalArgumentException("Expected type [%s] but was [%s]"
					% (int, type(position)))
		super(MotorAction, self).__init__(time)

		self.__motor = motor
		self.__position = position
	
	def getMotorName(self):
		return self.__motor.getName()
	
	def getName(self):
		return getMotorName()
	
	def getPosition(self):
		return self.__position
	
	def getDescription(self):
		return "Motor [%s] to [%d]" % (self.getMotorName(), self.getPosition())

	def run(self):
		self.__motor.setPosition(self.__position)

	def __str__(self):
		return "motor(%s, %d, %f)" % (self.getMotorName(), self.getPosition(), self.getTime())
	

class SoundAction(_Action):
	def __init__(self, soundFile, time):
		if type(soundFile) is not str:
			raise IllegalArgumentException("Expected type [%s] but was [%s]"
					% (str, type(soundFile)))
		super(SoundAction, self).__init__(time)
		
		self.__soundFile = soundFile

	def getSoundFile(self):
		return self.__soundFile

	def getDescription(self):
		return "Play sound [%s]" % self.getSoundFile()

	def run(self):
		pygame.mixer.music.load(self.__soundFile)
		pygame.mixer.music.play()

	def __str__(self):
		return "sound(%s, %f)" % (self.getSoundFile(), self.getTime())

def timeSince(startTime):
	return time.time() - startTime

def runCommand(rawActions):
	actions = list(rawActions)
	actions.sort()

	checkActions(actions)

	startTime = time.time()
	timeOffset = 0.0
	while len(actions) > 0:
		action = actions[0]
		curTime = timeSince(startTime)
		if curTime >= (action.getTime() + timeOffset):
			log.info("[%f] running cmd [%s]" 
					% (curTime, action.getDescription()))
			actions.pop(0)
			if type(action) is SoundAction:
				st = time.time()
				action.run()
				et = time.time()
				timeOffset += et - st
				log.info("offset: %f" % timeOffset)
			else:
				action.run()

# Type check the list of actions
def checkActions(actions):
	for action in actions:
		if type(action) is not MotorAction and type(action) is not SoundAction:
			raise IllegalArgumentException("Invalid action type [%s]" % type(action))

def loadConfigFile(filename):
	if type(filename) is not str:
		raise IllegalArgumentException("filename is not a string")
	f = open(filename)
	motors = dict()
	actions = []
	offset = 0.0
	for line in f:
		line = line.strip()
		if line.startswith("#") or not line:
			continue

		motorAction = re.search('^motorAction\((\S+),\s*(HIGH|LOW),\s*((\d+)(\.\d+))\)$', line)
		if motorAction:
			motorName = motorAction.group(1)
			rawPosition = motorAction.group(2).lower()
			time = float(motorAction.group(3)) + offset

			motor = motors[motorName]
			if motor is None:
				raise IOError("Unrecognized motor [%s]" % motorName)

			if rawPosition == "high":
				position = gpio.HIGH
			else:
				position = gpio.LOW

			motorAction = MotorAction(motor, position, time)
			actions.append(motorAction)
			continue
		
		motorMatch = re.search('^(\S+)\s*=\s*?motor\((\d+),\s*"(.*)"\)$', line)
		if motorMatch:
			motorVar = motorMatch.group(1)
			motor = Motor(int(motorMatch.group(2)), motorMatch.group(3))
			motors[motorVar] = motor
			continue

		soundMatch = re.search('^sound\("(.*)",\s*((\d+)(\.\d+))\)$', line)
		if soundMatch:
			time = float(soundMatch.group(2))
			sound = SoundAction(soundMatch.group(1), time + offset)
			actions.append(sound)
			continue

		offsetMatch = re.search('^offset\(((\d+)(\.\d+))\)$', line)
		if offsetMatch:
			time = float(offsetMatch.group(1))
			offset += time
			continue

	f.close()
	return actions

def createJitter(motor, startTime, timeIncrement, endTime):
	actions = []
	t = startTime
	high = True
	while t <= endTime:
		if high:
			position = gpio.HIGH
		else:
			position = gpio.LOW
		actions.append(MotorAction(motor, position, t))
		t += timeIncrement
		high = not high
	return actions
