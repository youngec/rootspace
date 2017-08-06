# -*- coding: utf-8 -*-

import enum
import json
import pathlib
from typing import Any, Dict, Union, Type

import glfw

from .ecs.serialization import SerDeTrait, SER


class Key(enum.IntEnum):
    """
    Provides a mapping of GLFW key constants to a Python `IntEnum`.
    This way, values can be serialized in a more readable form.
    """
    A = glfw.KEY_A
    D = glfw.KEY_D
    S = glfw.KEY_S
    W = glfw.KEY_W
    X = glfw.KEY_X
    Z = glfw.KEY_Z
    R = glfw.KEY_R

    @classmethod
    def coerce(cls, value: Union["Key", str, int]) -> "Key":
        """
        Coerce string or integer values to a `Key` enum.
        """
        if isinstance(value, Key):
            return value
        elif isinstance(value, str):
            try:
                return cls[value]
            except KeyError:
                raise ValueError("Key {} is not known.".format(value))
        elif isinstance(value, int):
            try:
                return min(k for k in cls if k == value)
            except ValueError:
                raise ValueError("Key {} is not known.".format(value))
        else:
            raise ValueError("Key {} is not known.".format(value))

    @classmethod
    def to_value(cls, value: Union["Key", str, int]) -> int:
        """
        Use `Key.coerce` to convert the input value to a GLFW key constant.
        """
        return cls.coerce(value).value

    @classmethod
    def to_name(cls, value: Union["Key", str, int]) -> str:
        """
        Use `Key.coerce` to convert the input value to the string
        representation of a key.
        """
        return cls.coerce(value).name


class KeyMap(SerDeTrait):
    def __init__(self, left: int, right: int, up: int, down: int, forward: int, backward: int, reset: int) -> None:
        self.left = left
        self.right = right
        self.up = up
        self.down = down
        self.forward = forward
        self.backward = backward
        self.reset = reset

    @classmethod
    def new(cls) -> "KeyMap":
        return cls(
            left=glfw.KEY_A,
            right=glfw.KEY_D,
            up=glfw.KEY_Z,
            down=glfw.KEY_X,
            forward=glfw.KEY_W,
            backward=glfw.KEY_S,
            reset=glfw.KEY_R
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "left": Key.to_name(self.left),
            "right": Key.to_name(self.right),
            "up": Key.to_name(self.up),
            "down": Key.to_name(self.down),
            "forward": Key.to_name(self.forward),
            "backward": Key.to_name(self.backward),
            "reset": Key.to_name(self.reset)
        }

    @classmethod
    def from_dict(cls: Type[SER], obj: Dict[str, Any]) -> SER:
        return cls(
            left=Key.to_value(obj["left"]),
            right=Key.to_value(obj["right"]),
            up=Key.to_value(obj["up"]),
            down=Key.to_value(obj["down"]),
            forward=Key.to_value(obj["forward"]),
            backward=Key.to_value(obj["backward"]),
            reset=Key.to_value(obj["reset"])
        )
