# coding:utf-8

"""Docstring"""

import pytest
import sdl2.ext


class TestMovementSystem(object):
    """
    Test the MovementSystem.
    """

    @pytest.fixture
    def system(self):
        return src.rootspace.pong.systems.MovementSystem(0, 1, 100, 200)

    def test_baseclass(self):
        """
        MovementSystem must be a subclass of Applicator.

        :return:
        """

        assert issubclass(src.rootspace.pong.systems.MovementSystem, sdl2.ext.Applicator)

    def test_componenttypes(self, system):
        """
        MovementSystem must accept component types Velocity and Sprite.

        :return:
        """

        assert issubclass(system.componenttypes[0], src.rootspace.pong.components.Velocity)
        assert issubclass(system.componenttypes[1], sdl2.ext.Sprite)

    def test_boundaries(self, system):
        """
        MovementSystem must have frame boundary fields.

        :return:
        """

        assert system.minx == 0
        assert system.miny == 1
        assert system.maxx == 100
        assert system.maxy == 200

    @pytest.mark.xfail
    def test_move(self, system):
        raise NotImplementedError()

    @pytest.mark.xfail
    def test_bound(self, system):
        raise NotImplementedError()

    @pytest.mark.xfail
    def test_process(self, system):
        raise NotImplementedError()


class TestCollisionSystem(object):
    """
    Test the CollisionSystem.
    """

    @pytest.fixture
    def system(self):
        return src.rootspace.pong.systems.CollisionSystem(0, 1, 100, 200)

    def test_baseclass(self):
        """
        CollisionSystem must be a subclass of Applicator.

        :return:
        """

        assert issubclass(src.rootspace.pong.systems.CollisionSystem, sdl2.ext.Applicator)

    def test_componenttypes(self, system):
        """
        CollisionSystem must accept component types Velocity and Sprite.

        :return:
        """

        assert issubclass(system.componenttypes[0], src.rootspace.pong.components.Velocity)
        assert issubclass(system.componenttypes[1], sdl2.ext.Sprite)

    def test_boundaries(self, system):
        """
        CollisionSystem must have frame boundary fields.

        :return:
        """

        assert system.minx == 0
        assert system.miny == 1
        assert system.maxx == 100
        assert system.maxy == 200

    def test_ball(self, system):
        """
        CollisionSystem must have a ball field.

        :param system:
        :return:
        """

        assert hasattr(system, "ball")

    @pytest.mark.xfail
    def test_overlap(self, system):
        raise NotImplementedError()

    @pytest.mark.xfail
    def test_deflect(self, system):
        raise NotImplementedError()

    @pytest.mark.xfail
    def test_bounce(self, system):
        raise NotImplementedError()

    @pytest.mark.xfail
    def test_process(self, system):
        raise NotImplementedError()


class TestTrackingAIController(object):
    """
    Test the TrackingAIController.
    """

    @pytest.fixture
    def system(self):
        return src.rootspace.pong.systems.TrackingAIController(0, 1, 100, 200)

    def test_baseclass(self):
        """
        TrackingAIController must be a subclass of Applicator.

        :return:
        """

        assert issubclass(src.rootspace.pong.systems.TrackingAIController, sdl2.ext.Applicator)

    def test_componenttypes(self, system):
        """
        TrackingAIController must accept component types PlayerData, Velocity and Sprite.

        :return:
        """

        assert issubclass(system.componenttypes[0], src.rootspace.pong.components.PlayerData)
        assert issubclass(system.componenttypes[1], src.rootspace.pong.components.Velocity)
        assert issubclass(system.componenttypes[2], sdl2.ext.Sprite)

    def test_boundaries(self, system):
        """
        TrackingAIController must have frame boundary fields.

        :return:
        """

        assert system.minx == 0
        assert system.miny == 1
        assert system.maxx == 100
        assert system.maxy == 200

    def test_ball(self, system):
        """
        TrackingAIController must have a ball field.

        :param system:
        :return:
        """

        assert hasattr(system, "ball")

    @pytest.mark.xfail
    def test_process(self, system):
        raise NotImplementedError()