# -*- coding: utf-8 -*-

import abc
import collections
import gzip
import json
import os.path
import shelve

import attr
import sdl2.render
import sdl2.video
from attr.validators import instance_of

from .entities import LocalComputer
from .systems import DisplaySystem, DisplayInterpreterSystem, TextInputSystem, ShellSystem
from .utilities import merge_configurations
from .worlds import World


@attr.s
class NewProject(object):
    """
    The project is used by the Engine to set the main loop parameters,
    the systems, entities, resources, states, etc.
    """
    State = collections.namedtuple("State", ("systems", "entities"))

    _name = attr.ib(validator=instance_of(str))
    _resources_root = attr.ib(validator=instance_of(str))
    _states_root = attr.ib(validator=instance_of(str))
    _debug = attr.ib(validator=instance_of(bool))
    _world = attr.ib(validator=instance_of(World))
    _renderer = attr.ib(validator=instance_of(sdl2.render.SDL_Renderer))

    @classmethod
    def create(cls, name, user_home, engine_location, world, renderer, debug=False):
        """
        Create a new project instance.

        :param name:
        :param user_home:
        :param engine_location:
        :return:
        """
        config_dir = ".config"
        resources_dir = "resources"

        resources_path = os.path.join(engine_location, resources_dir, name)
        states_path = os.path.join(user_home, config_dir, name)

        if not os.path.exists(resources_path):
            raise FileNotFoundError(resources_path)
        elif not os.path.isdir(resources_path):
            raise NotADirectoryError(resources_path)

        if not os.path.exists(states_path):
            os.makedirs(states_path)

        return cls(name, resources_path, states_path, world, renderer, debug)

    def load_state(self, state_name=None):
        """
        Load the specified state. If none is specified, create the initial state.

        :param state_name:
        :return:
        """
        if state_name is None:
            return self._init_state()
        elif isinstance(state_name, str):
            return self._load_state(state_name)
        else:
            raise TypeError("The parameter 'state_name' must be None or a string.")

    def save_state(self, state, state_name):
        """
        Save the specified state under the specified name.

        :param state:
        :param state_name:
        :return:
        """
        if isinstance(state_name, str):
            if isinstance(state, NewProject.State):
                self._save_state(state, state_name)
            else:
                raise TypeError("The parameter 'state' must be a NewProject.State instance.")
        else:
            raise TypeError("The parameter 'state_name' must be a string.")

    def _load_state(self, state_name):
        """
        Load the state with the specified name.

        :param state_name:
        :return:
        """
        state_file = os.path.join(self._states_root, state_name)
        with gzip.open(state_file, "rt") as sf:
            state_serialised = json.load(sf)
            return NewProject.State(**state_serialised)

    def _save_state(self, state, state_name):
        """
        Load the state with the specified name.

        :param state:
        :param state_name:
        :return:
        """
        state_file = os.path.join(self._states_root, state_name)
        with gzip.open(state_file, "wb") as sf:
            json.dump(state._asdict(), sf)

    def _init_state(self):
        """
        Load the initial state.

        :return:
        """
        pass


@attr.s
class Project(object, metaclass=abc.ABCMeta):
    _configuration = attr.ib(validator=instance_of(dict))
    _debug = attr.ib(validator=instance_of(bool))
    _systems = attr.ib(default=tuple(), validator=instance_of(tuple))
    _entities = attr.ib(default=tuple(), validator=instance_of(tuple))

    _default_config = {
        "delta_time": {
            "value": 0.01,
            "section": "Loop",
            "name": "Delta time"
        },
        "max_frame_duration": {
            "value": 0.25,
            "section": "Loop",
            "name": "Maximum frame duration"
        },
        "epsilon": {
            "value": 1e-5,
            "section": "Loop",
            "name": "Epsilon"
        },
        "window_title": {
            "value": "Untitled",
            "section": "Display",
            "name": "Window title"
        },
        "window_shape": {
            "value": (800, 600),
            "section": "Display",
            "name": "Window shape"
        },
        "window_flags": {
            "value": sdl2.video.SDL_WINDOW_SHOWN | sdl2.video.SDL_WINDOW_RESIZABLE,
            "section": "Display",
            "name": "Window flags"
        },
        "render_scale_quality": {
            "value": b"0",
            "section": "Display",
            "name": "Render scale quality"
        },
        "render_color": {
            "value": (0, 0, 0, 1),
            "section": "Display",
            "name": "Render clear color"
        },
        "resource_path": {
            "value": "resources",
            "section": "Paths",
            "name": "Resources"
        },
        "state_path": {
            "value": "state-data",
            "section": "Paths",
            "name": "States"
        }
    }

    @property
    def configuration(self):
        return self._configuration

    @classmethod
    def create(cls, resource_path, state_path, config_path="", debug=False, **kwargs):
        """
        Create a project instance.

        :param resource_path:
        :param config_path:
        :param debug:
        :param kwargs:
        :return:
        """
        # Create the state directory if it's not already present
        if not os.path.exists(state_path):
            os.makedirs(state_path)

        # Define configuration search paths (giving precedence to user configurations)
        cfg_paths = (
            config_path,
            os.path.join(resource_path, "config.ini")
        )

        # Update the default configuration
        default_config = cls._default_config.copy()
        default_config["resource_path"]["value"] = resource_path
        default_config["state_path"]["value"] = state_path

        # Load the conglomerate configuration
        configuration = merge_configurations(kwargs, cfg_paths, default_config)

        return cls(
            configuration=configuration,
            debug=debug,
            **kwargs
        )

    @abc.abstractmethod
    def load_state(self, world, renderer, resource_manager, systems, entities, state_name):
        """
        Load the specified state.

        :param world:
        :param renderer:
        :param resource_manager:
        :param systems:
        :param entities:
        :param state_name:
        :return:
        """
        pass

    @abc.abstractmethod
    def save_state(self, state_name):
        """
        Save the specified state.

        :param state_name:
        :return:
        """
        pass


@attr.s
class RootSpace(Project):
    """
    Implementation of the Rootspace project.
    """
    def load_state(self, world, renderer, resource_manager, systems, entities, state_name=None):
        if state_name is None:
            self._systems = (
                DisplaySystem.create(renderer, resource_manager),
                DisplayInterpreterSystem.create(),
                TextInputSystem.create(),
                ShellSystem.create()
            )
            self._entities = (
                LocalComputer.create(world, resource_manager=resource_manager, renderer=renderer),
            )
        else:
            state_file = os.path.join(self._configuration["state_path"], state_name)
            with shelve.open(state_file) as db:
                self._systems = db["systems"]
                self._entities = db["entities"]

        systems.extend(self._systems)
        entities.extend(self._entities)

    def save_state(self, state_name):
        state_file = os.path.join(self._configuration["state_path"], state_name)
        with shelve.open(state_file) as db:
            db["systems"] = self._systems
            db["entities"] = self._entities

