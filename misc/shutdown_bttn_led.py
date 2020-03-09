#!/usr/bin/env python3

from gpiozero import LED
from signal import pause

led = LED(26)
led.on()

pause()
