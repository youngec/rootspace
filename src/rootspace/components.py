# -*- coding: utf-8 -*-

import enum
import math
import xxhash
import contextlib
import warnings

import attr
import numpy
import OpenGL.GL as gl
import PIL.Image
from attr.validators import instance_of
from attr import Factory
from OpenGL.constant import Constant

from .opengl_math import perspective, translation, Quaternion, to_quaternion
from .wrappers import Texture, OpenGlProgram, OpenGlShader
from .utilities import camelcase_to_underscore, iterable_of
from .exceptions import TodoWarning, FixmeWarning
from .data_abstractions import Attribute, Mesh
from .model_parser import PlyParser


class ComponentMeta(type):
    """
    ComponentMeta registers all Components in ComponentMeta.classes
    """
    classes = dict()

    def __new__(meta, name, bases, cls_dict):
        register = cls_dict.pop("register", True)
        cls = super(ComponentMeta, meta).__new__(meta, name, bases, cls_dict)
        if register:
            ComponentMeta.classes[camelcase_to_underscore(cls.__name__)] = cls

        return cls


class Component(object, metaclass=ComponentMeta):
    pass


@attr.s
class PhysicsProperties(Component):
    mass = attr.ib(default=1, validator=instance_of(float), convert=float)
    inertia = attr.ib(default=1, validator=instance_of(float), convert=float)
    center_of_mass = attr.ib(default=numpy.zeros(3), validator=instance_of(numpy.ndarray), convert=numpy.array)


@attr.s
class PhysicsState(Component):
    momentum = attr.ib(default=numpy.zeros(3), validator=instance_of(numpy.ndarray), convert=numpy.array)
    spin = attr.ib(default=Factory(Quaternion), validator=instance_of(Quaternion), convert=to_quaternion)
    force = attr.ib(default=numpy.zeros(3), validator=instance_of(numpy.ndarray), convert=numpy.array)

    def __add__(self, other):
        """
        Perform a left-sided addition operation.

        :param PhysicsState|int|float other:
        :rtype: PhysicsState
        :return:
        """
        if isinstance(other, PhysicsState):
            return PhysicsState(self.momentum + other.momentum, self.spin + other.spin, self.force + other.force)
        elif isinstance(other, (int, float)):
            return PhysicsState(self.momentum + other, self.spin + other, self.force + other)
        else:
            raise TypeError("unsupported operand type(s) for +: '{}' and '{}'".format(type(self), type(other)))

    def __radd__(self, other):
        """
        Perform a right-sided addition operation. Equivalent to __add__.

        :param PhysicsState|int|float other:
        :rtype: PhysicsState
        :return:
        """
        return self.__add__(other)

    def __sub__(self, other):
        """
        Perform a left-sided subtraction operation.

        :param PhysicsState|int|float other:
        :rtype: PhysicsState
        :return:
        """
        if isinstance(other, PhysicsState):
            return PhysicsState(self.momentum - other.momentum, self.spin - other.spin, self.force - other.force)
        elif isinstance(other, (int, float)):
            return PhysicsState(self.momentum - other, self.spin - other, self.force - other)
        else:
            raise TypeError("unsupported operand type(s) for -: '{}' and '{}'".format(type(self), type(other)))

    def __rsub__(self, other):
        """
        Perform a right-sided subtraction operation.

        :param PhysicsState|int|float other:
        :rtype: PhysicsState
        :return:
        """
        if isinstance(other, PhysicsState):
            return PhysicsState(other.momentum - self.momentum, other.spin - self.spin, other.force - self.force)
        elif isinstance(other, (int, float)):
            return PhysicsState(other - self.momentum, other - self.spin, other - self.force)
        else:
            raise TypeError("unsupported operand type(s) for -: '{}' and '{}'".format(type(other), type(self)))

    def __mul__(self, other):
        """
        Perform a left-sided multiplication operation.

        :param PhysicsState|int|float other:
        :rtype: PhysicsState
        :return:
        """
        if isinstance(other, PhysicsState):
            return PhysicsState(self.momentum * other.momentum, self.spin * other.spin, self.force * other.force)
        elif isinstance(other, (int, float)):
            return PhysicsState(self.momentum * other, self.spin * other, self.force * other)
        else:
            raise TypeError("unsupported operand type(s) for *: '{}' and '{}'".format(type(self), type(other)))

    def __rmul__(self, other):
        """
        Perform a right-sided multiplication operation. Equivalent to __mul__.

        :param PhysicsState|int|float other:
        :rtype: PhysicsState
        :return:
        """
        return self.__mul__(other)


@attr.s
class Transform(Component):
    _pos = attr.ib(default=numpy.zeros(3), validator=instance_of(numpy.ndarray), convert=numpy.array)
    _scale = attr.ib(default=numpy.ones(3), validator=instance_of(numpy.ndarray), convert=numpy.array)
    _quat = attr.ib(default=Factory(Quaternion), validator=instance_of(Quaternion), convert=to_quaternion)

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
    def zero(self):
        return numpy.zeros(3)

    @property
    def up(self):
        return (self._quat.T.matrix4 @ (0, 1, 0, 1))[:3]

    @property
    def right(self):
        return (self._quat.T.matrix4 @ (1, 0, 0, 1))[:3]

    @property
    def forward(self):
        return (self._quat.T.matrix4 @ (0, 0, 1, 1))[:3]

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


@attr.s
class Projection(Component):
    _fov = attr.ib(default=math.pi / 4, validator=instance_of(float))
    _shape = attr.ib(default=(800, 600), validator=iterable_of(tuple, int), convert=tuple)
    _near = attr.ib(default=0.1, validator=instance_of(float))
    _far = attr.ib(default=1000.0, validator=instance_of(float))

    @property
    def matrix(self):
        return perspective(self._fov, self._shape[0] / self._shape[1], self._near, self._far)

    @property
    def shape(self):
        return self._shape

    @shape.setter
    def shape(self, value):
        self._shape = value


@attr.s
class Model(Component):
    """
    OpenGlModel encapsulates all that belongs to a graphical representation of an object, stored on the GPU.
    """
    _vao = attr.ib(validator=instance_of(int))
    _vbo = attr.ib(validator=instance_of(int))
    _ibo = attr.ib(validator=instance_of(int))
    _draw_mode = attr.ib(validator=instance_of(Constant))
    _index_len = attr.ib(validator=instance_of(int))
    _index_type = attr.ib(validator=instance_of(Constant))
    _texture = attr.ib(validator=instance_of((type(None), Texture)))
    _program = attr.ib(validator=instance_of(OpenGlProgram))
    _ctx_exit = attr.ib(validator=instance_of(contextlib.ExitStack), repr=False)
    _render_exit = attr.ib(default=None, validator=instance_of((type(None), contextlib.ExitStack)), repr=False)

    data_types = {
        "b": gl.GL_BYTE,
        "B": gl.GL_UNSIGNED_BYTE,
        "h": gl.GL_SHORT,
        "H": gl.GL_UNSIGNED_SHORT,
        "i": gl.GL_INT,
        "I": gl.GL_UNSIGNED_INT,
        "f": gl.GL_FLOAT,
        "d": gl.GL_DOUBLE
    }

    draw_modes = {
        Mesh.DrawMode.Points: gl.GL_POINTS,
        Mesh.DrawMode.LineStrip: gl.GL_LINE_STRIP,
        Mesh.DrawMode.LineLoop: gl.GL_LINE_LOOP,
        Mesh.DrawMode.Lines: gl.GL_LINES,
        Mesh.DrawMode.LineStripAdjacency: gl.GL_LINE_STRIP_ADJACENCY,
        Mesh.DrawMode.LinesAdjacency: gl.GL_LINES_ADJACENCY,
        Mesh.DrawMode.TriangleStrip: gl.GL_TRIANGLE_STRIP,
        Mesh.DrawMode.TriangleFan: gl.GL_TRIANGLE_FAN,
        Mesh.DrawMode.Triangles: gl.GL_TRIANGLES,
        Mesh.DrawMode.TriangleStripAdjacency: gl.GL_TRIANGLE_STRIP_ADJACENCY,
        Mesh.DrawMode.TrianglesAdjacency: gl.GL_TRIANGLES_ADJACENCY,
        Mesh.DrawMode.Patches: gl.GL_PATCHES
    }

    @classmethod
    def delete_vertex_arrays(cls, num, obj):
        if bool(gl.glDeleteVertexArrays) and obj >= 0:
            gl.glDeleteVertexArrays(num, obj)

    @classmethod
    def delete_buffers(cls, num, obj):
        if bool(gl.glDeleteBuffers) and obj >= 0:
            gl.glDeleteBuffers(num, obj)

    @classmethod
    def create(cls, mesh_path, vertex_shader_path, fragment_shader_path, texture_path=None):
        with contextlib.ExitStack() as ctx:
            # Load the mesh into memory.
            mesh = PlyParser.create().load(mesh_path)

            warnings.warn("Possibly rewrite the GL calls in Direct State Access style.", TodoWarning)
            # Create and bind the Vertex Array Object
            vao = int(gl.glGenVertexArrays(1))
            ctx.callback(cls.delete_vertex_arrays, 1, vao)
            gl.glBindVertexArray(vao)

            # Compile the shader program
            vertex_shader = OpenGlShader.create(gl.GL_VERTEX_SHADER, vertex_shader_path.read_text())
            fragment_shader = OpenGlShader.create(gl.GL_FRAGMENT_SHADER, fragment_shader_path.read_text())
            program = OpenGlProgram.create(vertex_shader, fragment_shader)

            # Create the texture only if necessary
            tex = None
            if any(a.type == Attribute.Type.Texture for a in mesh.attributes):
                if texture_path is not None:
                    with PIL.Image.open(texture_path) as tx_data:
                        tex = Texture.create(tx_data)
            elif texture_path is not None:
                warnings.warn("Texture data was provided but the model data does not use any.", FixmeWarning)

            # Initialise the vertex buffer
            vbo = int(gl.glGenBuffers(1))
            ctx.callback(cls.delete_buffers, 1, vbo)
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
            gl.glBufferData(gl.GL_ARRAY_BUFFER, len(mesh.data_bytes), mesh.data_bytes, gl.GL_STATIC_DRAW)

            # Initialise the index buffer
            ibo = int(gl.glGenBuffers(1))
            ctx.callback(cls.delete_buffers, 1, ibo)
            gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, ibo)
            gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, len(mesh.index_bytes), mesh.index_bytes, gl.GL_STATIC_DRAW)

            # Set the attribute pointers
            for a in mesh.attributes:
                gl.glEnableVertexAttribArray(a.location)
                gl.glVertexAttribPointer(
                    a.location, a.components, cls.data_types[mesh.data_type], False, a.stride_bytes, a.start_ptr
                )

            gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, 0)
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
            gl.glBindVertexArray(0)

            ctx_exit = ctx.pop_all()

            return cls(
                vao, vbo, ibo, cls.draw_modes[mesh.draw_mode], len(mesh.index), cls.data_types[mesh.index_type],
                tex, program, ctx_exit
            )

    def draw(self, matrix):
        """
        Draw the current model.

        :param matrix:
        :return:
        """
        warnings.warn("I should probably not hard-code the uniform variable names.", FixmeWarning)
        self._program.uniform("mvp_matrix", matrix)
        if self._texture is not None:
            gl.glActiveTexture(gl.GL_TEXTURE0)
            self._program.uniform("active_tex", 0)

        gl.glDrawElements(self._draw_mode, self._index_len, self._index_type, None)

    def __del__(self):
        self._ctx_exit.close()

    def __enter__(self):
        """
        Enable the model.

        :return:
        """
        with contextlib.ExitStack() as ctx_mgr:
            ctx_mgr.enter_context(self._program)

            if self._texture is not None:
                ctx_mgr.enter_context(self._texture)

            gl.glBindVertexArray(self._vao)
            ctx_mgr.callback(gl.glBindVertexArray, 0)

            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._vbo)
            ctx_mgr.callback(gl.glBindBuffer, gl.GL_ARRAY_BUFFER, 0)

            gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self._ibo)
            ctx_mgr.callback(gl.glBindBuffer, gl.GL_ELEMENT_ARRAY_BUFFER, 0)

            self._render_exit = ctx_mgr.pop_all()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Disable the model.

        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return:
        """
        self._render_exit.close()
        return False


@attr.s
class MachineState(Component):
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


@attr.s
class NetworkState(Component):
    """
    Describe the state of the network subsystem.
    """
    address = attr.ib(default=0, validator=instance_of(int))
    connected = attr.ib(default=attr.Factory(list), validator=instance_of(list))


@attr.s
class DisplayBuffer(Component):
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


@attr.s
class InputOutputStream(Component):
    """
    Model input and output streams.
    """
    test_output = bytearray(
        "NUL: \0, BEL: \a, BSP: \b, TAB: \t, LF: \n, VT: \v, FF: \f, CR:, \r, SUB: \x1a, ESC: \x1b, DEL: \x7f",
        "utf-8"
    )

    input = attr.ib(default=attr.Factory(bytearray), validator=instance_of(bytearray))
    output = attr.ib(default=test_output, validator=instance_of(bytearray))


@attr.s
class ShellState(Component):
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
