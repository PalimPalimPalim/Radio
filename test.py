from kivy.app import App
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label
from kivy.lang import Builder


class Lable (ButtonBehavior, Label):
    pass

b = Builder.load_string("""
Lable:
    text: "a"
    on_press: print("pressed")

""")

class MyApp(App):
    def build(self):
        return(b)
    
    def on_press(self):
        self.source = 'atlas://data/images/defaulttheme/checkbox_on'



if __name__ == '__main__':
    MyApp().run()