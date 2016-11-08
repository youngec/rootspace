# -*- coding: utf-8 -*-

import abc
import collections
import gzip
import json
import os.path
import shelve
import shutil
import logging

import attr
import sdl2.render
import sdl2.ext
from sdl2.video import SDL_WINDOW_SHOWN, SDL_WINDOW_RESIZABLE
from attr.validators import instance_of

from .entities import LocalComputer
from .systems import DisplaySystem, DisplayInterpreterSystem, TextInputSystem, ShellSystem
from .utilities import merge_configurations
from .worlds import World


@attr.s
class Context(object):
    """
    The Context is used by the Engine to set the main loop parameters,
    the systems, entities, resources, states, etc.
    """
    Data = collections.namedtuple("Data", (
        "delta_time", "max_frame_duration", "epsilon", "window_title", "window_shape",
        "window_flags", "render_scale_quality", "render_color", "window", "renderer", "world"
    ))

    default_ctx = Data(
        delta_time=0.01,
        max_frame_duration=0.25,
        epsilon=1e-5,
        window_title="Untitled",
        window_shape=(800, 600),
        window_flags=(SDL_WINDOW_SHOWN | SDL_WINDOW_RESIZABLE),
        render_scale_quality=b"0",
        render_color=(0, 0, 0, 1),
        window=None,
        renderer=None,
        world=None
    )
    default_config_dir = ".config"
    default_resources_dir = "resources"
    default_config_file = "config.json"

    _name = attr.ib(validator=instance_of(str))
    _resources_root = attr.ib(validator=instance_of(str))
    _states_root = attr.ib(validator=instance_of(str))
    _ctx = attr.ib(validator=instance_of(Data), repr=False)
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

        return cls(name, resources_path, states_path, ctx, debug, log)

    @property
    def data(self):
        """
        Return the context data.

        :return:
        """
        return self._ctx

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
        self._nfo("Initializing all components of the project.")

        # Initialise SDL2 and SDL2 TTF
        self._dbg("Initializing SDL2.")
        sdl2.ext.init()

        self._dbg("Initializing SDL2 TTF.")
        if sdl2.sdlttf.TTF_Init() != 0:
            raise SDLTTFError()

        # Create the Window
        self._dbg("Creating the window.")
        self._ctx.window = sdl2.ext.Window(
            self._ctx.window_title,
            self._ctx.window_shape,
            flags=self._ctx.window_flags
        )

        # Create the Renderer
        self._dbg("Creating the renderer.")
        sdl2.SDL_SetHint(sdl2.SDL_HINT_RENDER_SCALE_QUALITY, self._ctx.render_scale_quality)
        self._ctx.renderer = sdl2.ext.Renderer(self._ctx.window)
        sdl2.SDL_RenderSetLogicalSize(self._ctx.renderer.sdlrenderer, *self._ctx.window_shape)
        self._ctx.renderer.color = sdl2.ext.Color(*self._ctx.render_color)

        # Create the World
        self._dbg("Creating the world.")
        self._ctx.world = World()

        return self

    def __exit__(self, *exc):
        """
        Exit the context provided by this instance.

        :param exc:
        :return:
        """
        try:
            self._nfo("Closing down SDL2.")
            sdl2.ext.quit()
        except Exception:
            return True
        else:
            return False

