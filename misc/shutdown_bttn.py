#!/usr/bin/env python3

from gpiozero import Button
from subprocess import check_call
from signal import pause
from time import sleep

shutdown_btn = Button(3)
shutdown_btn.when_pressed = lambda : check_call(['sudo', 'poweroff'])

pause()
