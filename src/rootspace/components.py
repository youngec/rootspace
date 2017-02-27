# -*- coding: utf-8 -*-

import enum
import math

import xxhash
import contextlib
import warnings

import attr
import OpenGL.GL as gl
import PIL.Image
from attr.validators import instance_of
from OpenGL.constant import Constant

from .math import Quaternion, Matrix
from .wrappers import Texture, OpenGlProgram, OpenGlShader
from .utilities import camelcase_to_underscore
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
    mass = attr.ib(validator=instance_of(float))
    inertia = attr.ib(validator=instance_of(float))
    center_of_mass = attr.ib(validator=instance_of(Matrix))

    @classmethod
    def create(cls, mass=1.0, inertia=1.0, center_of_mass=(0, 0, 0)):
        """
        Create PhysicsProperties from mass, inertia and the center of mass.

        :param mass:
        :param inertia:
        :param center_of_mass:
        :return:
        """
        return cls(
            mass,
            inertia,
            Matrix((3, 1), center_of_mass)
        )


@attr.s
class PhysicsState(Component):
    momentum = attr.ib(validator=instance_of(Matrix))
    force = attr.ib(validator=instance_of(Matrix))

    @classmethod
    def create(cls, momentum=(0, 0, 0), force=(0, 0, 0)):
        """
        Create a PhysicsState component from momentum and force.

        :param momentum:
        :param force:
        :return:
        """
        return cls(
            Matrix((3, 1), momentum),
            Matrix((3, 1), force)
        )

    def __neg__(self):
        """
        Negate each element.

        :return:
        """
        return PhysicsState(-self.momentum, -self.force)

    def __add__(self, other):
        """
        Perform a left-sided addition operation.

        :param PhysicsState|int|float other:
        :rtype: PhysicsState
        :return:
        """
        if isinstance(other, PhysicsState):
            return PhysicsState(self.momentum + other.momentum, self.force + other.force)
        elif isinstance(other, (int, float)):
            return PhysicsState(self.momentum + other, self.force + other)
        else:
            return NotImplemented

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
        return self + -other

    def __rsub__(self, other):
        """
        Perform a right-sided subtraction operation.

        :param PhysicsState|int|float other:
        :rtype: PhysicsState
        :return:
        """
        return other + -self

    def __mul__(self, other):
        """
        Perform a left-sided element-wise multiplication operation.

        :param PhysicsState|int|float other:
        :rtype: PhysicsState
        :return:
        """
        if isinstance(other, PhysicsState):
            return PhysicsState(self.momentum * other.momentum, self.force * other.force)
        elif isinstance(other, (int, float)):
            return PhysicsState(self.momentum * other, self.force * other)
        else:
            return NotImplemented

    def __rmul__(self, other):
        """
        Perform a right-sided element-wise multiplication operation. Equivalent to __mul__.

        :param PhysicsState|int|float other:
        :rtype: PhysicsState
        :return:
        """
        return self.__mul__(other)

    def __truediv__(self, other):
        """
        Perform a left-sided element-wise division operation.

        :param PhysicsState|int|float other:
        :rtype: PhysicsState
        :return:
        """
        if isinstance(other, PhysicsState):
            return PhysicsState(self.momentum / other.momentum, self.force / other.force)
        elif isinstance(other, (int, float)):
            return PhysicsState(self.momentum / other, self.force / other)
        else:
            raise TypeError("unsupported operand type(s) for /: '{}' and '{}'".format(type(self), type(other)))

    def __rtruediv__(self, other):
        """
        Perform a right-sided element-wise division operation.

        :param PhysicsState|int|float other:
        :rtype: PhysicsState
        :return:
        """
        if isinstance(other, PhysicsState):
            return PhysicsState(other.momentum / self.momentum, other.force / self.force)
        elif isinstance(other, (int, float)):
            return PhysicsState(other / self.momentum, other / self.force)
        else:
            raise TypeError("unsupported operand type(s) for /: '{}' and '{}'".format(type(other), type(self)))


@attr.s
class Transform(Component):
    t = attr.ib(validator=instance_of(Matrix))
    r = attr.ib(validator=instance_of(Matrix))
    s = attr.ib(validator=instance_of(Matrix))

    @classmethod
    def create(cls, translation=(0, 0, 0), orientation=(0, 0, 0, 1), scale=(1, 1, 1)):
        """
        Create a Transform component from a translation vector, an orientation Quaternion and a scale vector.

        :param translation:
        :param orientation:
        :param scale:
        :return:
        """
        t = Matrix.translation(*translation)
        r = Quaternion(*orientation).matrix
        s = Matrix.scaling(*scale)

        return cls(t, r, s)

    @property
    def matrix(self):
        return self.t @ self.r @ self.s

    @property
    def position(self):
        return self.t[0:3, 3]

    @position.setter
    def position(self, value):
        self.t[0:3, 3] = value

@attr.s
class Projection(Component):
    p = attr.ib(validator=instance_of(Matrix))

    @classmethod
    def create(cls, field_of_view=math.pi/4, window_shape=(800, 600), near_plane=0-1, far_plane=1000):
        return cls(
            Matrix.perspective(field_of_view, window_shape[0] / window_shape[1], near_plane, far_plane)
        )

    @property
    def matrix(self):
        return self.p


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
    _buffer = attr.ib(validator=instance_of(Matrix))
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
        return not any(self._buffer)

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
