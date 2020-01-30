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
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.uix.behaviors.button import ButtonBehavior
from kivy.uix.modalview import ModalView
from kivy.properties import StringProperty, BooleanProperty, ObjectProperty, ListProperty, NumericProperty
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
        Clock.schedule_once(self._add_play_sign, 4)
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
    name = StringProperty('DF Nachrichten')
    image = StringProperty('deutschlandfunknachrichten.png')

    def __init__(self, **kwargs):
        super(DFNews, self).__init__(name=self.name, image=self.image, link="",**kwargs)


    def play_channel(self):
        self.link = self.get_link()
        super(DFNews, self).play_channel()


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

class PodcastBttn(Button):
    streaming_links = ListProperty()
    descriptions = ListProperty()
    timestamps = ListProperty()
    streams_num = NumericProperty()
    streams_num_finished = NumericProperty()
    url = StringProperty()
    img = StringProperty()
    name = StringProperty()

    def __init__(self, **kwargs):
        super(PodcastBttn, self).__init__(**kwargs)
        self.url = kwargs.get('url', '')
        self.img = kwargs.get('img', '')
        self.name = kwargs.get('name', '')


    def podcast_search_links(self, *args):

        # start loading animation  
        self.load = LoadingModal()
        self.load.open()

        for store in [self.streaming_links, self.descriptions, self.timestamps]:
            store.clear()

        UrlRequest(self.url, self.find_streams) # using kivys async requests
    
    def find_streams(self, request, html):
        soup = BeautifulSoup(html, "html.parser")
        download_buttons = soup.find_all("a", {"class": "download"}, href=True)
        self.streams_num = len(download_buttons)
        self.streams_num_finished = 0
        for button_link in download_buttons:
             UrlRequest(button_link.get('href'), self.economist_found_streams) # using kivys async requests

    def economist_found_streams(self, request, html):
        soup = BeautifulSoup(html, "html.parser")

        link = soup.find("a", {"class": "btn btn-ios download-btn"}, href=True).get('href')
        self.streaming_links.append(link)

        description = soup.find("p", {"class": "pod-name"}).get_text()
        self.descriptions.append(description)

        timestamp = soup.find("div", {"class": "time"}).span.get_text()
        self.timestamps.append(timestamp)

        self.streams_num_finished +=1

        if self.streams_num_finished == self.streams_num:
            # dismiss loading animation
            self.load.dismiss()
            PodcastPopup(self.streaming_links, self.descriptions, self.timestamps, self.img, self.name).open()


class ScrollGridLayout(GridLayout):
    pass

class PodcastPopup(Popup):
    
    def __init__(self, streaming_links, descriptions, timestamps, img, name, **kwargs):
        super(PodcastPopup, self).__init__(**kwargs)

        self.size_hint=(None, None)
        self.size=(Window.width * 0.5, Window.height * 0.4)
        self.title = name

        grid = ScrollGridLayout(row_default_height=40, cols=1, spacing=[5, 5])

        for (streaming_link, description, timestamp) in sorted(zip(streaming_links, descriptions, timestamps), key=lambda x: x[2], reverse=True):
            row = PodcastPopupRow(streaming_link, description, timestamp, img, name)
            grid.add_widget(row)
        
        scrollview = ScrollView(do_scroll_y=True)
        scrollview.add_widget(grid)
        self.content = scrollview

class PodcastPopupRow(ButtonBehavior, GridLayout):
    link = StringProperty()
    image = StringProperty()
    description = StringProperty()
    name = StringProperty()
    timestamp = StringProperty()

    def __init__(self, link, description, timestamp, image, name, **kwargs):
        self.link = link
        self.description = description
        self.image = image
        self.name = name
        self.timestamp = timestamp
        super(PodcastPopupRow, self).__init__(**kwargs)
    
    def play_channel(self):
        # dismiss Popup
        self.parent.parent.parent.parent.parent.dismiss()
        App.get_running_app().play(self.link, image=self.image, name=self.name, description=self.description)

class LoadingWdgt(Label):
    angle_1 = NumericProperty(0)
    angle_2 = NumericProperty(20)

    def __init__(self, **kwargs):
        super(LoadingWdgt, self).__init__(**kwargs)
        Clock.schedule_once(self.set_circle)
        Clock.schedule_once(self.set_loading)

    def set_circle(self, dt):
        
        self.angle_1 = self.angle_1 + dt*90
        self.angle_2 = self.angle_2 + dt*180
        
        if self.angle_1 % 360 < self.angle_2 % 360:
            self.angle_1 = self.angle_1 % 360
            self.angle_2 = self.angle_2 % 360
            self.angle_2 += 15 

        Clock.schedule_once(self.set_circle, 1.0/20)
    
    def set_loading(self, dt):
        self.text = self.text + "."
        if self.text.count(".") == 4:
            self.text = "Loading ."
        Clock.schedule_once(self.set_loading, 0.3)


class LoadingModal(ModalView):
    pass

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
        
        print(link)
        print(kwargs)
        
        if link:
            # play
            media = self.vlc_inst.media_new(link)
            media.get_mrl()
            self.vlc_player.set_media(media)

        self.playing_name = kwargs.get('name', '')
        self.playing_image = kwargs.get('image', '')
        self.playing_description = kwargs.get('description', '')

        self.root.ids.playing_channel_img.source = './ButtonImages/' + self.playing_image
        self.root.ids.cover_image.source = './ButtonImages/' + self.playing_image

        
        self.vlc_player.play()
        
        Clock.schedule_interval(self.get_stream_info, 1)

    def get_stream_info(self, media, *largs):
        media = self.vlc_player.get_media()
        info = [media.get_meta(i) for i in range(30)]


        self.station = info[0] if info[0] else ''
        self.meta_info = info[12] if info[12] else ''

        if self.station.strip() == 'media.mp3':
            self.station = self.playing_name
            self.meta_info = self.playing_description

        return(info)

    def toggle(self):
        self.vlc_player.pause()


    def build(self):
        Window.borderless = False

if __name__ == "__main__":
    RadioApp().run()
