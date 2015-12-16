# coding:utf-8

"""Docstring"""

import math

import pytest

import config.generic


class TestVelocity(object):
    """
    Test the Velocity component.
    """

    @pytest.fixture
    def vel(self):
        return rootspace.pong.components.Velocity()

    def test_velocity(self, vel):
        """
        The initial velocity and delta vector must be zero.

        :return:
        """

        assert vel.vx == 0
        assert vel.vy == 0

        assert vel._dx == 0
        assert vel._dy == 0

        assert hasattr(vel, "default")

    def test_reset(self, vel):
        """
        The reset method must result in a non-zero velocity that
        closely matches the default velocity in magnitude.

        :return:
        """

        vel.reset()

        vr = math.sqrt(pow(vel.vx, 2) + pow(vel.vy, 2))
        assert abs(vel.default - vr) < config.generic.EPS

    def test_up(self, vel):
        """
        The up method must result in a negative y-velocity
        that matches the default velocity.

        :return:
        """

        vel.up()

        assert vel.vx == 0
        assert vel.vy == -vel.default

    def test_down(self, vel):
        """
        The down method must result in a positive y-velocity
        that matches the default velocity.

        :return:
        """

        vel.down()

        assert vel.vx == 0
        assert vel.vy == vel.default

    def test_stop(self, vel):
        """
        The stop method must result in a zero velocity.

        :return:
        """

        vel.stop()

        assert vel.vx == 0
        assert vel.vy == 0


class TestPlayerData(object):
    """
    Test the PlayerData component.
    """

    def test_ai(self):
        """
        The ai field of PlayerData must be false at first.

        :return:
        """

        playerdata = rootspace.pong.components.PlayerData()

        assert not playerdata.ai