#!/usr/bin/python

import atexit
import logging as log
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
	
	def __lt__(self, other):
		if other is None:
			return False
		return self.time < other.time
	
	def __gt__(self, other):
		return self.time > other.time

	def __eq__(self, other):
		return self.time == other.time
	
	def __ne__(self, other):
		return self.time != other.time

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

	def __lt__(self, other):
		return self.time < other.time
	
	def __gt__(self, other):
		return self.time > other.time

	def __eq__(self, other):
		return self.time == other.time
	
	def __ne__(self, other):
		return self.time != other.time

def timeSince(startTime):
	return time.time() - startTime

def run(rawActions):
	actions = list(rawActions)
	actions.sort()

	checkActions(actions)

	startTime = time.time()
	while len(actions) > 0:
		action = actions[0]
		curTime = timeSince(startTime)
		if curTime >= action.getTime():
			log.info("[%f] running cmd [%s]" 
					% (curTime, action.getDescription()))
			actions.pop(0)
			action.run()

# Type check the list of actions
def checkActions(actions):
	for action in actions:
		if type(action) is not MotorAction and type(action) is not SoundAction:
			raise IllegalArgumentException("Invalid action type [%s]" % type(action))

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
