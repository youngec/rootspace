#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Collection of components in an Entity-Component-System architecture."""

import math
import random

import sdl2

import rootspace.engine.components as components
import config.keymap


class PaddleControl(components.EventComponent):
    """
    The PaddleControl component stores an AI flag and the direction of
    the requested paddle movement. It reacts to events SDL_KEYDOWN and SDL_KEYUP.
    """

    def __init__(self):
        super(PaddleControl, self).__init__()

        self.ai = False
        self.movement = ""

        self.events = {
            sdl2.events.SDL_KEYDOWN: self.keypress,
            sdl2.events.SDL_KEYUP: self.keyrelease
        }

    def keypress(self, event):
        if event.key.keysym.sym == config.keymap.KEY_UP:
            self.movement = "up"
        elif event.key.keysym.sym == config.keymap.KEY_DOWN:
            self.movement = "down"

    def keyrelease(self, event):
        if event.key.keysym.sym in (config.keymap.KEY_UP, config.keymap.KEY_DOWN):
            self.movement = "stop"


class Score(object):
    def __init__(self):
        self.score = 0


class Velocity(object):
    def __init__(self):
        self.vx = 0
        self.vy = 0

        self.dx = 0
        self.dy = 0

        self.default = 200

    def reset(self):
        phi = math.pi * random.randint(0, 1)
        self.vx = self.default * math.cos(phi)
        self.vy = self.default * math.sin(phi)

    def up(self):
        self.vx = 0
        self.vy = -self.default

    def down(self):
        self.vx = 0
        self.vy = self.default

    def stop(self):
        self.vx = 0
        self.vy = 0
