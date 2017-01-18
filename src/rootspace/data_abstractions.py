# -*- coding: utf-8 -*-

"""
Define data abstractions for various concepts.
"""

import attr
import enum
from attr.validators import instance_of
from .utilities import iterable_of
import glfw
import math
from OpenGL.GL import GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT


@attr.s
class ContextData(object):
    """
    Contains simple Context data.
    """
    default_config_dir = ".config"
    default_resources_dir = "resources"
    default_config_file = "config.json"
    default_keymap_file = "keymap.json"

    delta_time = attr.ib(default=0.01, validator=instance_of(float))
    max_frame_duration = attr.ib(default=0.25, validator=instance_of(float))
    epsilon = attr.ib(default=1e-5, validator=instance_of(float))
    window_title = attr.ib(default="Untitled", validator=instance_of(str))
    window_shape = attr.ib(default=(1024, 768), validator=iterable_of(tuple, int), convert=tuple)
    window_hint_context_version_major = attr.ib(default=3, validator=instance_of(int))
    window_hint_context_version_minor = attr.ib(default=3, validator=instance_of(int))
    window_hint_opengl_forward_compat = attr.ib(default=True, validator=instance_of(bool))
    window_hint_opengl_profile = attr.ib(default=glfw.OPENGL_CORE_PROFILE, validator=instance_of(int))
    swap_interval = attr.ib(default=1, validator=instance_of(int))
    clear_color = attr.ib(default=(0, 0, 0, 1), validator=iterable_of(tuple, int), convert=tuple)
    clear_bits = attr.ib(default=(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT), validator=instance_of(int))
    field_of_view = attr.ib(default=math.pi, validator=instance_of(float))
    near_plane = attr.ib(default=0.1, validator=instance_of(float))
    far_plane = attr.ib(default=100.0, validator=instance_of(float))

    @property
    def window_hints(self):
        """
        Return the GLFW window hints as dictionary.

        :return:
        """
        window_hints = dict()
        for k, v in attr.asdict(self, filter=lambda a, v: a.name.startswith("window_hint")).items():
            name = getattr(glfw, k.replace("window_hint_", "").upper())
            window_hints[name] = v

        return window_hints

    @classmethod
    def from_dict(cls, **config):
        """
        Create an instance from a dictionary.

        :param config:
        :return:
        """
        modified_attributes = {a.name: config[a.name] for a in attr.fields(cls) if a.name in config}
        return cls(**modified_attributes)


@attr.s
class KeyMap(object):
    """
    KeyMap shall hold all known keys and corresponding actions.
    """
    class Key(enum.Enum):
        A = glfw.KEY_A
        D = glfw.KEY_D
        S = glfw.KEY_S
        W = glfw.KEY_W
        X = glfw.KEY_X
        Z = glfw.KEY_Z

        @classmethod
        def coerce(cls, value):
            if isinstance(value, cls):
                return value
            elif isinstance(value, str):
                try:
                    return cls[value]
                except KeyError:
                    raise ValueError("Key {} is not known.".format(value))
            else:
                raise ValueError("Key {} is not known.".format(value))

    _left = attr.ib(validator=instance_of(Key), convert=Key.coerce)
    _right = attr.ib(validator=instance_of(Key), convert=Key.coerce)
    _up = attr.ib(validator=instance_of(Key), convert=Key.coerce)
    _down = attr.ib(validator=instance_of(Key), convert=Key.coerce)
    _forward = attr.ib(validator=instance_of(Key), convert=Key.coerce)
    _backward = attr.ib(validator=instance_of(Key), convert=Key.coerce)

    @property
    def left(self):
        return self._left.value

    @property
    def right(self):
        return self._right.value

    @property
    def up(self):
        return self._up.value

    @property
    def down(self):
        return self._down.value

    @property
    def forward(self):
        return self._forward.value

    @property
    def backward(self):
        return self._backward.value

    @classmethod
    def from_dict(cls, **config):
        """
        Create an instance from a dictionary.

        :param config:
        :return:
        """
        return cls(**config)

    def __iter__(self):
        """
        Allow iteration over the KeyMap member variables.

        :return:
        """
        for member in attr.astuple(self):
            yield member.value
