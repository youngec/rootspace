# -*- coding: utf-8 -*-

import enum
import string
import uuid

import attr
import numpy
import sdl2.pixels
import sdl2.render
import sdl2.stdinc
import sdl2.surface
import sdl2.surface
import xxhash
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
        if self._texture is not None:
            sdl2.render.SDL_DestroyTexture(self._texture)

        # FIXME: Utilise sdl2.render.SDL_QueryTexture()
        self._texture = value

    @classmethod
    def create(cls, position, shape, depth=0,
               renderer=None, pixel_format=sdl2.pixels.SDL_PIXELFORMAT_RGBA8888,
               access=sdl2.render.SDL_TEXTUREACCESS_STATIC, bpp=32, masks=(0, 0, 0, 0)):
        if renderer is not None:
            sdl_renderer = renderer.renderer
            tex = sdl2.render.SDL_CreateTexture(
                sdl_renderer, pixel_format, access, shape[0], shape[1]
            )

            if not tex:
                raise SDLError()

            return cls(
                position[0], position[1], shape[0], shape[1], depth,
                texture=tex.contents
            )
        else:
            surf = sdl2.surface.SDL_CreateRGBSurface(
                0, shape[0], shape[1], bpp, *masks
            )

            if not surf:
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
    # TODO: This design does not account for different operating systems.
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
class FileSystemState(object):
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
class DisplayBuffer(object):
    """
    Describe the state of the display buffer of the simulated display.
    """
    _buffer = attr.ib(validator=instance_of(numpy.ndarray))
    _ident = attr.ib(default=attr.Factory(uuid.uuid4), validator=instance_of(uuid.UUID))
    _hasher = attr.ib(default=attr.Factory(xxhash.xxh64), validator=instance_of(xxhash.xxh64))
    _digest = attr.ib(default=b"", validator=instance_of(bytes))

    @property
    def buffer(self):
        return self._buffer

    @property
    def ident(self):
        return self._ident

    @property
    def modified(self):
        """
        Determine if the buffer was modified since the last access to this property.
        :return:
        """
        self._hasher.reset()
        self._hasher.update(self._buffer)
        digest = self._hasher.digest()
        if digest != self._digest:
            self._digest = digest
            return True
        else:
            return False

    @property
    def empty(self):
        """
        Determine if the buffer is empty.

        :return:
        """
        return numpy.count_nonzero(self._buffer) == 0

    @classmethod
    def create(cls, buffer_shape, fill_buffer=True):
        """
        Create a TerminalDisplayBuffer

        :param buffer_shape:
        :param fill_buffer:
        :return:
        """
        if fill_buffer:
            buffer = numpy.random.choice(tuple(string.ascii_letters), size=buffer_shape)
        else:
            buffer = numpy.zeros(buffer_shape, dtype="<U1")

        return cls(buffer)

    def get_line(self, line_idx):
        """
        Merge the specified line to a string.

        :param line_idx:
        :return:
        """
        return "".join(self._buffer[line_idx, :].flatten())

    def to_bytes(self, encoding="utf-8"):
        """
        Merge the entire buffer to a byte string.

        :return:
        """
        return self.to_string().encode(encoding)

    def to_string(self):
        """
        Merge the entire buffer to a string.

        :return:
        """
        return "\n".join("".join(self._buffer[i, :]) for i in range(self._buffer.shape[0]))


@attr.s(slots=True)
class InputOutputStream(object):
    """
    Model input and output streams.
    """
    input = attr.ib(default=attr.Factory(bytearray), validator=instance_of(bytearray))
    output = attr.ib(default=attr.Factory(bytearray), validator=instance_of(bytearray))


@attr.s(slots=True)
class ShellEnvironment(object):
    """
    Model the environment of a shell.
    """
    default_environment = {
        "PWD": "",
        "SHELL": "",
        "PATH": ""
    }

    environment = attr.ib(default=default_environment, validator=instance_of(dict))
