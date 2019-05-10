#!/usr/bin/env python3
import kivy
from kivy.core.window import Window
from kivy.app import App
from kivy.graphics import Color, Rectangle
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout


from kivy.uix.stacklayout import StackLayout
import os

import _thread
import serial
import re

#INITCOLOR = (255, 255, 255, 1)
INITCOLOR = (0, 1, 0, 1)

class Box(Image):
  def __y2colorchange(self, y):
      c = float(y)/self.height
      c = min(c,1)
      c = max(c,0)
      return(c)

  def on_touch_move(self, touch):
    print(touch.x, touch.y)
    r,g,b,a = self.color
    if touch.x < self.width/3:
      r = self.__y2colorchange(touch.y)
      print("Red:", r)
    if touch.x >= self.width/3 and touch.x <= self.width - self.width/3:
      g = self.__y2colorchange(touch.y)
      print("Green:", g)
    if touch.x > self.width - self.width/3:
      b = self.__y2colorchange(touch.y)
      print("Blue:", b)
    self.color = (r, g, b, a)


class MyApp(App):
  def build(self):
    self.title = "Color control"
    self.layout = FloatLayout()
    self.im = Image(source='cc-cloud.png')
    self.layout.add_widget(self.im)
    self.box = Box(pos_hint={'center_x': 0.5, 'center_y': 0.5}, size_hint = (0.2, 0.2), color = INITCOLOR)
    self.layout.add_widget(self.box)
    return self.layout

class Setting(App):
  def build(self):
    self.title = "Color control settings"
    self.dialog = StackLayout()
    for f in os.listdir():
      if re.match('.*\.png$', f):
        btn  = Button(text = f)
        btn.bind(on_release = lambda btn: f)
        self.dialog.add_widget(btn)
    return self.dialog

def serialLoop(kivyApp):
  ser = serial.Serial('/dev/ttyUSB0')
  while True:
      ##print(ser.readline().decode('ascii'))
      m = re.search('Encoder ([0-9]): (\-?[0-9]+)',ser.readline().decode('ascii'))
      knob = int(m.group(1))
      value = float(m.group(2))
      #print("Knob {}, value {}".format(knob, value))
      cc = kivyApp.box.color
      vars(cc)
      #cc[knob] = max(min(INITCOLOR[knob] + value,255),0)/255.
      cc[knob] = max(min(INITCOLOR[knob] + value/1000., 1),0)
      print("RGB (0-1): {:.3f} {:.3f} {:.3f}".format(cc[0], cc[1], cc[2]))
      print("RGB (0-255): {:.0f} {:.0f} {:.0f}".format([c*255 for c in cc][0], [c*255 for c in cc][1], [c*255 for c in cc][2]))
      kivyApp.box.color = cc
  ser.close()


Window.size = (600,600)

Kivy = MyApp()
_thread.start_new_thread(serialLoop,(Kivy,))

Kivy.run()


