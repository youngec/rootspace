# coding:utf-8

"""Docstring"""

import unittest.mock

import sdl2.ext
import pytest
import config.generic
import engine.core
import pong.core
import pong.systems
import pong.entities


class TestPongCore(object):
    """
    The PongCore inherits from Core and is basically a
    simplistic implementation of the pong game.
    """

    @pytest.fixture
    def core(self):
        return pong.core.PongCore()

    def test_baseclass(self):
        """
        PongCore must be a subclass of engine.core.Core.

        :return:
        """

        assert issubclass(pong.core.PongCore, engine.core.Core)

    def test_create_systems(self, monkeypatch, core):
        """
        The _create_systems method must create a MovementSystem,
        a CollisionSystem and a TrackingAIController and add their
        references to self._systems.

        :param monkeypatch:
        :param core:
        :return:
        """

        mock_movement = unittest.mock.MagicMock()
        mock_collision = unittest.mock.MagicMock()
        mock_ai = unittest.mock.MagicMock()

        monkeypatch.setattr(pong.systems, "MovementSystem", mock_movement)
        monkeypatch.setattr(pong.systems, "CollisionSystem", mock_collision)
        monkeypatch.setattr(pong.systems, "TrackingAIController", mock_ai)

        core._create_systems()

        # All systems must have been added to the _systems dictionary
        assert len(core._systems) == 3

        # All systems must have been created once with given arguments.
        mock_movement.assert_called_once_with(0, 0, *config.generic.WINDOW_SHAPE)
        mock_collision.assert_called_once_with(0, 0, *config.generic.WINDOW_SHAPE)
        mock_ai.assert_called_once_with(0, 0, *config.generic.WINDOW_SHAPE)

    def test_add_entities(self, monkeypatch, core):
        """
        The _add_entities method must create two Players and a Ball. Both CollisionSystem and TackingAIContorller
        need a reference to the ball.

        :param monkeypatch:
        :param core:
        :return:
        """

        monkeypatch.setattr(core, "_logger", unittest.mock.MagicMock())
        monkeypatch.setattr(core, "_factory", unittest.mock.MagicMock(spec=sdl2.ext.SpriteFactory))
        monkeypatch.setattr(core, "_world", unittest.mock.MagicMock(spec=sdl2.ext.World))

        core._systems["collision"] = unittest.mock.MagicMock()
        core._systems["aitracker"] = unittest.mock.MagicMock()

        mock_player = unittest.mock.MagicMock()
        mock_ball = unittest.mock.MagicMock()

        monkeypatch.setattr(pong.entities, "Player", mock_player)
        monkeypatch.setattr(pong.entities, "Ball", mock_ball)

        core._add_entities()

        assert all([a in core._entities.keys() for a in ("player1", "player2", "ball")])
        mock_player.assert_any_call(core._world, unittest.mock.ANY, position=unittest.mock.ANY)
        mock_player.assert_any_call(core._world, unittest.mock.ANY, position=unittest.mock.ANY, ai=unittest.mock.ANY)
        mock_ball.assert_any_call(core._world, unittest.mock.ANY, position=unittest.mock.ANY)
        core._entities["ball"].velocity.reset.assert_called_once_with()
        assert core._systems["collision"].ball == core._entities["ball"]
        assert core._systems["aitracker"].ball == core._entities["ball"]

    def test_process_event(self):
        """
        This test will always pass.

        :return:
        """

        assert True