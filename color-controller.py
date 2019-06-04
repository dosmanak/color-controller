#!/usr/bin/env python3
BOXFACTOR=0.5
import os.path
import time
import sys
import argparse
import colorsys

import _thread
import serial
import re

# Add '--' into args to skip kivy argparser
sys.argv = [sys.argv[0], '--'] + sys.argv[1:]

import kivy
from kivy.core.window import Window
from kivy.app import App
#from kivy.properties.ListProperty import ListProperty
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout


class Box(Image):
  def __y2colorchange(self, y):
      c = float(y)/self.height
      c = min(c,1)
      c = max(c,0)
      return(c)

  def on_touch_move(self, touch):
    """ Mouse control is only for development, could be removed """
    #print(touch.x, touch.y)
    r,g,b,a = self.color
    pos_x, pos_y = self.pos
    if touch.x - pos_x < self.width/3:
      r = self.__y2colorchange(touch.y - pos_y)
      print("Red:", r)
    if touch.x - pos_x >= self.width/3 and touch.x - pos_x <= self.width - self.width/3:
      g = self.__y2colorchange(touch.y - pos_y)
      print("Green:", g)
    if touch.x - pos_x > self.width - self.width/3:
      b = self.__y2colorchange(touch.y - pos_y)
      print("Blue:", b)
    self.color = (r, g, b, a)


class MyApp(App):
  def build(self):
    self.title = "Color control"
    self.layout = FloatLayout()
    self.im = Image(source=args.image)
    Window.size = tuple(i*1.2 for i in self.im.texture_size)
    self.layout.add_widget(self.im)
    self.box = Box(pos_hint={'center_x': 0.5, 'center_y': 0.5}, size_hint = (BOXFACTOR, BOXFACTOR), color = INITCOLOR)
    self.layout.add_widget(self.box)
    return self.layout

def replayLoop(kivyApp):
  global respondent, lightlevel, controller_state
  time.sleep(1) # wait for kivy to initialize
  fd = open('controller.csv')
  for current_line in fd.readlines():
    entry = current_line.split(';')
    entry_image = entry[1]
    entry_cspace = entry[4]
    entry_color = entry[5].split(',')
    entry_color = [ float(c) for c in entry_color ]
    if entry_image.strip() != args.image:
      print('SKIPPING(image mismatch): {}'.format(current_line), end = '')
      continue
    print(current_line, end = '')
    if entry_cspace == " RGB ":
      entry_rgb = [ c/255 for c in entry_color ]
      entry_rgb.append(1)
      kivyApp.box.color = entry_rgb
    else:
      # convert color from hsv to rgb
      entry_rgb = list( colorsys.hsv_to_rgb(entry_color[0]/360, entry_color[1], entry_color[2]) )
      entry_rgb.append(1)
      kivyApp.box.color = tuple(entry_rgb)
    time.sleep(float(args.replay))
  print('The file controller.csv has been replayed, you may close the window.')


def serialLoop(kivyApp):
  ''' NB: serial device path might differ on some machines '''
  global respondent, lightlevel, controller_state
  ser = serial.Serial('/dev/ttyUSB0')
  last_line = ''
  while True:
      current_line = ser.readline().decode('ascii')
      if current_line == last_line:
        continue
      m = re.search('Encoder ([0-9]): (\-?[0-9]+)',current_line)
      knob = int(m.group(1))
      value = float(m.group(2))
      cc = kivyApp.box.color
      if args.rgb:
        # step in controller is around 1, color is in range 0..1, use one step as 1/1000 (maybe too small)
        cc[knob] = max(min(INITCOLOR[knob] + value/1000., 1), 0)
        controller_state = "{}; {}; {}; {}; RGB ; {:.0f},{:.0f},{:.0f}".format(
          time.ctime(), args.image, respondent, lightlevel,
          [c*255 for c in cc][0], [c*255 for c in cc][1], [c*255 for c in cc][2])
        print(controller_state)
        kivyApp.box.color = cc
      else:
        # convert color from rgb to hsv, update changed value, convrt back to rgb
        c_hsv = list( colorsys.rgb_to_hsv(cc[0], cc[1], cc[2]) )
        init_hsv = colorsys.rgb_to_hsv(INITCOLOR[0], INITCOLOR[1], INITCOLOR[2])
        # step for saturation is 1/100, for hue it is 1/1000 
        if knob in [1,2]:
          step = value/100
        else:
          step = value/1000
        c_hsv[knob] = max(min(init_hsv[knob] + step, 1), 0)
        controller_state = "{}; {}; {}; {}; HSV ; {:.3f},{:.3f},{:.3f}".format(
          time.ctime(), args.image, respondent, lightlevel,
          360*c_hsv[0], c_hsv[1], c_hsv[2])
        print(controller_state)
        c_rgb = list( colorsys.hsv_to_rgb(c_hsv[0], c_hsv[1], c_hsv[2]) )
        c_rgb.append(1)
        kivyApp.box.color = tuple(c_rgb)
      last_line = current_line

  ser.close()

def inputLoop():
  global respondent, lightlevel, controller_state
  time.sleep(3)
  print('# # # # # # # # # # # # # # # # # # # # # #')
  print(' # # # # # # # # # # # # # # # # # # # # # #')
  print('Anytime, type in respondent(num), lightlevel(num) and press enter to set it.')
  print('Or type S (capital) and press enter to store current settings to controller.csv in current dir.')
  while True:
    human = input()
    try:
      respondent = int(human.split(',')[0].strip())
      lightlevel = int(human.split(',')[1].strip())
    except:
      if human == 'S':
        fd = open('controller.csv','a')
        fd.write(controller_state + '\n')
        fd.close
        print('WRITTEN: ' + controller_state)
      else:
        print('', end='.')

# main

INITCOLOR = (1, 1, 1, 1)
respondent = 0
lightlevel = 0
controller_state = 'NEW'

parser = argparse.ArgumentParser(description='Color controller')
parser.add_argument('image', help='Background image (png format)')
parser.add_argument('--inithsv', help='initial color in format "h[0-360],s[0-1],v[0-1]"')
parser.add_argument('--initrgb', help='initial color in format "r,g,b", values [0-255]')
parser.add_argument('--rgb', action='store_const', const=True, default=False, help='Controler input in rgb, default is hsv')
parser.add_argument('--replay', metavar='N', default=False, help='Replay stored data from controller.csv, wait N seconds between changes')

args = parser.parse_args()

if args.inithsv:
  if args.initrgb:
    parser.error('Can not assign both HSV and RGB initial color')
    exit(2)
  inithsv = tuple( float(i) for i in args.inithsv.split(',') )
  if len(inithsv) != 3:
    parser.error('HSV must have 3 parts')
    exit(1)
  inithsv=(inithsv[0]/360, inithsv[1], inithsv[2])
  initrgb = colorsys.hsv_to_rgb(inithsv[0], inithsv[1], inithsv[2])
  initrgb = list(initrgb)
  initrgb.append(1)
  INITCOLOR = tuple(initrgb)

if args.initrgb:
  initrgb = [ float(i)/255 for i in args.initrgb.split(',') ]
  if len(initrgb) != 3:
    parser.error('RGB must have 3 parts')
    exit(1)
  initrgb.append(1)
  INITCOLOR = tuple(initrgb)

if not os.path.isfile(args.image):
  parser.error('File "{}" does not exist'.format(args.image))
  exit(127)

Kivy = MyApp()
if args.replay != False:
  _thread.start_new_thread(replayLoop, (Kivy,))
else:
  _thread.start_new_thread(serialLoop, (Kivy,))
  _thread.start_new_thread(inputLoop, tuple())

Kivy.run()


