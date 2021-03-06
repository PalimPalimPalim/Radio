#!/usr/bin/env python3
import os
import csv
import vlc
import requests
from bs4 import BeautifulSoup
from functools import partial
import coverpy
import dateparser
import time
from misc.detectpi import is_raspberry_pi
from misc.osType import get_platform
from misc.download_tagesthemen import get_tagesthemen_download_link_date
from pathlib import Path

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
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty, BooleanProperty, ObjectProperty, ListProperty, NumericProperty
from kivy.network.urlrequest import UrlRequest
from kivy.clock import Clock
from kivy.vector import Vector
from kivy.graphics.vertex_instructions import Triangle, Rectangle, Ellipse
from kivy.graphics.context_instructions import Color
from kivy.graphics.instructions import Callback, InstructionGroup
from kivy.core.window import Window
from kivy.animation import Animation

IS_RASPBERRY_PI = is_raspberry_pi()
IS_WINDOWS = get_platform() == 'Windows'
IS_MAC = get_platform() == 'OS X'

if IS_RASPBERRY_PI:
    from omxplayer.player import OMXPlayer, OMXPlayerDeadError

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
    
    def get_status(self):
        status = App.get_running_app().vlc_player.get_state()
        return status


    def check_status(self, *largs):
        # retrieve if playing
        status = self.get_status()

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

class PlayPauseButtonVideo(PlayPauseButton):
    def get_status(self):
        return 'State.Playing'


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
        print(get_platform(), 'palim')

        App.get_running_app().vlc_player.stop()

        if IS_RASPBERRY_PI:
            App.get_running_app().root.current = 'video'
            App.get_running_app().playing_video = self.get_date() + self.name + ".mp4"
        elif IS_WINDOWS:
            os.system("start ./videos/" + self.get_date() + self.name + ".mp4")
        elif IS_MAC:
            os.system("open ./videos/" + self.get_date() + self.name + ".mp4")

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
        super().__init__(**kwargs)
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


class PodcastBttn2(PodcastBttn):

    def podcast_search_links(self, *args):

        # start loading animation  
        self.load = LoadingModal()
        self.load.open()

        for store in [self.streaming_links, self.descriptions, self.timestamps]:
            store.clear()

        UrlRequest(self.url, self.find_streams) # using kivys async requests

    def find_streams(self, request, html):
        soup = BeautifulSoup(html, "html.parser")
        
        for item in soup.find_all('item'):
            title = item.find('title').getText()
            link = item.find('enclosure').get('url')
            # description =f"({item.find('itunes:duration').getText()}) {item.find('description').getText()[3:-4]}"
            timestamp = item.find('pubdate').getText()[5:16]
            self.streaming_links.append(link)
            self.descriptions.append(title)
            self.timestamps.append(timestamp)

        # dismiss loading animation
        self.load.dismiss()
        PodcastPopup(self.streaming_links, self.descriptions, self.timestamps, self.img, self.name).open()



class ScrollGridLayout(GridLayout):
    pass

class PodcastPopup(Popup):
    
    def __init__(self, streaming_links, descriptions, timestamps, img, name, **kwargs):
        super(PodcastPopup, self).__init__(**kwargs)

        self.size_hint=(None, None)
        self.size=(Window.width * 0.5, Window.height * 0.9)
        self.title = name

        grid = ScrollGridLayout(row_default_height=40, cols=1, spacing=[5, 5])
        
        for (streaming_link, description, timestamp) in sorted(zip(streaming_links, descriptions, timestamps), key=lambda x: dateparser.parse(x[2]), reverse=True):
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
    perc_finished = NumericProperty(0)
    is_refreshing = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(VideoGrid, self).__init__(**kwargs)
        Clock.schedule_once(self.add_tagesthemen, 2)

    def refresh(self):
        self.refresh_tagesthemen()

    def refresh_tagesthemen(self):
        self.is_refreshing = True
        Clock.tick()
        info = get_tagesthemen_download_link_date()
        UrlRequest( url=info['link'], 
                    on_success=self.after_download,
                    on_progress=self.on_download_progress,
                    file_path='./videos/' + info['date'] + 'tagesthemen.mp4')

    def after_download(self, request, result):
        print(f'request={request}, result={result}')
        print('download finished')
        self.is_refreshing = False
        self.clear_widgets()
        self.add_tagesthemen()

    def on_download_progress(self, request, current_size, total_size):
        # print(f'request={request}, current_size={current_size}, total_size={total_size}')
        self.perc_finished = current_size / total_size

    def add_tagesthemen(self, *_):
        self.add_widget(TVButton(name="tagesthemen", 
                                 image="tagesthemen.png",
                                 size_hint=(None, None),
                                 width=(Window.width - 2 * 5) / 6,
                                 height=(Window.width - 2 * 5) / 6)) # spacing inside channel grid is 5

        for _ in range(15):
            self.add_widget(VideoGridSpacer())

class VideoGridSpacer(Widget):
    pass

class RefreshScrollView(ScrollView):
    is_refreshing = BooleanProperty(False)

    def __init__(self, **kwargs):
        self.register_event_type('on_refresh')
        super().__init__(**kwargs)
    
    def check_refresh(self):
        if not self.is_refreshing and self.scroll_y > 1.05:
            Clock.schedule_once(lambda x: self.dispatch('on_refresh'), 2)
            self.is_refreshing = True
            Clock.schedule_once(lambda x: setattr(self, 'is_refreshing', False), 10)

    def on_refresh(self):
        pass

class ClockLabel(Label):

    def __init__(self, **kwargs):
        super(ClockLabel, self).__init__(**kwargs)
        Clock.schedule_interval(self.update, 1)
    
    def update(self, *_):
        self.text = time.asctime()

class RootScreenManager(ScreenManager):
    def __init__(self, **kwargs):
        super(RootScreenManager, self).__init__(**kwargs)
        self.add_widget(BaseScreen())
        self.add_widget(ScreenSaver())
        if IS_RASPBERRY_PI:
            self.add_widget(VideoPlayerScreen())


class BaseScreen(Screen, ButtonBehavior):
    touches = ListProperty([])
    delay = NumericProperty(15)

    def on_touch_down(self, touch):
        touch.grab(self)
        self.touches.append(touch)
        Clock.unschedule(self.callback)
        return super(BaseScreen, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            self.touches.remove(touch)
            if not(self.touches):
                Clock.schedule_once(self.callback, self.delay)
            return True
        else:
            return super(BaseScreen, self).on_touch_up(touch)

    def callback(self, *args):
        if App.get_running_app().root.current == self.name: # ToDo, make this better, this should not be called if it is not on BaseScreen
            self.parent.current = 'screen_saver'

class ScreenSaver(Screen, ButtonBehavior):
    def __init__(self, **kwargs):
        super(ScreenSaver, self).__init__(**kwargs)
        self.bind(on_touch_down=self.deactivate_screen_saver)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            return True
        return super(ScreenSaver, self).on_touch_down(touch)

    def deactivate_screen_saver(self, *_):
        self.parent.current = 'base'

class VideoPlayerScreen(Screen):
    slider = ObjectProperty()
    minimized = BooleanProperty(True)
    video_path = StringProperty() # 20200308tagesthemen.mp4

    def is_playing(self):
        if hasattr(self, 'player'):
            try:
                return self.player.is_playing()
            except OMXPlayerDeadError:
                self.leave_player()
                return False
        else:
            return False
    
    def set_play_pause_bttn(self, *args):
        print(self.ids)
        if self.is_playing():
            self.ids.play_pause_image.source = 'atlas://data/images/defaulttheme/media-playback-pause'   
        else:
            self.ids.play_pause_image.source = 'atlas://data/images/defaulttheme/media-playback-start'


    def play(self):
        VIDEO_PATH = Path("videos/" + self.video_path)
        print(VIDEO_PATH)
        self.player = OMXPlayer(VIDEO_PATH, args=['-o', 'alsa',  '--layer',  '100000'])
        self.player.set_video_pos(0,0,800,480)
        self.set_slider()
        self.change_size()
        Clock.schedule_interval(self.set_slider, 3)
        Clock.schedule_interval(self.set_play_pause_bttn, 1)

    def player_stop(self):
        Clock.unschedule(self.set_play_pause_bttn)
        Clock.unschedule(self.set_slider)
        if self.is_playing():
            self.player.stop()
    
    @staticmethod
    def leave_player():
        App.get_running_app().root.current = 'base'

    def play_pause(self):
        self.player.play_pause()

    def quit(self, gg, **kwargs):
        self.player.quit()
        App.get_running_app().stop()

    def set_slider(self, *args):
        try: 
            pos = self.player.position() # in seconds as int
            duration =  self.player.duration() # in seconds as float
            self.slider.value_normalized = pos / duration
        except OMXPlayerDeadError:
            self.leave_player()
        

    def set_videopos(self, *args):
        pos = self.player.position() # in seconds as int
        duration =  self.player.duration() # in seconds as float
        if abs (pos/duration - self.slider.value_normalized) > 0.05:
            self.player.set_position(self.slider.value_normalized*duration)


    def change_size(self):

        if self.minimized:
            self.player.set_alpha(255)
        else:
            self.player.set_alpha(100)
        self.minimized = not self.minimized

class PlayPauseButtonVideo(PlayPauseButton):
    pass

class RadioApp(App):
    station = StringProperty()
    meta_info = StringProperty()
    playing_name = StringProperty()
    playing_image = StringProperty('black.png')
    playing_description = StringProperty()
    playing_video = StringProperty()


    def __init__(self, **kwargs):
        super(RadioApp, self).__init__(**kwargs)
        # start vlc for mp3 streaming
        self.vlc_inst = vlc.Instance('--fullscreen')
        self.vlc_player = self.vlc_inst.media_player_new()
        
    def play(self, link='', **kwargs):
        # Window.clearcolor = (0,0,0,0)
        # link = 'videos/20200308tagesthemen.mp4'
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

        # self.root.ids.playing_channel_img.source = './ButtonImages/' + self.playing_image
        # self.root.ids.cover_image.source = './ButtonImages/' + self.playing_image
        
        self.vlc_player.play()


        Clock.schedule_interval(self.get_stream_info, 1)

    def get_stream_info(self, media, *largs):
        media = self.vlc_player.get_media()
        info = [media.get_meta(i) for i in range(30)]


        self.station = info[0] if info[0] else self.playing_name
        self.meta_info = info[12] if info[12] else self.playing_description

        if '.mp3' in self.station:
            self.station = self.playing_name
            self.meta_info = self.playing_description

        return(info)

    def toggle(self):
        self.vlc_player.pause()


    def build(self):
        Window.borderless = False

if __name__ == "__main__":
    radio = RadioApp()
    try:
        radio.run()
    except KeyboardInterrupt:
        radio.stop()
        # os.system('killall dbus-daemon')
