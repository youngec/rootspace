#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Collection of entities in an Entity-Component-System architecture."""

import sdl2.ext
from pong.components import PaddleControl, Velocity, Score


class Player(sdl2.ext.Entity):
    """
    A Player is an Entity with a sprite, velocity and player data.
    """

    def __init__(self, world, sprite, position=(0, 0), ai=False):
        """
        Construct a Player.

        :param world: Containing World (used by __new__()!)
        :param sprite: Sprite instance
        :param position: Desired position of the Sprite
        :param ai: AI flag
        :return:
        """

        self.sprite = sprite
        self.paddlecontrol = PaddleControl()
        self.velocity = Velocity()
        self.score = Score()

        self.paddlecontrol.ai = ai
        self.sprite.position = position


class Ball(sdl2.ext.Entity):
    """
    A Ball is an Entity with a sprite and velocity.
    """

    def __init__(self, world, sprite, position=(0, 0)):
        """
        Construct a Ball.

        :param world: Containing World (used by __new__()!)
        :param sprite: Sprite instance
        :param position: Desired position of the Sprite
        :return:
        """

        self.sprite = sprite
        self.velocity = Velocity()

        self.sprite.position = position
