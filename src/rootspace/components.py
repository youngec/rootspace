# -*- coding: utf-8 -*-

import enum
import xxhash
import sys

import attr
import numpy
import sdl2.pixels
import sdl2.render
import sdl2.stdinc
import sdl2.surface
import sdl2.surface
from attr.validators import instance_of

from .exceptions import SDLError, NotAnExecutableError


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
            tex = sdl2.render.SDL_CreateTexture(
                renderer, pixel_format, access, shape[0], shape[1]
            )

            if not tex:
                raise SDLError()

            if sdl2.render.SDL_SetRenderTarget(renderer, tex) != 0:
                raise SDLError()

            if sdl2.render.SDL_RenderClear(renderer) != 0:
                raise SDLError()

            if sdl2.render.SDL_SetRenderTarget(renderer, None) != 0:
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

    _platform = attr.ib(default="", validator=instance_of(str))
    _state = attr.ib(default=MSE.power_off, validator=instance_of(MSE))

    @property
    def fatal(self):
        return self._state == MachineState.MSE.fatal

    @fatal.setter
    def fatal(self, value):
        if value:
            self._state = MachineState.MSE.fatal

    @property
    def power_off(self):
        return self._state == MachineState.MSE.power_off

    @power_off.setter
    def power_off(self, value):
        if value:
            self._state = MachineState.MSE.power_off

    @property
    def power_up(self):
        return self._state == MachineState.MSE.power_up

    @power_up.setter
    def power_up(self, value):
        if value:
            self._state = MachineState.MSE.power_up

    @property
    def ready(self):
        return self._state == MachineState.MSE.ready

    @ready.setter
    def ready(self, value):
        if value:
            self._state = MachineState.MSE.ready

    @property
    def power_down(self):
        return self._state == MachineState.MSE.power_down

    @power_down.setter
    def power_down(self, value):
        if value:
            self._state = MachineState.MSE.power_down


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
        "root": {"uid": 0, "gid": 0, "perm": 0o755, "contents": {
            "bin": {"uid": 0, "gid": 0, "perm": 0o777, "contents": {}},
            "dev": {"uid": 0, "gid": 0, "perm": 0o755, "contents": {}},
            "etc": {"uid": 0, "gid": 0, "perm": 0o755, "contents": {
                "passwd": {"uid": 0, "gid": 0, "perm": 0o644, "id": 0x0001},
                "shadow": {"uid": 0, "gid": 0, "perm": 0o000, "id": 0x0002}
            }
            },
            "home": {"uid": 0, "gid": 0, "perm": 0o755, "contents": {}},
            "root": {"uid": 0, "gid": 0, "perm": 0o750, "contents": {}},
            "tmp": {"uid": 0, "gid": 0, "perm": 0o777, "contents": {}},
            "usr": {"uid": 0, "gid": 0, "perm": 0o755, "contents": {}}
              }
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

    _hierarchy = attr.ib(default=default_hierarchy, validator=instance_of(dict))
    _database = attr.ib(default=default_database, validator=instance_of(dict))
    flavour = attr.ib(default="unix", validator=instance_of(str))
    root = attr.ib(default="/", validator=instance_of(str))
    sep = attr.ib(default="/", validator=instance_of(str))

    def stat(self, uid, gid, path):
        """
        Return metadata to a particular file or directory.

        :param uid:
        :param gid:
        :param path:
        :return:
        """
        node = self._get_node(uid, gid, path)
        node_perm = node.get("perm", 0o000)
        node_uid = node.get("uid", 0)
        node_gid = node.get("gid", 0)
        node_type = "d" if "contents" in node else "-"
        stat_dict = {
            "path": path,
            "perm": "({:o} / {})".format(node_perm, self._explain_perm(node_type, node_perm)),
            "uid": "({} / {})".format(node_uid, self._explain_uid(node_uid)),
            "gid": "({} / {})".format(node_gid, self._explain_gid(node_gid))
        }
        return stat_dict

    def read(self, uid, gid, path):
        """
        Read data from a particular file.

        :param uid:
        :param gid:
        :param path:
        :return:
        """
        node = self._get_node(uid, gid, path)
        return self._read_data(uid, gid, node)

    def write(self, uid, gid, path, data):
        """
        Write data to a specified file.

        :param uid:
        :param gid:
        :param path:
        :param data:
        :return:
        """
        # FIXME: Create a node if it does not exist.
        node = self._get_node(uid, gid, path)
        self._write_data(uid, gid, node, data)

    def execute(self, uid, gid, path, context):
        """
        Execute a specified file within the given context.

        :param uid:
        :param gid:
        :param path:
        :param context:
        :return:
        """
        node = self._get_node(uid, gid, path)
        return self._execute_data(uid, gid, node, context)

    def _split_path(self, path):
        """
        Split a path string into a list of directories, starting at the tree root.

        :param path:
        :return:
        """
        path_parts = []
        if path.startswith(self.root):
            path_parts = ["root"] + list(filter(None, path.split(self.sep)))

        return path_parts

    def _has_read_perm(self, uid, gid, node):
        """
        Return True if the supplied user and group have read permission on the specified node.

        :param uid:
        :param gid:
        :param node:
        :return:
        """
        if uid == 0 and gid == 0:
            return True
        else:
            if uid == node["uid"]:
                return ((node["perm"] // 64) // 4) > 0
            elif gid == node["gid"]:
                return (((node["perm"] % 64) // 8) // 4) > 0
            else:
                return ((node["perm"] % 8) // 4) > 0

    def _has_write_perm(self, uid, gid, node):
        """
        Return True if the supplied user and group have write permission on the specified node.

        :param uid:
        :param gid:
        :param node:
        :return:
        """
        if uid == 0 and gid == 0:
            return True
        else:
            if uid == node["uid"]:
                return (((node["perm"] // 64) % 4) // 2) > 0
            elif gid == node["gid"]:
                return ((((node["perm"] % 64) // 8) % 4) // 2) > 0
            else:
                return (((node["perm"] % 8) % 4) // 2) > 0

    def _has_exec_perm(self, uid, gid, node):
        """
        Return True if the supplied user and group have execute permission on the specified node.

        :param uid:
        :param gid:
        :param node:
        :return:
        """
        if uid == node["uid"]:
            return ((node["perm"] // 64) % 2) > 0
        elif gid == node["gid"]:
            return (((node["perm"] % 64) // 8) % 2) > 0
        else:
            return ((node["perm"] % 8) % 2) > 0

    def _get_child(self, uid, gid, hierarchy, path_parts):
        """
        Recursively retrieve a child of the hierarchy.

        :param uid:
        :param gid:
        :param hierarchy:
        :param path_parts:
        :return:
        """
        if len(path_parts) > 1:
            node = hierarchy.get(path_parts[0], {})
            if self._has_read_perm(uid, gid, node):
                sub_hierarchy = node.get("contents", None)
                if sub_hierarchy is not None:
                    return self._get_child(uid, gid, sub_hierarchy, path_parts[1:])
                else:
                    raise FileNotFoundError()
            else:
                raise PermissionError()
        elif len(path_parts) == 1:
            node = hierarchy.get(path_parts[0], None)
            if node is not None:
                return node
            else:
                raise FileNotFoundError()
        else:
            return None

    def _get_node(self, uid, gid, path):
        """
        Get the hierarchy node at a specified path.

        :param uid:
        :param gid:
        :param path:
        :return:
        """
        path_parts = self._split_path(path)
        return self._get_child(uid, gid, self._hierarchy, path_parts)

    def _read_data(self, uid, gid, node):
        """
        Retrieve the data pertaining to a particular hierarchy node.

        :param uid:
        :param gid:
        :param node:
        :return:
        """
        if "id" in node:
            if self._has_read_perm(uid, gid, node):
                data = self._database.get(node["id"])
                if data is not None:
                    return data.copy()
                else:
                    raise FileNotFoundError()
            else:
                raise PermissionError()
        else:
            raise IsADirectoryError()

    def _write_data(self, uid, gid, node, data):
        """
        Write data of a particular node.

        :param uid:
        :param gid:
        :param node:
        :param data:
        :return:
        """
        if "id" in node:
            if self._has_write_perm(uid, gid, node):
                self._database[node["id"]] = data
            else:
                raise PermissionError()
        else:
            raise IsADirectoryError()

    def _execute_data(self, uid, gid, node, context):
        """
        Execute data of a particular node.

        :param uid:
        :param gid:
        :param node:
        :param context:
        :return:
        """
        if "id" in node:
            if self._has_exec_perm(uid, gid, node):
                data = self._database.get(node["id"])
                if data is not None:
                    if callable(data):
                        return data(context)
                    else:
                        raise NotAnExecutableError()
                else:
                    raise FileNotFoundError()
            else:
                raise PermissionError()
        else:
            raise IsADirectoryError()

    def _get_size(self, uid, gid, node):
        """
        Get the size of an object at specified path.

        :param uid:
        :param gid:
        :param node:
        :return:
        """
        data = self._read_data(uid, gid, node)

        if data is not None:
            return sys.getsizeof(data)
        else:
            return sys.getsizeof(node)

    def _explain_perm(self, node_type, perm):
        """
        Explain a particular permission number.

        :param perm:
        :return:
        """
        perm_str = ""
        if self.flavour == "unix":
            perm_digits = (perm // 64, (perm % 64) // 8, perm % 8)
            perm_list = (((p // 4) > 0, ((p % 4) // 2) > 0, (p % 2) > 0) for p in perm_digits)
            perm_groups = ("{}{}{}".format("r" if p[0] else "-", "w" if p[1] else "-", "x" if p[2] else "-") for p in perm_list)
            perm_str = node_type + "".join(perm_groups)

        return perm_str

    def _explain_uid(self, uid):
        """
        Explain a UID (user ID).

        :param uid:
        :return:
        """
        return "Unknown UID"

    def _explain_gid(self, gid):
        """
        Explain a GID (group ID).

        :param gid:
        :return:
        """
        return "Unknown GID"


@attr.s(slots=True)
class DisplayBuffer(object):
    """
    Describe the state of the display buffer of the simulated display.
    """
    _buffer = attr.ib(validator=instance_of(numpy.ndarray))
    _cursor_x = attr.ib(default=0, validator=instance_of(int))
    _cursor_y = attr.ib(default=0, validator=instance_of(int))
    _hasher = attr.ib(default=attr.Factory(xxhash.xxh64), validator=instance_of(xxhash.xxh64))
    _digest = attr.ib(default=b"", validator=instance_of(bytes))

    @property
    def buffer(self):
        return self._buffer

    @property
    def shape(self):
        return self._buffer.shape

    @property
    def cursor(self):
        return self._cursor_x, self._cursor_y

    @cursor.setter
    def cursor(self, value):
        self._cursor_x, self._cursor_y = value

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
    def create(cls, buffer_shape):
        """
        Create a TerminalDisplayBuffer

        :param buffer_shape:
        :return:
        """
        return cls(numpy.full(buffer_shape, b" ", dtype=bytes))

    def to_bytes(self):
        """
        Merge the entire buffer to a byte string.

        :return:
        """
        return b"\n".join(b"".join(self._buffer[i, :]) for i in range(self._buffer.shape[0]))

    def to_string(self, encoding="utf-8"):
        """
        Merge the entire buffer to a string.

        :return:
        """
        return self.to_bytes().decode(encoding)


@attr.s(slots=True)
class InputOutputStream(object):
    """
    Model input and output streams.
    """
    test_output = bytearray(
        "NUL: \0, BEL: \a, BSP: \b, TAB: \t, LF: \n, VT: \v, FF: \f, CR:, \r, SUB: \x1a, ESC: \x1b, DEL: \x7f",
        "utf-8"
    )

    input = attr.ib(default=attr.Factory(bytearray), validator=instance_of(bytearray))
    output = attr.ib(default=test_output, validator=instance_of(bytearray))


@attr.s(slots=True)
class ShellState(object):
    """
    Model the environment of a shell.
    """
    default_env = {
        "PWD": "",
        "SHELL": "",
        "PATH": ""
    }

    env = attr.ib(default=default_env, validator=instance_of(dict))
    line_buffer = attr.ib(default=attr.Factory(bytearray), validator=instance_of(bytearray))
    # stdin = attr.ib()
    # stdout = attr.ib()
