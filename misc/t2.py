#!/usr/bin/env python3

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivy.core.window import Window

from omxplayer.player import OMXPlayer

import os
from pathlib import Path
from time import sleep

class VideoBttn(Button):
    @staticmethod
    def clearbckgrnd():
        Window.clearcolor = (0,0,0,0)

    @staticmethod
    def addbckgrnd():
        Window.clearcolor = (0,0,0,1)

    def play(self):
        print('starting player')
        #os.system('killall dbus-daemon')
        Window.clearcolor = (1,0,0,0.5)
        VIDEO_PATH = Path("../videos/20200223tagesthemen.mp4")

        player = OMXPlayer(VIDEO_PATH, args=['-o', 'alsa'])#, '--layer',  '10000'])




class VideoApp(App):
    def build(self):
        print('clearing')
        Window.clearcolor = (1, 0, 1, 0)
        return Builder.load_string('''

VideoBttn:
    size_hint: (0.1, 0.1)
    on_press: self.play()

''')


if __name__ == "__main__":
    VideoApp().run()