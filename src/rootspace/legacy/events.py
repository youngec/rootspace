# -*- coding: utf-8 -*-

"""
The following classes encapsulate GLFW events.
"""

import abc
from typing import Any


class Event(object, metaclass=abc.ABCMeta):
    """
    Abstract base class of an event.
    """
    pass


class KeyEvent(Event):
    """
    A wrapper around the GLFW key event. 
    Contains information about key presses.
    """
    def __init__(self, window: Any, key: int,
                 scan_code: int, action: int, mods: int) -> None:
        self.window = window
        self.key = key
        self.scan_code = scan_code
        self.action = action
        self.mods = mods


class CharEvent(Event):
    """
    A wrapper around the GLFW character event. 
    Contains text input information.
    """
    def __init__(self, window: Any, code_point: int) -> None:
        self.window = window
        self.code_point = code_point


class CursorEvent(Event):
    """
    A wrapper around the GLFW cursor event. 
    Contains cursor movement information.
    """
    def __init__(self, window: Any, xpos, ypos) -> None:
        self.window = window
        self.xpos = xpos
        self.ypos = ypos


class CursorEnterEvent(Event):
    """
    A wrapper around the GLFW cursor enter event.
    Contains information about whether the cursor resides within the window.
    """
    def __init__(self, window: Any, entered: bool) -> None:
        self.window = window
        self.entered = entered


class MouseButtonEvent(Event):
    """
    A wrapper around the GLFW mouse button event.
    Contains information about the mouse button clicks.
    """
    def __init__(self, window: Any, button, action, mods) -> None:
        self.window = window
        self.button = button
        self.action = action
        self.mods = mods


class ScrollEvent(Event):
    """
    A wrapper around the GLFW scroll wheel event.
    Contains information about the mouse scroll wheel.
    """
    def __init__(self, window: Any, xoffset: int,
                 yoffset: int) -> None:
        self.window = window
        self.xoffset = xoffset
        self.yoffset = yoffset


class SceneEvent(Event):
    """
    Describes the request for a scene change.
    """
    def __init__(self, name: str) -> None:
        self.name = name
