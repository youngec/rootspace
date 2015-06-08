# coding:utf-8

"""Docstring"""

import sdl2.ext
import pong.entities
import pong.components


class TestPlayer(object):
    """
    Test the Player entity.
    """

    def test_baseclass(self):
        """
        The Player must be a subclass of Entity.

        :return:
        """

        assert issubclass(pong.entities.Player, sdl2.ext.Entity)

    def test_player(self):
        """
        The Player must have a Sprite, Velocity and a PlayerData component.

        :return:
        """

        player = pong.entities.Player(sdl2.ext.World(), sdl2.ext.Sprite())

        assert isinstance(player.sprite, sdl2.ext.Sprite)
        assert isinstance(player.velocity, pong.components.Velocity)
        assert isinstance(player.playerdata, pong.components.PlayerData)


class TestBall(object):
    """
    Test the Player entity.
    """

    def test_baseclass(self):
        """
        The Ball must be a subclass of Entity.

        :return:
        """
        assert issubclass(pong.entities.Ball, sdl2.ext.Entity)

    def test_ball(self):
        """
        The Ball must have a Sprite and a Velocity component.

        :return:
        """

        ball = pong.entities.Ball(sdl2.ext.World(), sdl2.ext.Sprite())

        assert isinstance(ball.sprite, sdl2.ext.Sprite)
        assert isinstance(ball.velocity, pong.components.Velocity)