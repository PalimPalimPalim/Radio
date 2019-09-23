#!/usr/bin/env python3
import os
import csv
import vlc
import requests
from bs4 import BeautifulSoup
from functools import partial
import coverpy

# kivy imports
from kivy.config import Config
# Config.set('graphics', 'fullscreen', 'fake')
Config.set('graphics', 'resizable', 0)
from kivy.app import App
from kivy.uix.image import Image, AsyncImage
from kivy.uix.widget import Widget
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.behaviors.button import ButtonBehavior
from kivy.properties import StringProperty, BooleanProperty, ObjectProperty
from kivy.network.urlrequest import UrlRequest
from kivy.clock import Clock
from kivy.vector import Vector
from kivy.graphics.vertex_instructions import Triangle, Rectangle, Ellipse
from kivy.graphics.context_instructions import Color
from kivy.graphics.instructions import Callback, InstructionGroup
from kivy.core.window import Window


class HoverBehavior(object):
    """Hover behavior.
    :Events:
        `on_enter`
            Fired when mouse enter the bbox of the widget.
        `on_leave`
            Fired when the mouse exit the widget 
    Taken from https://gist.github.com/opqopq/15c707dc4cffc2b6455f
    """

    hovered = BooleanProperty(False)
    border_point= ObjectProperty(None)
    '''Contains the last relevant point received by the Hoverable. This can
    be used in `on_enter` or `on_leave` in order to know where was dispatched the event.
    '''

    def __init__(self, **kwargs):
        self.register_event_type('on_enter')
        self.register_event_type('on_leave')
        Window.bind(mouse_pos=self.on_mouse_pos)
        super(HoverBehavior, self).__init__(**kwargs)

    def on_mouse_pos(self, *args):
        if not self.get_root_window():
            return # do proceed if I'm not displayed <=> If have no parent
        pos = args[1]
        #Next line to_widget allow to compensate for relative layout
        inside = self.collide_point(*self.to_widget(*pos))
        if self.hovered == inside:
            #We have already done what was needed
            return
        self.border_point = pos
        self.hovered = inside
        if inside:
            self.dispatch('on_enter')
        else:
            self.dispatch('on_leave')

    def on_enter(self):
        pass

    def on_leave(self):
        pass


class CoverImage(AsyncImage):
    cover_info = StringProperty()
    cover_info_prev = StringProperty()

    def update_cover(self):
        if self.cover_info != self.cover_info_prev:
            
            cover = coverpy.CoverPy()
            try: 
                result = cover.get_cover(self.cover_info, 3)
                self.source = result.artwork(300)
                self.cover_info_prev = self.cover_info
            except:
                self.source = './ButtonImages/' + App.get_running_app().playing_image



class InfoLabel(Label):
    station = StringProperty()
    meta_info = StringProperty()
    
    def __init__(self, **kwargs):
        super(InfoLabel, self).__init__(**kwargs)
    
    def update_info(self):
        App.get_running_app().get_stream_info()



class PlayPauseButton(ButtonBehavior, Widget, HoverBehavior):
    status_play_pause = "paused"

    def __init__(self, **kwargs):
        super(PlayPauseButton, self).__init__(**kwargs)
        Clock.schedule_once(self._add_play_sign, 2)
        Clock.schedule_interval(self.check_status, 0.3)

    def collide_point(self, x, y):
        return Vector(x, y).distance(self.center) < self.width / 2

    def check_status(self, *largs):
        # retrieve if playing
        status = App.get_running_app().vlc_player.get_state()

        # change play/pause sign if is not like status
        if str(status) in ['State.Opening', 'State.Buffering','State.Playing']:
            if self.status_play_pause == "paused":
                self._remove_play_sign()
                self._add_pause_sign()
                self.status_play_pause = "playing"
        
        else:
            if self.status_play_pause == "playing":
                self._remove_pause_sign()
                self._add_play_sign()
                self.status_play_pause = "paused"

    def toggle(self):
        App.get_running_app().toggle()

    def _add_play_sign(self, *largs):
        self.play_sign = InstructionGroup()
        self.play_sign.add(Color(1, 1, 1, 1))
        self.play_sign.add(Triangle(points=[self.x + self.width * 0.35, self.y + self.height * 0.25, 
                                            self.x + self.width * 0.35, self.y + self.height * 0.75, 
                                            self.x + self.width * 0.75, self.y + self.height * 0.50]))
        self.canvas.after.add(self.play_sign)
    
    def _remove_play_sign(self):
        self.canvas.after.remove(self.play_sign)

    def _add_pause_sign(self):
        self.pause_sign = InstructionGroup()
        self.pause_sign.add(Color(1, 1, 1, 1))
        self.pause_sign.add(Rectangle(pos=(self.x + self.width * 0.35, self.y + self.height * 0.25), 
                                      size=(self.width * 0.1, self.height * 0.5)))
        self.pause_sign.add(Rectangle(pos=(self.x + self.width * 0.55, self.y + self.height * 0.25), 
                                      size=(self.width * 0.1, self.height * 0.5)))
        self.canvas.after.add(self.pause_sign)
    
    def _remove_pause_sign(self):
        self.canvas.after.remove(self.pause_sign)

    def _hover_add_background(self):
        self.background = InstructionGroup()
        self.background.add(Color(1,1,1,0.1))
        self.background.add(Ellipse(pos=self.pos, size=self.size))
        self.canvas.before.add(self.background)

    def _hover_remove_background(self):
        self.canvas.before.remove(self.background)




class ChannelGrid(GridLayout):
    pass

class RadioGrid(ChannelGrid):
    def __init__(self, **kwargs):
        super(RadioGrid, self).__init__(**kwargs)

        # add channels based on file stations.csv
        with open('stations.csv') as csvfile:
            station_reader = csv.reader(csvfile, delimiter=",")
            for row in station_reader:
                self.add_channel(*row)
    
    def add_channel(self, name: str, image: str, link: str, *args):
        self.add_widget(RadioButton(name, image, link))

class RadioButton(Button):
    name = StringProperty()
    image = StringProperty()
    link = StringProperty()
    description = StringProperty()

    def __init__(self, name: str, image: str, link: str, **kwargs):
        self.name = name
        self.image = image
        self.link = link
        self.description = kwargs.get('description','')
        super(RadioButton, self).__init__(**kwargs)

    def play_channel(self):
        App.get_running_app().play(self.link, image=self.image, name=self.name)

class DFNews(RadioButton):

    def __init__(self, **kwargs):
        super(DFNews, self).__init__(**kwargs)
        self.get_link()

    def play_channel(self):
        App.get_running_app().play(self.get_link())

    @staticmethod
    def get_link():
        url = 'http://www.deutschlandfunk.de/podcast-nachrichten.1257.de.podcast.xml'
        r = requests.get(url)
        begin = r.text.find("http://podcast-mp3.dradio.de/podcast/")
        end = r.text.find(".mp3", begin) + len(".mp3")
        podcast_url = r.text[begin:end]
        print(podcast_url)
        return(podcast_url)

class TVButton(RadioButton):

    def __init__(self, name: str, image: str, **kwargs):
        self.text = self.get_date()
        super(TVButton, self).__init__(name, image, '', **kwargs)
        Clock.schedule_once(self.check_videos_available)


    def get_date(self):
        files = [file for file in os.listdir("./videos") if self.name in file]
        dates = [file[0:8] for file in files]
        return(max(dates) if dates else '')

    def check_videos_available(self, *args):
        if self.text == "":
            self.parent.remove_widget(self)

    def play_channel(self):
        os.system("start ./videos/" + self.get_date() + self.name + ".mp4")



class NewsGrid(ChannelGrid):
    download_links = None

    def __init__(self, **kwargs):
        super(NewsGrid, self).__init__(**kwargs)
        # DF Nachrichten
        self.add_widget(DFNews(name='DF Nachrichten', image='deutschlandfunknachrichten.png', link=''))
        # Economist
        self.economist_search_links()

    
    def economist_search_links(self):
        url = "https://www.podbean.com/podcast-detail/jdhgv-2ef60/Economist-Radio-Podcast"
        UrlRequest(url, self.economist_found_links) # using kivys async requests
    
    def economist_found_links(self, request, html):
        soup = BeautifulSoup(html, "html.parser")
        download_buttons = soup.find_all("a", {"class": "download"}, href=True)
        for button_link in download_buttons:
             UrlRequest(button_link.get('href'), self.economist_found_streams) # using kivys async requests

    def economist_found_streams(self, request, html):
        soup = BeautifulSoup(html, "html.parser")
        link = soup.find_all("a", {"class": "btn btn-ios download-btn"}, href=True)[0].get('href')
        description = soup.find_all("p", {"class": "pod-name"})[0].get_text()
        self.add_widget(RadioButton('economist',
                                    self.economist_match_image(link), 
                                    link,
                                    description=description))
        
    @staticmethod
    def economist_match_image(link):
        if "theeconomistasks" in link:
            return("Economist_asks.jpeg")
        elif "theintelligence" in link:
            return("Economist_The_Intelligence.jpeg")
        elif "theeconomisteditorspicks" in link:
            return("Economist_Editors_Picks.jpeg")
        elif "theeconomistmoneytalks" in link:
            return("Economist_Money_talks.jpeg")
        elif "theeconomistbabbage" in link:
            return("Economist_Babbage.jpeg")
        else:
            return("Economist_Radio.png")
        
class VideoGrid(ChannelGrid):
    def __init__(self, **kwargs):
        super(VideoGrid, self).__init__(**kwargs)
        Clock.schedule_once(self.add_tagesthemen, 2)

    def add_tagesthemen(self, *args):
        self.add_widget(TVButton(name="tagesthemen", 
                                 image="tagesthemen.png",
                                 size_hint=(None, None),
                                 width=(Window.width - 2 * 5) / 6,
                                 height=(Window.width - 2 * 5) / 6)) # spacing inside channel grid is 5


class CloseMinimzeGrid(GridLayout, HoverBehavior):
    def children_add(self):
        self.add_widget(MinimizeButton(height=self.height))
        self.add_widget(CloseButton(height=self.height))

    def children_remove(self):
        self.clear_widgets()

class CloseButton(ButtonBehavior, Label, HoverBehavior):
    def close_app(self):
        App.get_running_app().stop()

class MinimizeButton(ButtonBehavior, Label, HoverBehavior):
    def minimize_app(self):
        App.get_running_app().root_window.minimize()


class RadioApp(App):
    station = StringProperty()
    meta_info = StringProperty()
    playing_name = StringProperty()
    playing_image = StringProperty()
    playing_description = StringProperty()


    def __init__(self, **kwargs):
        super(RadioApp, self).__init__(**kwargs)
        # start vlc for mp3 streaming
        self.vlc_inst = vlc.Instance()
        self.vlc_player = self.vlc_inst.media_player_new()
        
    def play(self, link='', **kwargs):
        if link:
            # play
            media = self.vlc_inst.media_new(link)
            media.get_mrl()
            self.vlc_player.set_media(media)

        self.playing_name = kwargs.get('name', '')
        self.playing_image = kwargs.get('image', '')
        
        print(link)
        
        self.vlc_player.play()
        
        Clock.schedule_interval(self.get_stream_info, 1)

    def get_stream_info(self, media, *largs):
        media = self.vlc_player.get_media()
        info = [media.get_meta(i) for i in range(30)]

        self.station = info[0] if info[0] else ''
        self.meta_info = info[12] if info[12] else ''

        if self.station.strip() == 'media.mp3':
            self.station = self.playing_description

        return(info)

    def toggle(self):
        self.vlc_player.pause()


    def build(self):
        Window.borderless = True

if __name__ == "__main__":
    RadioApp().run()
