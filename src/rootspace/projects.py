# -*- coding: utf-8 -*-

import collections
import os.path

import attr
import sdl2.video
from attr.validators import instance_of

from .utilities import merge_configurations


@attr.s
class Project(object):
    _name = attr.ib(validator=instance_of(str))
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
        }
    }

    @property
    def name(self):
        return self._name

    @property
    def configuration(self):
        return self._configuration

    @classmethod
    def create(cls, name, user_home, resource_path, config_path="", debug=False, **kwargs):
        # Define configuration search paths (giving precedence to user configurations)
        cfg_paths = (
            config_path,
            os.path.join(user_home, ".config", name, "config.ini"),
            os.path.join(resource_path, name, "config.ini")
        )

        # Load the conglomerate configuration
        configuration = merge_configurations(cfg_paths, kwargs, cls._default_config)
        configuration["resource_path"] = resource_path

        return cls(name, configuration, debug)

    def create_systems(self):
        return collections.OrderedDict()

    def create_entities(self):
        return list()
