#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Implementation of a simple Pong clone."""

import sdl2.ext

from ..core import Project
from .systems import ControlSystem, MovementSystem, CollisionSystem
from .entities import Ball, Player


class Pong(Project):
    def init_systems(self, systems):
        systems["control"] = ControlSystem(0, 0, *self._window.size)
        systems["movement"] = MovementSystem(0, 0, *self._window.size)
        systems["collision"] = CollisionSystem(0, 0, *self._window.size)

        return systems

    def init_entities(self, systems, entities):
        sp_paddle1 = self._factory.from_color(sdl2.ext.Color(), size=(20, 100))
        sp_paddle2 = self._factory.from_color(sdl2.ext.Color(), size=(20, 100))
        sp_ball = self._factory.from_color(sdl2.ext.Color(), size=(20, 20))

        entities["player1"] = Player(self._world, sp_paddle1, position=(0, 250))
        entities["player2"] = Player(self._world, sp_paddle2, position=(780, 250), ai=True)

        entities["ball"] = Ball(self._world, sp_ball, position=(390, 290))
        entities["ball"].velocity.reset()

        systems["collision"].ball = entities["ball"]
        systems["collision"].player1 = entities["player1"]
        systems["collision"].player2 = entities["player2"]
        systems["control"].ball = entities["ball"]

        return entities
