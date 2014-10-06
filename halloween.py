#!/usr/bin/python

import atexit
import logging as log
import pifish
import time
import os
import random
import collections
import threading
import RPi.GPIO as gpio

def __onExit():
	pifish.cleanup()

def __getConfigFilesFromFolder(folder):
	files = []
	for filename in os.listdir(folder):
		if not filename.endswith(".conf"):
			continue
		files.append("%s/%s" % (folder, filename))
	return files

def __loadConfigs(folder):
	files = __getConfigFilesFromFolder(folder)
	configs = []
	for file in files:
		conf = pifish.Configuration(file)
		configs.append(conf)
	return configs

def __byPriority(item):
	return item.getPriority()

def __setPriorityRanges(configs):
	priorities = []
	
	for config in configs:
		priorities.append(config.getPriority())
	
	priorities.sort()
	sortedConfigs = sorted(configs, key=__byPriority, reverse=True)
	
	minRange = 0
	maxRange = 0
	totalConfigPriority = 0
	for i in range(0, len(configs)):
		priority = priorities[i]
		maxRange += priority
		sortedConfigs[i].setPriorityRange(minRange, maxRange)
		minRange += priority
		totalConfigPriority += priority
	
	for config in sortedConfigs:
		print "(%f-%f) - %s" % (config.getMinPriority(), config.getMaxPriority(), config.getConfigFile())
	
	print "Total priority range: %f" % totalConfigPriority
	return totalConfigPriority

_previousConfigs = collections.deque(maxlen=10)

def __getConfig():
	while True:
		value = random.random() * totalConfigPriority
		for config in configs:
			if config in _previousConfigs:
				continue
			if config.isInRange(value):
				#print "%d -> %s" % (value, config.getConfigFile())
				_previousConfigs.append(config)
				print _previousConfigs
				return config

_lock = threading.Lock()
_runningConfig = None
_minSleep = 5.0
_maxSleep = 45.0
_sleepTime = _minSleep
_sleepIncrease = 5
_sleepDecrease = 0.1
_sleepThreadTime = 0.5

def __motion():
	global _lock, _runningConfig
	if _lock.acquire(False):
		try:
			if _runningConfig.isRunning():
				print "config is still running"
				return
			else:
				thread = threading.Thread(target=__runNewConfig)
				thread.daemon = True
				thread.start()
		except AttributeError:
			thread = threading.Thread(target=__runNewConfig)
			thread.daemon = True
			thread.start()
	else:
		print "Unable to acquire lock"

def __runNewConfig():
	global _runningConfig, _lock, _sleepTime, _sleepIncrease

	try:
		config = __getConfig()
		_runningConfig = config
		print "Running [%s]" % config.getConfigFile()
		config.run()
		print "Sleeping [%f]" % _sleepTime
		time.sleep(_sleepTime)
		print "Done sleeping"
		__increaseSleepTime()
		_lock.release()
	except:
		_lock.release()

def __increaseSleepTime():
	global _sleepTime, _sleepIncrease

	if (_sleepTime + _sleepIncrease > _maxSleep):
		_sleepTime = _maxSleep
	else:
		_sleepTime += _sleepIncrease

def __sleepAdjustThread():
	global _sleepThreadTime
	while True:
		__decreaseSleepTime()
		time.sleep(_sleepThreadTime)

def __decreaseSleepTime():
	global _sleepTime, _sleepDecrease, _minSleep, _runningConfig, _lock

	_lock.acquire()
	_lock.release()
	
	if _sleepTime - _sleepDecrease < _minSleep:
		_sleepTime = _minSleep
	else:
		_sleepTime -= _sleepDecrease
	print "Sleep time decreased to [%f]" % _sleepTime

atexit.register(__onExit)

log.info("Initializing...")
pifish.init()

print "Loading configurations..."
configs = __loadConfigs("config")
totalConfigPriority = __setPriorityRanges(configs)
print "Done loading configuration. Beginning main control loop"

motionSensorPin = 26

gpio.setup(motionSensorPin, gpio.IN, pull_up_down=gpio.PUD_UP)
gpio.add_event_detect(motionSensorPin, gpio.RISING, callback=__motion)

sleepTimeAdjustThread = threading.Thread(target=__sleepAdjustThread)
sleepTimeAdjustThread.daemon = True
sleepTimeAdjustThread.start()

while True:
	raw_input("Waiting for user signal")
	__motion()

#configChoices = {}
#for i in range(0, 5000):
#	config = __getConfig()
#	try:
#		configChoices[config] = configChoices[config] + 1
#	except KeyError:
#		configChoices[config] = 1
#
#sortedConfigs = sorted(configs, key=__byPriority)
#
#for config in sortedConfigs:
#	print "%s -> %d" % (config.getConfigFile(), configChoices[config])
#
#print "Goodbye"
