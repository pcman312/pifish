#!/usr/bin/python

import fish
import logging as log
import RPi.GPIO as gpio

log.basicConfig(filename="fish.log", level=log.INFO)

log.info("Starting...")

body = fish.Motor(18, "Body")
mouth = fish.Motor(23, "Mouth")
tail = fish.Motor(24, "Tail")

actions = [fish.Action(body, gpio.HIGH, 0.0)]
actions.extend(fish.createJitter(tail, 0.0, 0.5, 3.0))
actions.extend(fish.createJitter(mouth, 0.0, 0.05, 3.0))

fish.run(actions)

log.info("Goodbye")
