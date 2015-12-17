#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Collection of entities in an Entity-Component-System architecture."""

import sdl2.ext
import attr
from attr.validators import instance_of, optional
from ..ebs import Entity
from .components import PaddleControl, Velocity, Score


@attr.s
class Player(Entity):
    """
    A Player is an Entity with a sprite, velocity and player data.
    """
    sprite = attr.ib(default=None, validator=optional(instance_of(sdl2.ext.Sprite)))
    paddle_control = attr.ib(default=attr.Factory(PaddleControl), validator=instance_of(PaddleControl))
    velocity = attr.ib(default=attr.Factory(Velocity), validator=instance_of(Velocity))
    score = attr.ib(default=attr.Factory(Score), validator=instance_of(Score))


@attr.s
class Ball(Entity):
    """
    A Ball is an Entity with a sprite and velocity.
    """
    sprite = attr.ib(default=None, validator=optional(instance_of(sdl2.ext.Sprite)))
    velocity = attr.ib(default=attr.Factory(Velocity), validator=instance_of(Velocity))
