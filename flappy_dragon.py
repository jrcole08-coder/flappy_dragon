"""
Flappy Dragon: Siege Master  --  run THIS file.
Keep fd_core.py, fd_art.py, fd_logic.py and fd_draw.py in the same folder.
"""
import pygame
import os
import sys
try:
  sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
except NameError:
  sys.path.insert(0, os.getcwd())
pygame.mixer.pre_init(22050, -16, 1, 512)
pygame.init()
from fd_core import *
from fd_art import *
from fd_logic import GameLogic
from fd_draw import GameDraw

class Game(GameLogic, GameDraw):
  pass

def main():
  Game().run()

if __name__ == "__main__":
  main()
