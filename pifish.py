#!/usr/bin/python

import getpass
import sys

if getpass.getuser() != "root":
	print "Must run as root"
	sys.exit(1)

import pygame
from os import path
import time
import RPi.GPIO as gpio
import re
import logging as log
import threading

log.basicConfig(level=log.INFO, format="%(asctime)s %(levelname)-8s %(message)s", filename="pifish.log", buffer=1024)

_motors = {}
_sounds = {}
_channel = None
_initialized = False

def init(logLevel=log.INFO):
	global _initialized
	if not _initialized:
		global _motors
		global _channel

		gpio.setmode(gpio.BCM)

		pygame.mixer.init()
		_channel = pygame.mixer.Channel(1)
		_initialized = True
	
def isInitialized():
	global _initialized
	return _initialized

def cleanup():
	global _initialized
	if _initialized:
		global _motors
		global _sounds
		global _channel

		log.info("Cleaning up")
		if len(_motors) > 0:
			gpio.cleanup()
			_motors = {}
		_sounds = {}
		_channel = None
		_initialized = False
		log.info("Done cleaning up")
		

class IllegalArgumentException(ValueError):
	pass

# ###################################################################
# General abstract Action class
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
		self.description = ""

	def getTime(self):
		return self.time

	def getName(self):
		return self.name

	def getDescription(self):
		return self.description

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

# ###################################################################
# Represenation of fish motor
class Motor(object):
	def __init__(self, pin, name="undefined name"):
		global _motors
		self.__pin = pin
		self.__name = name
		gpio.setup(pin, gpio.OUT, pull_up_down=gpio.PUD_UP)
		_motors[pin] = self

	def getName(self):
		return self.__name

	def setPosition(self, position):
		log.debug("Moving [%d][%s] to %d" % (self.__pin, self.__name, position))
		gpio.output(self.__pin, position)

# ###################################################################
# Moves a given motor to the given position at the given time
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

# ###################################################################
# Plays the given sound at the given time
class SoundAction(_Action):
	def __init__(self, soundFile, time):
		if type(soundFile) is not str:
			raise IllegalArgumentException("Expected type [%s] but was [%s]"
					% (str, type(soundFile)))
		super(SoundAction, self).__init__(time)

		self.__soundFile = soundFile
		self.__sound = _getOrCreateSound(self.__soundFile)

	def getSound(self):
		return self.__sound

	def getSoundFile(self):
		return self.__soundFile

	def getDescription(self):
		return "Play sound [%s]" % self.getSoundFile()

	def run(self):
		global _channel
		_channel.play(self.getSound())
		#while _channel.get_busy():
		#	continue

	def __str__(self):
		return "sound(%s, %f)" % (self.getSoundFile(), self.getTime())

# ###################################################################
# Sets the volume of the Pi at the given time
class VolumeAction(_Action):
	def __init__(self, volume, time):
		if type(volume) is not float and type(volume) is not int:
			raise IllegalArgumentException("Expected type [%s] or [%s] but was [%s]"
					% (float, int, type(volume)))
		super(VolumeAction, self).__init__(time)

		self.__volume = volume

	def getVolume(self):
		return self.__volume

	def run(self):
		pygame.mixer.music.set_volume(self.__volume)

	def __str__(self):
		return "volume(%f, %f)" % (self.__volume, self.__time)

# ###################################################################
# Represents a configuration to be loaded for a future run
class Configuration(object):
	def __init__(self, configFile, priority = -1):
		if configFile is None or type(configFile) is not str:
			raise IllegalArgumentException("")
		self.__configFile = configFile
		self.__loadActions(configFile)
		self.__lock = threading.Lock()

	def __loadActions(self, configFile):
		self.__configFile = configFile
		log.info("Loading configuration [%s]" % configFile)
		f = open(configFile)

		motors = {}
		actions = []
		ignoreMotors = [] # Used when using a single fish to emulate multiple fish
		offset = 0.0
		for line in f:
			line = line.strip()
			ignoreMatch = re.search('^ignore\((\S+)\)$', line)
			if ignoreMatch:
				motorVar = ignoreMatch.group(1)
				ignoreMotors.append(motorVar)
				continue

			motorAction = re.search('^motorAction\((\S+),\s*(HIGH|LOW),\s*((\d+)(\.\d+))\)$', line)
			if motorAction:
				motorName = motorAction.group(1)
				rawPosition = motorAction.group(2).lower()
				time = float(motorAction.group(3)) + offset

				if motorName in ignoreMotors:
					continue
				
				try:
					motor = motors[motorName]
				except KeyError:
					raise IOError("Unrecognized motor [%s]" % motorName)

				if rawPosition == "high":
					position = gpio.HIGH
				else:
					position = gpio.LOW

				motorAction = MotorAction(motor, position, time)
				actions.append(motorAction)

			motorMatch = re.search('^(\S+)\s*=\s*?motor\((\d+)(,\s*"(.*)")\)$', line)
			if motorMatch:
				motorVar = motorMatch.group(1)
				motor = _getOrCreateMotor(int(motorMatch.group(2)), motorMatch.group(4))
				motors[motorVar] = motor

			soundMatch = re.search('^sound\("(.*)",\s*((\d+)(\.\d+))\)$', line)
			if soundMatch:
				time = float(soundMatch.group(2))
				sound = SoundAction(soundMatch.group(1), time + offset)
				actions.append(sound)

			offsetMatch = re.search('^offset\(((\d+)(\.\d+))\)$', line)
			if offsetMatch:
				time = float(offsetMatch.group(1))
				offset += time

			volumeMatch = re.search('^volume\(((\d+)(\.\d+)),\s*((\d+)(\.\d+))\)$', line)
			if volumeMatch:
				volume = float(volumeMatch.group(1))
				time = float(volumeMatch.group(2))
				actions.append(VolumeAction(volume, time))

			priorityMatch = re.search('priority\(((\d+)(\.\d+)?)\)', line)
			if priorityMatch:
				try:
					self.__priority
					raise IllegalArgumentException("Priority already set in [%s]" % self.__configFile)
				except AttributeError:
					log.info("Setting priority %s" % priorityMatch.group(1))
					self.__priority = float(priorityMatch.group(1))

		f.close()

		startTime = actions[0].getTime()
		endTime = actions[len(actions) - 1].getTime()
		self.__length = endTime - startTime

		try:
			self.__priority
		except AttributeError:
			actions.sort()
			log.info("Priority not set, setting to length [%f]" % self.__length)
			self.__priority = self.__length
		self.__actions = actions
		log.info("%s has priority %f" % (self.__configFile, self.__priority))
	
	def run(self):
		with self.__lock:
			runCommand(self.__actions)
	
	def isRunning(self):
		running = not self.__lock.acquire(False)
		if not running:
			self.__lock.release()
		return running
	
	def getConfigFile(self):
		return self.__configFile

	def getPriority(self):
		return self.__priority

	def getLength(self):
		return self.__length

	def setPriorityRange(self, min, max):
		self.__minRange = min
		self.__maxRange = max
	
	def getMinPriority(self):
		return self.__minRange
	
	def getMaxPriority(self):
		return self.__maxRange
	
	def isInRange(self, value):
		return value >= self.__minRange and value < self.__maxRange

def _timeSince(startTime):
	return time.time() - startTime

def _getOrCreateMotor(pin = None, name = None):
	if name is None and pin is None:
		raise IllegalArgumentException("name and pin is None")
	global _motors
	try:
		motorByPin = _motors[pin]
		return motorByPin
	except KeyError:
		if name is None:
			log.warn("Creating a motor without a name on pin [%s]" % pin)
		motor = Motor(pin, name)
		_motors[pin] = motor
		return motor

def _getOrCreateSound(soundFile):
	if soundFile is None:
		raise IllegalArgumentException("soundFile is null")
	if not path.isfile(soundFile):
		raise IOError("Unable to find sound file [%s]" % soundFile)
	global _sounds
	try:
		sound = _sounds[soundFile]
	except KeyError:
		sound = pygame.mixer.Sound(soundFile)
		_sounds[soundFile] = sound
	return sound

def runCommand(rawActions):
	actions = list(rawActions)
	actions.sort()

	#checkActions(actions)

	startTime = time.time()
	timeOffset = 0.0
	while len(actions) > 0:
		action = actions[0]
		curTime = _timeSince(startTime)
		if curTime >= (action.getTime() + timeOffset):
			log.info("[%f] running cmd [%s]"
					% (curTime, action.getDescription()))
			actions.pop(0)
			action.run()
	downAllMotors()

def downAllMotors():
	global _motors
	for pin in _motors:
		motor = _motors[pin]
		log.info("Downing motor [" + motor.getName() + "]")
		motor.setPosition(gpio.LOW)
