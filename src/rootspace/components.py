# -*- coding: utf-8 -*-

import enum
import math
import xxhash

import attr
import numpy
from attr.validators import instance_of

from .opengl_math import perspective, translation, Quaternion, to_quaternion


@attr.s(slots=True)
class Transform(object):
    _pos = attr.ib(default=numpy.zeros(3), validator=instance_of(numpy.ndarray), convert=numpy.array)
    _scale = attr.ib(default=numpy.ones(3), validator=instance_of(numpy.ndarray), convert=numpy.array)
    _quat = attr.ib(default=Quaternion(1, 0, 0, 0), validator=instance_of(Quaternion), convert=to_quaternion)

    @property
    def position(self):
        return self._pos

    @position.setter
    def position(self, value):
        if isinstance(value, numpy.ndarray) and value.shape == (3,):
            self._pos = value
        else:
            raise TypeError("Position must be a 3-component numpy array.")

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, value):
        if isinstance(value, numpy.ndarray) and value.shape == (3,):
            self._scale = value
        elif isinstance(value, (int, float)):
            self._scale = value * numpy.ones(3)
        else:
            raise TypeError("Scale must be a 3-component numpy array or a scalar.")

    @property
    def orientation(self):
        return self._quat

    @orientation.setter
    def orientation(self, value):
        if isinstance(value, Quaternion):
            self._quat = value
        else:
            raise TypeError("Orientation must be a Quaternion.")

    @property
    def up(self):
        return self._quat.T.matrix4 @ (0, 1, 0, 1)

    @property
    def right(self):
        return self._quat.T.matrix4 @ (1, 0, 0, 1)

    @property
    def forward(self):
        return self._quat.T.matrix4 @ (0, 0, 1, 1)

    @property
    def matrix(self):
        scale_matrix = numpy.eye(4)
        scale_matrix[:3, :3] *= self._scale
        return translation(self._pos) @ scale_matrix @ self._quat.matrix4

    def look_at(self, target):
        forward = target - self._pos
        forward /= numpy.linalg.norm(forward)

        forward_dot = self.forward[:3] @ forward
        if math.isclose(forward_dot, -1):
            self._quat = Quaternion(0, 0, 1, 0)
        elif math.isclose(forward_dot, 1):
            self._quat = Quaternion(1, 0, 0, 0)
        else:
            axis = numpy.cross(self.forward[:3], forward)
            angle = math.acos(forward_dot)
            self.rotate(axis, angle, chain=False)

    def rotate(self, axis, angle, chain=True):
        """
        Rotate the component around the given axis by the specified angle.

        :param axis:
        :param angle:
        :param chain:
        :return:
        """
        quat = Quaternion.from_axis(axis, angle)

        if chain:
            self._quat = quat @ self._quat
        else:
            self._quat = quat


@attr.s(slots=True)
class CameraData(object):
    _fov = attr.ib(default=numpy.pi / 4, validator=instance_of(float))
    _aspect = attr.ib(default=1.0, validator=instance_of(float))
    _near = attr.ib(default=0.1, validator=instance_of(float))
    _far = attr.ib(default=10.0, validator=instance_of(float))

    @property
    def matrix(self):
        return perspective(self._fov, self._aspect, self._near, self._far)

    @property
    def aspect(self):
        return self._aspect

    @aspect.setter
    def aspect(self, value):
        self._aspect = value


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
    path_sep = attr.ib(default=":", validator=instance_of(str))

    # stdin = attr.ib()
    # stdout = attr.ib()

    @property
    def uid(self):
        return -1

    @property
    def gids(self):
        return (-1,)

    @property
    def path(self):
        return list(filter(None, self.env.split(self.path_sep)))
