from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.clock import Clock
from kivy.properties import NumericProperty
from kivy.base import Builder


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

class test_app(App):
    def load_loading(self, *largs):
        load = LoadingModal()
        load.open()

    def build(self):
        # open the view
        Clock.schedule_once(self.load_loading, 1)

        return Builder.load_string("""
GridLayout:
    cols:3

#<LoadingModal>:

<LoadingModal>:
    background: './ButtonImages/transparent.png'
    size_hint: None, None
    width: self.height
    height: app.root.height* 0.5
    LoadingWdgt:
        auto_dismiss: False
        text: "Loading "
        canvas.after:
            Color:
                rgb: 1,1,1
            Line:
                circle:self.center_x, self.center_y, (self.width / 2) * 0.8, self.angle_1, self.angle_2
                width: 2
        size_hint_y: None
        height: self.width
""")

if __name__ == '__main__':
    test_app().run()