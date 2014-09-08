#!/usr/bin/python

import atexit
import logging as log
import RPi.GPIO as gpio
import time

_Motor__motors = []

# Register the exit listener first in case any of the following code fails to compile or run
def __onExit():
	for motor in _Motor__motors:
		log.info("Downing motor [" + motor.getName() + "]")
		motor.setPosition(gpio.LOW)
	gpio.cleanup()
	log.info("Cleanup complete. Exiting.")

atexit.register(__onExit)

class IllegalArgumentException(ValueError):
	pass

class Motor(object):
	def __init__(self, pin, name="undefined name"):
		global __motors
		self.__pin = pin
		self.__name = name
		gpio.setmode(gpio.BCM)
		gpio.setup(pin, gpio.OUT, pull_up_down=gpio.PUD_UP)
		__motors.append(self)
	
	def getName(self):
		return self.__name
	
	def setPosition(self, position):
		gpio.output(self.__pin, position)

class Action(object):
	def __init__(self, motor, position, time):
		if type(motor) is not Motor:
			raise IllegalArgumentException("Expected type [%s] but was [%s]"
					% (Motor, type(motor)))
		self.__motor = motor
		self.__position = position
		self.__time = time
	
	def getMotorName(self):
		return self.__motor.getName()
	
	def getPosition(self):
		return self.__position

	def getTime(self):
		return self.__time
	
	def run(self):
		self.__motor.setPosition(self.__position)
	
	def __lt__(self, other):
		return self.__time < other.__time
	
	def __gt__(self, other):
		return self.__time > other.__time

	def __eq__(self, other):
		return self.__time == other.__time
	
	def __ne__(self, other):
		return self.__time != other.__time

def timeSince(startTime):
	return time.time() - startTime

def run(rawActions):
	actions = list(rawActions)
	actions.sort()

	startTime = time.time()
	while len(actions) > 0:
		action = actions[0]
		curTime = timeSince(startTime)
		if curTime >= action.getTime():
			log.info("[%f] running cmd [%s, %d]" 
					% (curTime, action.getMotorName(), action.getPosition()))
			actions.pop(0)
			action.run()

def createJitter(motor, startTime, timeIncrement, endTime):
	actions = []
	t = startTime
	high = True
	while t <= endTime:
		if high:
			position = gpio.HIGH
		else:
			position = gpio.LOW
		actions.append(Action(motor, position, t))
		t += timeIncrement
		high = not high
	return actions
