# -*- coding: utf-8 -*-

import enum

import attr
import numpy
import sdl2.pixels
import sdl2.render
import sdl2.stdinc
import sdl2.surface
import sdl2.surface
from attr.validators import instance_of

from .exceptions import SDLError


@attr.s(slots=True)
class Sprite(object):
    x = attr.ib(validator=instance_of(int))
    y = attr.ib(validator=instance_of(int))
    _width = attr.ib(validator=instance_of(int))
    _height = attr.ib(validator=instance_of(int))
    _depth = attr.ib(validator=instance_of(int))
    _renderer = attr.ib(default=None)
    _surface = attr.ib(default=None)
    _texture = attr.ib(default=None)

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
        self.x, self.y = value

    @property
    def shape(self):
        """
        Return the size of the Sprite as tuple.

        :return:
        """
        return self._width, self._height

    @property
    def depth(self):
        """
        Return the render depth of the Sprite.

        :return:
        """
        return self._depth

    @depth.setter
    def depth(self, value):
        """
        Set the render depth.

        :param value:
        :return:
        """
        self._depth = value

    @property
    def surface(self):
        return self._surface

    @property
    def texture(self):
        return self._texture

    @texture.setter
    def texture(self, value):
        sdl2.render.SDL_DestroyTexture(self._texture)
        self._texture = value

    @texture.deleter
    def texture(self):
        sdl2.render.SDL_DestroyTexture(self._texture)

    @classmethod
    def create(cls, position, shape, depth=0,
               renderer=None, pixel_format=sdl2.pixels.SDL_PIXELFORMAT_RGBA8888,
               access=sdl2.render.SDL_TEXTUREACCESS_STATIC, bpp=32, masks=(0, 0, 0, 0)):
        if renderer is not None:
            sdl_renderer = renderer.renderer
            tex = sdl2.render.SDL_CreateTexture(
                sdl_renderer, pixel_format, access, shape[0], shape[1]
            )

            if tex is None:
                raise SDLError()

            return cls(
                position[0], position[1], shape[0], shape[1], depth,
                texture=tex.contents
            )
        else:
            surf = sdl2.surface.SDL_CreateRGBSurface(
                0, shape[0], shape[1], bpp, *masks
            )

            if surf is None:
                raise SDLError()

            return cls(
                position[0], position[1], shape[0], shape[1], depth,
                surface=surf.contents
            )

    def __del__(self):
        """
        Frees the resources bound to the sprite.

        :return:
        """
        if self._surface is not None:
            sdl2.surface.SDL_FreeSurface(self._surface)
            self._surface = None

        if self._texture is not None:
            sdl2.render.SDL_DestroyTexture(self._texture)
            self._texture = None


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
class TerminalDisplayBuffer(object):
    """
    Describe the state of the display buffer of the simulated display.
    """
    buffer = attr.ib(validator=instance_of(numpy.ndarray))

    @classmethod
    def create(cls, buffer_shape):
        """
        Create a TerminalDisplayBuffer

        :param buffer_shape:
        :return:
        """
        return cls(numpy.zeros(buffer_shape, dtype=str))
