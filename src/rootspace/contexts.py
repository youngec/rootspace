# -*- coding: utf-8 -*-

import collections
import json
import os.path
import shutil
import logging

import attr
import sdl2.render
import sdl2.sdlttf
import sdl2.ext
from sdl2.video import SDL_WINDOW_SHOWN, SDL_WINDOW_RESIZABLE
from attr.validators import instance_of

from .worlds import World
from .exceptions import SDLTTFError


@attr.s
class Context(object):
    """
    The Context is used by the Engine to set the main loop parameters,
    the systems, entities, resources, states, etc.
    """
    Data = collections.namedtuple("Data", (
        "delta_time", "max_frame_duration", "epsilon", "window_title", "window_shape",
        "window_flags", "render_scale_quality", "render_color"
    ))

    default_ctx = Data(
        delta_time=0.01,
        max_frame_duration=0.25,
        epsilon=1e-5,
        window_title="Untitled",
        window_shape=(800, 600),
        window_flags=(SDL_WINDOW_SHOWN | SDL_WINDOW_RESIZABLE),
        render_scale_quality=b"0",
        render_color=(0, 0, 0, 1)
    )
    default_config_dir = ".config"
    default_resources_dir = "resources"
    default_config_file = "config.json"

    _name = attr.ib(validator=instance_of(str))
    _resources_root = attr.ib(validator=instance_of(str))
    _states_root = attr.ib(validator=instance_of(str))
    _data = attr.ib(validator=instance_of(Data), repr=False)
    _resources = attr.ib(validator=instance_of((type(None), sdl2.ext.Resources)))
    _window = attr.ib(validator=instance_of((type(None), sdl2.ext.Window)))
    _renderer = attr.ib(validator=instance_of((type(None), sdl2.ext.Renderer)))
    _world = attr.ib(validator=instance_of((type(None), World)))
    _debug = attr.ib(validator=instance_of(bool))
    _log = attr.ib(validator=instance_of(logging.Logger), repr=False)

    @classmethod
    def create(cls, name, user_home, engine_location, debug=False):
        """
        Create a new project instance.

        :param name:
        :param user_home:
        :param engine_location:
        :return:
        """
        # Specify the configuration directory and the resources directory
        resources_path = os.path.join(engine_location, cls.default_resources_dir, name)
        states_path = os.path.join(user_home, cls.default_config_dir, name)

        # Specify the configuration file paths
        config_default = os.path.join(resources_path, cls.default_config_file)
        config_user = os.path.join(states_path, cls.default_config_file)

        # Ensure that both directories (resources and states) are present
        if not os.path.exists(resources_path):
            raise FileNotFoundError(resources_path)
        elif not os.path.isdir(resources_path):
            raise NotADirectoryError(resources_path)

        if not os.path.exists(states_path):
            os.makedirs(states_path)

        # Copy the default configuration to the user-specific directory
        if not os.path.exists(config_user):
            shutil.copyfile(config_default, config_user)

        # Load the configuration
        with open(config_user, "r") as f:
            ctx = cls.default_ctx._replace(**json.load(f))

        # Create the logger
        log = logging.getLogger("{}.{}".format(__name__, cls.__name__))

        return cls(name, resources_path, states_path, ctx, None, None, None, None, debug, log)

    @property
    def data(self):
        """
        Return the context data.

        :return:
        """
        return self._data

    @property
    def resources(self):
        """
        Return a reference to the Resources or None.

        :return:
        """
        return self._resources

    @property
    def window(self):
        """
        Return a reference to the Window or None.

        :return:
        """
        return self._window

    @property
    def renderer(self):
        """
        Return a reference to the Renderer or None.

        :return:
        """
        return self._renderer

    @property
    def world(self):
        """
        Return a reference to the World or None.

        :return:
        """
        return self._world

    def _dbg(self, message):
        """
        Send a debug message.

        :param message:
        :return:
        """
        self._log.debug(message)

    def _nfo(self, message):
        """
        Send an info message.

        :param message:
        :return:
        """
        self._log.info(message)

    def _wrn(self, message):
        """
        Send a warning message.

        :param message:
        :return:
        """
        self._log.warn(message)

    def __enter__(self):
        """
        Enter the context provided by this instance.

        :return:
        """
        self._nfo("Initializing the context.")

        # Initialise SDL2 and SDL2 TTF
        self._dbg("Initializing SDL2.")
        sdl2.ext.init()

        self._dbg("Initializing SDL2 TTF.")
        if sdl2.sdlttf.TTF_Init() != 0:
            raise SDLTTFError()

        # Create the resource manager
        self._dbg("Creating the resource manager.")
        self._resources = sdl2.ext.Resources(self._resources_root)

        # Create the Window
        self._dbg("Creating the window.")
        self._window = sdl2.ext.Window(
            self._data.window_title,
            self._data.window_shape,
            flags=self._data.window_flags
        )

        # Create the Renderer
        self._dbg("Creating the renderer.")
        sdl2.SDL_SetHint(sdl2.SDL_HINT_RENDER_SCALE_QUALITY, self._data.render_scale_quality)
        self._renderer = sdl2.ext.Renderer(self._window)
        sdl2.SDL_RenderSetLogicalSize(self._renderer.sdlrenderer, *self._data.window_shape)
        self._renderer.color = sdl2.ext.Color(*self._data.render_color)

        # Create the World
        self._dbg("Creating the world.")
        self._world = World()

        return self

    def __exit__(self, *exc):
        """
        Exit the context provided by this instance.

        :param exc:
        :return:
        """
        self._nfo("Closing down the context.")
        self._dbg("Deleting the Resources, Window, Renderer and World instances.")
        self._world = None
        self._renderer = None
        self._window = None
        self._resources = None

        self._dbg("Quitting SDL2.")
        sdl2.ext.quit()
        return False
