import kivy
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.image import Image


class MyApp(App):
  def build(self):
    return Image(source='cc-cloud.png')

MyApp().run()
