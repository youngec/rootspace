# -*- coding: utf-8 -*-

"""The following classes encapsulate GLFW event concepts."""

import enum
import attr
import glfw
from attr.validators import instance_of


@attr.s
class KeyEvent(object):
    window = attr.ib()
    key = attr.ib()
    scancode = attr.ib()
    action = attr.ib()
    mods = attr.ib()


@attr.s
class CharEvent(object):
    window = attr.ib()
    codepoint = attr.ib()


@attr.s
class CursorEvent(object):
    window = attr.ib()
    xpos = attr.ib()
    ypos = attr.ib()


@attr.s
class CursorEnterEvent(object):
    window = attr.ib()
    entered = attr.ib()


@attr.s
class MouseButtonEvent(object):
    window = attr.ib()
    button = attr.ib()
    action = attr.ib()
    mods = attr.ib()


@attr.s
class ScrollEvent(object):
    window = attr.ib()
    xoffset = attr.ib()
    yoffset = attr.ib()


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

    def __iter__(self):
        """
        Allow iteration over the KeyMap member variables.

        :return:
        """
        for member in attr.astuple(self):
            yield member.value
