#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Implementation of a simple Pong clone."""

import sdl2.ext

from ..core import Project
from .systems import ControlSystem, MovementSystem, CollisionSystem
from .entities import Ball, Player
from .components import PaddleControl, Velocity, Score


class Pong(Project):
    def init_systems(self, systems):
        window_params = dict(
                minx=0,
                miny=0,
                maxx=self._window.size[0],
                maxy=self._window.size[1]
        )

        systems["control"] = ControlSystem(**window_params)
        systems["movement"] = MovementSystem(**window_params)
        systems["collision"] = CollisionSystem(**window_params)

        return systems

    def init_entities(self, systems, entities):
        sp_paddle1 = self._factory.from_color(sdl2.ext.Color(), size=(20, 100))
        sp_paddle1.position = (0, 250)
        entities["player1"] = Player.create(
                self._world,
                sprite=sp_paddle1,
                paddle_control=PaddleControl(key_up=sdl2.SDL_KEYUP, key_down=sdl2.SDL_KEYDOWN),
                velocity=Velocity(),
                score=Score()
        )

        sp_paddle2 = self._factory.from_color(sdl2.ext.Color(), size=(20, 100))
        sp_paddle2.position = (780, 250)
        entities["player2"] = Player.create(
                self._world,
                sprite=sp_paddle2,
                paddle_control=PaddleControl(key_up=0, key_down=0, ai=True),
                velocity=Velocity(),
                score=Score()
        )

        sp_ball = self._factory.from_color(sdl2.ext.Color(), size=(20, 20))
        sp_ball.position = (390, 290)
        vel_ball = Velocity()
        vel_ball.reset()
        entities["ball"] = Ball.create(
                self._world,
                sprite=sp_ball,
                velocity=vel_ball
        )

        systems["collision"].ball = entities["ball"]
        systems["collision"].player1 = entities["player1"]
        systems["collision"].player2 = entities["player2"]
        systems["control"].ball = entities["ball"]

        return entities
