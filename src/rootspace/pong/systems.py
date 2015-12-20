#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Collection of systems in an Entity-Component-System architecture."""

import sdl2.ext
import attr
from attr.validators import instance_of, optional
from ..abstract import Applicator
from .components import PaddleControl, Velocity
from .entities import Ball, Player


@attr.s
class ControlSystem(Applicator):
    minx = attr.ib(default=0, validator=instance_of(int))
    miny = attr.ib(default=0, validator=instance_of(int))
    maxx = attr.ib(default=640, validator=instance_of(int))
    maxy = attr.ib(default=480, validator=instance_of(int))
    ball = attr.ib(default=None, validator=optional(instance_of(Ball)))

    def __init__(self):
        self.component_types = (PaddleControl, Velocity, sdl2.ext.Sprite)

    def _control_pc(self, paddle_control, velocity, sprite):
        if paddle_control.movement == "up":
            velocity.up()
        elif paddle_control.movement == "down":
            velocity.down()
        elif paddle_control.movement == "stop":
            velocity.stop()

        paddle_control.movement = ""

    def _control_npc(self, paddle_control, velocity, sprite):
        centery = sprite.y + sprite.size[1] / 2

        if self.ball.velocity.vx < 0:
            # ball is moving away from the AI
            if centery < self.maxy / 2:
                velocity.down()
            elif centery > self.maxy / 2:
                velocity.up()
            else:
                velocity.stop()
        else:
            bcentery = self.ball.sprite.y + self.ball.sprite.size[1] / 2
            if bcentery < centery:
                velocity.up()
            elif bcentery > centery:
                velocity.down()
            else:
                velocity.stop()

    def update(self, t, dt, world, components):
        for pcontrol, vel, sprite in components:
            if pcontrol.ai:
                self._control_npc(pcontrol, vel, sprite)
            else:
                self._control_pc(pcontrol, vel, sprite)


@attr.s
class MovementSystem(Applicator):
    minx = attr.ib(default=0, validator=instance_of(int))
    miny = attr.ib(default=0, validator=instance_of(int))
    maxx = attr.ib(default=640, validator=instance_of(int))
    maxy = attr.ib(default=480, validator=instance_of(int))

    def __init__(self):
        self.component_types = (Velocity, sdl2.ext.Sprite)

    def _move(self, dt, velocity, sprite):
        """
        Move a Sprite according to the velocity of the parent Entity.

        :param velocity:
        :param sprite:
        :return:
        """
        velocity.dx += velocity.vx * dt
        if abs(velocity.dx) >= 1:
            sprite.x += round(velocity.dx)
            velocity.dx = 0

        velocity.dy += velocity.vy * dt
        if abs(velocity.dy) >= 1:
            sprite.y += round(velocity.dy)
            velocity.dy = 0

    def _bound(self, sprite):
        """
        Ensure that the Sprite remains within the frame boundary.

        :param sprite:
        :return:
        """
        sprite.x = max(self.minx, sprite.x)
        sprite.y = max(self.miny, sprite.y)

        swidth, sheight = sprite.size
        pmaxx = sprite.x + swidth
        pmaxy = sprite.y + sheight
        if pmaxx > self.maxx:
            sprite.x = self.maxx - swidth
        if pmaxy > self.maxy:
            sprite.y = self.maxy - sheight

    def update(self, t, dt, world, components):
        for velocity, sprite in components:
            self._move(dt, velocity, sprite)
            self._bound(sprite)


@attr.s
class CollisionSystem(Applicator):
    minx = attr.ib(default=0, validator=instance_of(int))
    miny = attr.ib(default=0, validator=instance_of(int))
    maxx = attr.ib(default=640, validator=instance_of(int))
    maxy = attr.ib(default=480, validator=instance_of(int))
    ball = attr.ib(default=None, validator=optional(instance_of(Ball)))
    player1 = attr.ib(default=None, validator=optional(instance_of(Player)))
    player2 = attr.ib(default=None, validator=optional(instance_of(Player)))

    def __init__(self):
        self.component_types = (Velocity, sdl2.ext.Sprite)

    def _overlap(self, item):
        """
        Check whether the Ball overlaps with any Entity.

        :param item:
        :return:
        """
        pos, sprite = item
        if sprite == self.ball.sprite:
            return False

        left, top, right, bottom = sprite.area
        bleft, btop, bright, bbottom = self.ball.sprite.area

        return bleft < right and bright > left and btop < bottom and bbottom > top

    def _deflect(self, comps):
        """
        Deflect a Ball impinging on a Paddle.

        :param comps:
        :return:
        """
        self.ball.velocity.vx = -self.ball.velocity.vx

        sprite = comps[0][1]
        ballcentery = self.ball.sprite.y + self.ball.sprite.size[1] / 2
        halfheight = sprite.size[1] / 2
        stepsize = halfheight / 10
        degrees = 45
        paddlecentery = sprite.y + halfheight

        if ballcentery < paddlecentery:
            self._logger.debug("Ball hits paddle above center.")
            factor = (paddlecentery - ballcentery) / stepsize
            self.ball.velocity.vy = -factor * degrees
        elif ballcentery > paddlecentery:
            self._logger.debug("Ball hits paddle below center.")
            factor = (ballcentery - paddlecentery) / stepsize
            self.ball.velocity.vy = factor * degrees
        else:
            self._logger.debug("Ball hits paddle in the center.")
            self.ball.velocity.vy = - self.ball.velocity.vy

    def _bounce(self):
        """
        Bounce the Ball on the frame box.

        :return:
        """

        if self.ball.sprite.y <= self.miny:
            self._logger.debug("Ball hits top boundary.")
            self.ball.velocity.vy = -self.ball.velocity.vy

        if self.ball.sprite.y + self.ball.sprite.size[1] >= self.maxy:
            self._logger.debug("Ball hits bottom boundary.")
            self.ball.velocity.vy = -self.ball.velocity.vy

        if self.ball.sprite.x <= self.minx:
            self._logger.debug("Ball hits left boundary.")
            self._logger.info("Player 2 has won a point!")
            self.player2.score.score += 1
            self.ball.sprite.position = (390, 290)
            self.ball.velocity.reset()

        if self.ball.sprite.x + self.ball.sprite.size[0] >= self.maxx:
            self._logger.debug("Ball hits right boundary.")
            self._logger.info("Player 1 has won a point!")
            self.player1.score.score += 1
            self.ball.sprite.position = (390, 290)
            self.ball.velocity.reset()

    def update(self, t, dt, world, components):
        collitems = [comp for comp in components if self._overlap(comp)]
        if collitems:
            self._deflect(collitems)

        self._bounce()
