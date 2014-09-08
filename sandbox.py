#!/usr/bin/python

import pifish
import logging as log
import RPi.GPIO as gpio

log.basicConfig(filename="pifish.log", level=log.INFO)

log.info("Starting...")

body = pifish.Motor(18, "Body")
mouth = pifish.Motor(23, "Mouth")
tail = pifish.Motor(24, "Tail")

actions = [pifish.Action(body, gpio.HIGH, 0.0)]
actions.extend(pifish.createJitter(tail, 0.0, 0.5, 3.0))
actions.extend(pifish.createJitter(mouth, 0.0, 0.05, 3.0))

pifish.run(actions)

log.info("Goodbye")
