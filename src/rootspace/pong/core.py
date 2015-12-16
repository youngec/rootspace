#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Implementation of a simple Pong clone."""

import sdl2.ext

from ..core import Core
from .systems import ControlSystem, MovementSystem, CollisionSystem
from .entities import Ball, Player


class PongCore(Core):
    @classmethod
    def _create_systems(cls):
        self._log.debug("Creating the paddle control movement system.")
        self._systems["control"] = ControlSystem(0, 0, *self._window.size)

        self._log.debug("Creating movement system.")
        self._systems["movement"] = MovementSystem(0, 0, *self._window.size)

        self._log.debug("Creating collision system.")
        self._systems["collision"] = CollisionSystem(0, 0, *self._window.size)

    @classmethod
    def _add_entities(cls):
        self._log.debug("Creating sprites.")
        sp_paddle1 = self._factory.from_color(sdl2.ext.Color(), size=(20, 100))
        sp_paddle2 = self._factory.from_color(sdl2.ext.Color(), size=(20, 100))
        sp_ball = self._factory.from_color(sdl2.ext.Color(), size=(20, 20))

        self._log.debug("Creating players.")
        self._entities["player1"] = Player(self._world, sp_paddle1, position=(0, 250))
        self._entities["player2"] = Player(self._world, sp_paddle2, position=(780, 250), ai=True)

        self._log.debug("Creating ball.")
        self._entities["ball"] = Ball(self._world, sp_ball, position=(390, 290))
        self._entities["ball"].velocity.reset()
        self._systems["collision"].ball = self._entities["ball"]
        self._systems["collision"].player1 = self._entities["player1"]
        self._systems["collision"].player2 = self._entities["player2"]
        self._systems["control"].ball = self._entities["ball"]
