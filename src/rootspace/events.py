# -*- coding: utf-8 -*-

"""The following classes encapsulate GLFW event concepts."""

import attr


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
