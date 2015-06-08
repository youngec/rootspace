# coding:utf-8

"""Docstring"""

import logging
import unittest.mock

import sdl2.ext
import collections
import pytest
import engine.core


class TestCore(object):
    """
    Performs unit tests on the Core class. The Core is in a sense the general
    object manager.
    """

    @pytest.fixture
    def core(self):
        """
        Generate a Core instance.

        :return:
        """

        return engine.core.Core()

    def test_attrs(self, core):
        """
        Ensure that the Core class provides the following member variables:

        _location: str
        _logger
        _resources
        _window
        _renderer
        _factory
        _world
        _systems: dict
        _entities: collections.OrderedDict

        :param core:
        :return:
        """

        # The project location is important for the logging
        # configuration as well as for the contrib database.
        assert isinstance(core._location, str)

        # Ensure that the Core provides a logger instance for subclasses.
        assert hasattr(core, "_logger")
        assert hasattr(core, "_Core__logger")

        # The Core needs to provide the following SDL2 object containers.
        assert hasattr(core, "_resources")  # sdl2.ext.Resources
        assert hasattr(core, "_window")  # sdl2.ext.Window
        assert hasattr(core, "_renderer")  # sdl2.ext.Renderer
        assert hasattr(core, "_factory")  # sdl2.ext.SpriteFactory
        assert hasattr(core, "_world")  # sdl2.ext.World

        # The following members are dictionaries of sdl2.ext.Entity and sdl2.ext.System,
        # respectively. They are used to reduce the number of similar member variables
        # and to ease cleanup in the end. Note that the order of systems must be known!
        assert isinstance(core._entities, dict)
        assert isinstance(core._systems,  collections.OrderedDict)

    def test_execute(self, monkeypatch, core):
        """
        Ensure that the core has a public method execute that
        calls _startup, _loop and _shutdown exactly once, even
        in case of an exception.

        :param monkeypatch:
        :param core:
        :return:
        """

        # The execute method should be public!
        assert hasattr(core, "execute")

        # The execute method must call _startup, _loop and _shutdown exactly once each.
        magic1 = unittest.mock.MagicMock()
        magic2 = unittest.mock.MagicMock()
        magic3 = unittest.mock.MagicMock()
        monkeypatch.setattr(core, "_startup", magic1)
        monkeypatch.setattr(core, "_loop", magic2)
        monkeypatch.setattr(core, "_shutdown", magic3)

        core.execute()

        magic1.assert_called_once_with()
        magic2.assert_called_once_with()
        magic3.assert_called_once_with()

        # The execute must call _shutdown even if there was an exception.
        magic1.reset_mock()
        magic3.reset_mock()

        def mock_loop():
            raise RuntimeError()

        monkeypatch.setattr(core, "_loop", mock_loop)

        with pytest.raises(RuntimeError):
            core.execute()

        magic1.assert_called_once_with()
        magic3.assert_called_once_with()

    @pytest.mark.xfail
    def test_startup(self, core):
        raise NotImplementedError()

    @pytest.mark.xfail
    def test_config_location(self):
        raise NotImplementedError()

    @pytest.mark.xfail
    def test_config_logger(self):
        raise NotImplementedError()

    def test_create_systems(self, recwarn, core):
        """
        In the Core class, this method should do nothing but issue a warning.

        :param recwarn:
        :param core:
        :return:
        """

        core._create_systems()

        w = recwarn.pop(engine.core.NotImplementedWarning)
        assert issubclass(w.category, engine.core.NotImplementedWarning)

    def test_add_entities(self, recwarn, core):
        """
        In the Core class, this method should do nothing but issue a warning.

        :param recwarn:
        :param core:
        :return:
        """

        core._add_entities()

        w = recwarn.pop(engine.core.NotImplementedWarning)
        assert issubclass(w.category, engine.core.NotImplementedWarning)

    @pytest.mark.xfail
    def test_loop(self):
        raise NotImplementedError()

    def test_process_event(self, recwarn, core):
        """
        In the Core class, this method should do nothing but issue a warning.

        :param recwarn:
        :param core:
        :return:
        """

        core._process_event(None)

        w = recwarn.pop(engine.core.NotImplementedWarning)
        assert issubclass(w.category, engine.core.NotImplementedWarning)

    def test_shutdown(self, monkeypatch, core):
        """
        Ensure that the shutdown method deletes all references and closes down SDL2 and the logging system.

        :param monkeypatch:
        :param core:
        :return:
        """

        magic_sdl = unittest.mock.MagicMock()
        magic_logging = unittest.mock.MagicMock()

        monkeypatch.setattr(core, '_Core__logger', unittest.mock.MagicMock())
        monkeypatch.setattr(sdl2.ext, 'quit', magic_sdl)
        monkeypatch.setattr(logging, 'shutdown', magic_logging)

        core._shutdown()

        # Ensure that the entities and systems dictionaries are empty
        assert len(core._entities) == 0
        assert len(core._systems) == 0

        # Ensure that all references are set to None
        assert core._factory is None
        assert core._world is None
        assert core._renderer is None
        assert core._window is None
        assert core._resources is None

        # Ensure that the logger is set to None
        assert core._logger is None
        assert core._Core__logger is None

        # Ensure that both sdl2.ext.quit() and logging.shutdown() are called exactly once.
        magic_sdl.assert_called_once_with()
        magic_logging.assert_called_once_with()


class TestUpdateRenderWorld(object):
    @pytest.fixture
    def world(self):
        return engine.core.UpdateRenderWorld()

    @pytest.mark.xfail
    def test_update(self):
        raise NotImplementedError()

    @pytest.mark.xfail
    def test_render(self):
        raise NotImplementedError()