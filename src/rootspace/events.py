# -*- coding: utf-8 -*-

"""The following classes encapsulate GLFW event concepts."""

import attr

from attr.validators import instance_of


@attr.s
class Event(object):
    pass


@attr.s
class KeyEvent(Event):
    window = attr.ib()
    key = attr.ib()
    scancode = attr.ib()
    action = attr.ib()
    mods = attr.ib()


@attr.s
class CharEvent(Event):
    window = attr.ib()
    codepoint = attr.ib()


@attr.s
class CursorEvent(Event):
    window = attr.ib()
    xpos = attr.ib()
    ypos = attr.ib()


@attr.s
class CursorEnterEvent(Event):
    window = attr.ib()
    entered = attr.ib()


@attr.s
class MouseButtonEvent(Event):
    window = attr.ib()
    button = attr.ib()
    action = attr.ib()
    mods = attr.ib()


@attr.s
class ScrollEvent(Event):
    window = attr.ib()
    xoffset = attr.ib()
    yoffset = attr.ib()


@attr.s
class SceneEvent(Event):
    name = attr.ib(validator=instance_of(str))
