# -*- coding: utf-8 -*-

import abc
import attr
import enum
from attr.validators import instance_of
import sdl2.stdinc
import sdl2.render
from ctypes import byref, c_int

from .exceptions import SDLError


@attr.s(slots=True)
class Sprite(object, metaclass=abc.ABCMeta):
    x = attr.ib(validator=instance_of(int))
    y = attr.ib(validator=instance_of(int))
    depth = attr.ib(validator=instance_of(int))

    @property
    def position(self):
        """
        The position of the top-left corner of the Sprite

        :return:
        """
        return self.x, self.y

    @position.setter
    def position(self, value):
        """
        Set position of the Sprite using its top-left corner.

        :param value:
        :return:
        """
        self.x = value[0]
        self.y = value[1]

    @property
    @abc.abstractmethod
    def size(self):
        """
        Return the size of the Sprite as tuple.

        :return:
        """
        pass

    @property
    def area(self):
        """
        Return the rectangle occupied by the sprite as tuple.

        :return:
        """
        return self.x, self.y, self.x + self.size[0], self.y + self.size[1]


@attr.s(slots=True)
class TextureSprite(Sprite):
    """
    A simple texture-based sprite.
    """
    texture = attr.ib(validator=instance_of(sdl2.render.SDL_Texture))

    @property
    def size(self):
        flags = sdl2.stdinc.Uint32()
        access = c_int()
        w = c_int()
        h = c_int()
        if sdl2.render.SDL_QueryTexture(self.texture, byref(flags), byref(access), byref(w), byref(h)) == -1:
            raise SDLError("Cannot determine the TextureSprite size by SDL_QueryTexture().")

        return w.value, h.value


@attr.s(slots=True)
class MachineState(object):
    """
    Describe whether a particular entity is in working order or not.
    """
    class MSE(enum.Enum):
        """
        Enumeration of the machine states.
        """
        fatal = -1
        power_off = 0
        power_up = 1
        ready = 2
        power_down = 3

    state = attr.ib(default=MSE.power_off, validator=instance_of(MSE))


@attr.s(slots=True)
class NetworkState(object):
    """
    Describe the state of the network subsystem.
    """
    address = attr.ib(default=0, validator=instance_of(int))
    connected = attr.ib(default=attr.Factory(list), validator=instance_of(list))


@attr.s(slots=True)
class FileSystem(object):
    """
    Describe the state of the file system.
    """
    # FIXME: This design does not account for permissions.
    default_hierarchy = {
        "/": {
            "bin": {},
            "dev": {},
            "etc": {
                "passwd": 0x0001
            },
            "home": {},
            "root": {},
            "tmp": {},
            "usr": {}
        }
    }

    default_database = {
        0x0001: {
            "root": {
                "password": "x",
                "UID": 0,
                "GID": 0,
                "GECOS": "root",
                "directory": "/root",
                "shell": "/bin/sh"
            }
        }
    }

    hierarchy = attr.ib(default=default_hierarchy, validator=instance_of(dict))
    database = attr.ib(default=default_database, validator=instance_of(dict))


@attr.s(slots=True)
class TerminalDisplay(object):
    pass
