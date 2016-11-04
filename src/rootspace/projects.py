# -*- coding: utf-8 -*-

import abc
import os.path

import attr
import sdl2.video
from attr.validators import instance_of

from .entities import LocalComputer
from .systems import DisplaySystem, DisplayInterpreterSystem, TextInputSystem, ShellSystem
from .utilities import merge_configurations


@attr.s
class Project(object, metaclass=abc.ABCMeta):
    _configuration = attr.ib(validator=instance_of(dict))
    _debug = attr.ib(validator=instance_of(bool))

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
            "section": "Resources",
            "name": "Path"
        }
    }

    @property
    def configuration(self):
        return self._configuration

    @classmethod
    def create(cls, resource_path, config_path="", debug=False, **kwargs):
        """
        Create a project instance.

        :param resource_path:
        :param config_path:
        :param debug:
        :param kwargs:
        :return:
        """
        # Define configuration search paths (giving precedence to user configurations)
        cfg_paths = (
            config_path,
            os.path.join(resource_path, "config.ini")
        )

        # Update the default configuration
        default_config = cls._default_config.copy()
        default_config["resource_path"]["value"] = resource_path

        # Load the conglomerate configuration
        configuration = merge_configurations(kwargs, cfg_paths, default_config)

        return cls(
            configuration=configuration,
            debug=debug,
            **kwargs
        )

    @abc.abstractmethod
    def load_scene(self, world, renderer, resource_manager, systems, entities, scene=None):
        """
        Load the specified scene.

        :param world:
        :param renderer:
        :param resource_manager:
        :param systems:
        :param entities:
        :param scene:
        :return:
        """
        pass


@attr.s
class RootSpace(Project):
    """
    Implementation of the Rootspace project.
    """

    def load_scene(self, world, renderer, resource_manager, systems, entities, scene=None):
        if scene is None:
            sys = (
                DisplaySystem.create(renderer, resource_manager),
                DisplayInterpreterSystem.create(),
                TextInputSystem.create(),
                ShellSystem.create()
            )
            ent = (
                LocalComputer.create(world, resource_manager=resource_manager, renderer=renderer),
            )
            systems.extend(sys)
            entities.extend(ent)
