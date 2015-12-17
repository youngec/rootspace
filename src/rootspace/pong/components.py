#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Collection of components in an Entity-Component-System architecture."""

import math
import random

import sdl2
import attr
from attr.validators import instance_of

from ..ebs import EventComponent


@attr.s
class PaddleControl(EventComponent):
    """
    The PaddleControl component stores an AI flag and the direction of
    the requested paddle movement. It reacts to events SDL_KEYDOWN and SDL_KEYUP.
    """
    key_up = attr.ib(default=sdl2.SDL_KEYUP, validator=instance_of(int))
    key_down = attr.ib(default=sdl2.SDL_KEYDOWN, validator=instance_of(int))
    ai = attr.ib(default=False, validator=instance_of(bool))
    movement = attr.ib(default="", validator=instance_of(str))

    def __init__(self):
        self.events = {
            sdl2.events.SDL_KEYDOWN: self.keypress,
            sdl2.events.SDL_KEYUP: self.keyrelease
        }

    def keypress(self, event):
        if event.key.keysym.sym == self.key_up:
            self.movement = "up"
        elif event.key.keysym.sym == self.key_down:
            self.movement = "down"

    def keyrelease(self, event):
        if event.key.keysym.sym in (self.key_up, self.key_down):
            self.movement = "stop"


@attr.s
class Score(object):
    score = attr.ib(default=0, validator=instance_of(int))


@attr.s
class Velocity(object):
    vx = attr.ib(default=0, validator=instance_of(float))
    vy = attr.ib(default=0, validator=instance_of(float))
    dx = attr.ib(default=0)
    dy = attr.ib(default=0)
    def_velocity = attr.ib(default=200, validator=instance_of(float))

    def reset(self):
        phi = math.pi * random.randint(0, 1)
        self.vx = self.def_velocity * math.cos(phi)
        self.vy = self.def_velocity * math.sin(phi)

    def up(self):
        self.vx = 0
        self.vy = -self.def_velocity

    def down(self):
        self.vx = 0
        self.vy = self.def_velocity

    def stop(self):
        self.vx = 0
        self.vy = 0
