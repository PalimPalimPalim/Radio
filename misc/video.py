import subprocess
import os


from time import sleep

# https://github.com/willprice/python-omxplayer-wrapper
from omxplayer.player import OMXPlayer

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.properties import ObjectProperty, BooleanProperty

from kivy.core.window import Window

from kivy.clock import Clock
from pathlib import Path


class VideoPlayerScreen(Screen):
    slider = ObjectProperty()
    minimized = BooleanProperty(False)

    @staticmethod
    def clearbckgrnd():
        Window.clearcolor = (0,0,0,0)

    @staticmethod
    def addbckgrnd():
        Window.clearcolor = (0,0,0,1)

    def play(self):
        VIDEO_PATH = Path("../videos/20200223tagesthemen.mp4")

        self.player = OMXPlayer(VIDEO_PATH, args=['-o', 'alsa',  '--layer',  '10000'])
        #self.player = OMXPlayer('/home/pi/Documents/Radio/videos/20200223tagesthemen.mp4')
        self.player.set_video_pos(0,0,800,480)
        #self.player.hide_video()
        #self.player.show_video()
        self.player.set_alpha(100)
        self.set_slider()
        #Clock.schedule_once(self.quit, 20)
        Clock.schedule_interval(self.set_slider, 3)


    def playpause(self):
        self.player.play_pause()

    def quit(self, gg, **kwargs):
        self.player.quit()
        App.get_running_app().stop()


    def set_slider(self, *args):
        pos = self.player.position() # in seconds as int
        duration =  self.player.duration() # in seconds as float
        #return pos/duration
        self.slider.value_normalized = pos/duration
        #return 0.5

    def set_videopos(self, *args):
        pos = self.player.position() # in seconds as int
        duration =  self.player.duration() # in seconds as float
        if abs (pos/duration - self.slider.value_normalized) > 0.05:
            self.player.set_position(self.slider.value_normalized*duration)


    def change_size(self):
        # pass
        #width 800
        #height 480

        # check if crop as alternative

        if self.minimized:
            # self.player.set_video_pos(2,2,798,478)
            self.player.set_alpha(255)
        else:
            # self.player.set_video_pos(2,2,798,418)
            self.player.set_alpha(100)

        self.minimized = not self.minimized





class VideoApp(App):
    def build(self):
        return Builder.load_string('''
ScreenManager:
    Screen:
        Button:
            on_press: root.current = "video"
            on_press: self.enabled = False
    VideoPlayerScreen:

<VideoPlayerScreen>:
    slider: slider
    name: "video"
    on_enter: self.clearbckgrnd()
    on_enter: self.play()
    on_pre_leave: self.addbckgrnd()
    BoxLayout:
        orientation: 'vertical'
        Button:
            size_hint_y: 420
            #text: "play"
            on_press: print('button to minimize pressed')
            on_press: root.change_size()
            background_color: (0,0,0,1)
            # Image:
            #     source: './Infinity.gif'
            #     height: self.parent.height / 1.5 
            #     y: self.parent.y + self.parent.height /2 - self.height / 2
            #     x: self.parent.x + self.parent.width / 2 - self.width / 2
            #     allow_stretch: False
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 60
            Slider:
                id: slider
                on_value: root.set_videopos(self.value_normalized)
                #value_normalized: root.set_slider
            BoxLayout:
                Button:
                    text: 'Play/Pause'
                    on_press: root.playpause()

''')

if __name__ == "__main__":
    #os.system('killall dbus-daemon')
    video = VideoApp()
    try:
        video.run()
    except KeyboardInterrupt:
        video.stop()
        os.system('killall dbus-daemon')