#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Implementation of a simple Pong clone."""

import sdl2.ext
import engine.core
import pong.systems
import pong.entities


class PongCore(engine.core.Core):
    def _create_systems(self):
        self._log.debug("Creating the paddle control movement system.")
        self._systems["control"] = pong.systems.ControlSystem(0, 0, *self._window.size)

        self._log.debug("Creating movement system.")
        self._systems["movement"] = pong.systems.MovementSystem(0, 0, *self._window.size)

        self._log.debug("Creating collision system.")
        self._systems["collision"] = pong.systems.CollisionSystem(0, 0, *self._window.size)

    def _add_entities(self):
        self._log.debug("Creating sprites.")
        sp_paddle1 = self._factory.from_color(sdl2.ext.Color(), size=(20, 100))
        sp_paddle2 = self._factory.from_color(sdl2.ext.Color(), size=(20, 100))
        sp_ball = self._factory.from_color(sdl2.ext.Color(), size=(20, 20))

        self._log.debug("Creating players.")
        self._entities["player1"] = pong.entities.Player(self._world, sp_paddle1, position=(0, 250))
        self._entities["player2"] = pong.entities.Player(self._world, sp_paddle2, position=(780, 250), ai=True)

        self._log.debug("Creating ball.")
        self._entities["ball"] = pong.entities.Ball(self._world, sp_ball, position=(390, 290))
        self._entities["ball"].velocity.reset()
        self._systems["collision"].ball = self._entities["ball"]
        self._systems["collision"].player1 = self._entities["player1"]
        self._systems["collision"].player2 = self._entities["player2"]
        self._systems["control"].ball = self._entities["ball"]