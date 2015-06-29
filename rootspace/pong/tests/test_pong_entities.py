# coding:utf-8

"""Docstring"""

import sdl2.ext

import rootspace.pong.components


class TestPlayer(object):
    """
    Test the Player entity.
    """

    def test_baseclass(self):
        """
        The Player must be a subclass of Entity.

        :return:
        """

        assert issubclass(rootspace.pong.entities.Player, sdl2.ext.Entity)

    def test_player(self):
        """
        The Player must have a Sprite, Velocity and a PlayerData component.

        :return:
        """

        player = rootspace.pong.entities.Player(sdl2.ext.World(), sdl2.ext.Sprite())

        assert isinstance(player.sprite, sdl2.ext.Sprite)
        assert isinstance(player.velocity, rootspace.pong.components.Velocity)
        assert isinstance(player.playerdata, rootspace.pong.components.PlayerData)


class TestBall(object):
    """
    Test the Player entity.
    """

    def test_baseclass(self):
        """
        The Ball must be a subclass of Entity.

        :return:
        """
        assert issubclass(rootspace.pong.entities.Ball, sdl2.ext.Entity)

    def test_ball(self):
        """
        The Ball must have a Sprite and a Velocity component.

        :return:
        """

        ball = rootspace.pong.entities.Ball(sdl2.ext.World(), sdl2.ext.Sprite())

        assert isinstance(ball.sprite, sdl2.ext.Sprite)
        assert isinstance(ball.velocity, rootspace.pong.components.Velocity)