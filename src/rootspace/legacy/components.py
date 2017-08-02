# -*- coding: utf-8 -*-

import enum
import math
from typing import Optional
from contextlib import ExitStack

import xxhash
import warnings

import OpenGL.GL as gl
import PIL.Image
from OpenGL.constant import Constant

from .math import Quaternion, Matrix
from .wrappers import Texture, OpenGlProgram, OpenGlShader
from .utilities import camelcase_to_underscore
from .exceptions import FixmeWarning
from .data_abstractions import Mesh


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
    def __repr__(self):
        return "{}(...)".format(self.__class__.__name__)

    def __str__(self):
        return self.__class__.__name__


class BoundingVolume(Component):
    def __init__(self, minimum: Matrix, maximum: Matrix) -> None:
        self.minimum = minimum
        self.maximum = maximum

    @classmethod
    def create(cls, context, minimum=(-1, -1, -1), maximum=(1, 1, 1)):
        """
        Create a BoundingVolume component from the minimum and maximum points.

        :param context:
        :param minimum:
        :param maximum:
        :return:
        """
        return cls(
            Matrix((4, 1), minimum + (1,)),
            Matrix((4, 1), maximum + (1,))
        )


class PhysicsProperties(Component):
    def __init__(self, mass: float, inertia: float, center_of_mass: Matrix, g: Matrix) -> None:
        self.mass = mass
        self.inertia = inertia
        self.center_of_mass = center_of_mass
        self.g = g

    @classmethod
    def create(cls, context, mass=1.0, inertia=1.0, center_of_mass=(0, 0, 0), g=(0, -9.80665, 0)):
        """
        Create PhysicsProperties from mass, inertia and the center of mass.

        :param context:
        :param mass:
        :param inertia:
        :param center_of_mass:
        :return:
        """
        return cls(
            mass,
            inertia,
            Matrix((3, 1), center_of_mass),
            Matrix((3, 1), g)
        )


class PhysicsState(Component):
    def __init__(self, momentum: Matrix, force: Matrix) -> None:
        self.momentum = momentum
        self.force = force

    @classmethod
    def create(cls, context, momentum=(0, 0, 0), force=(0, 0, 0)):
        """
        Create a PhysicsState component from momentum and force.

        :param context:
        :param momentum:
        :param force:
        :return:
        """
        return cls(
            Matrix((3, 1), momentum),
            Matrix((3, 1), force)
        )

    def reset(self):
        self.momentum = Matrix((3, 1), 0)
        self.force = Matrix((3, 1), 0)


class Transform(Component):
    def __init__(self, t: Matrix, r: Matrix, s: Matrix, camera: bool) -> None:
        self.t = t
        self.r = r
        self.s = s
        self.camera = camera

    @classmethod
    def create(cls, context, position=(0, 0, 0), orientation=(0, 0, 0, 1), scale=(1, 1, 1), camera=False):
        """
        Create a Transform component from a translation vector, an orientation Quaternion and a scale vector.
        Setting camera to True inverts all translation operations.

        :param context:
        :param position:
        :param orientation:
        :param scale:
        :param camera:
        :return:
        """
        t = Matrix.translation(*position)
        q = Quaternion(*orientation)
        q /= q.norm()
        s = Matrix.scaling(*scale)

        return cls(t, q.matrix, s, camera)

    @property
    def right(self):
        return self.r[:3, :3].t @ Matrix.ex()

    @property
    def up(self):
        return self.r[:3, :3].t @ Matrix.ey()

    @property
    def forward(self):
        return self.r[:3, :3].t @ -Matrix.ez()

    @property
    def position(self):
        if self.camera:
            return -self.t[0:3, 3]
        else:
            return self.t[0:3, 3]

    @position.setter
    def position(self, value):
        if self.camera:
            self.t[0:3, 3] = -value
        else:
            self.t[0:3, 3] = value

    def reset(self):
        self.t = Matrix.identity(4)
        self.r = Matrix.identity(4)
        self.s = Matrix.identity(4)


class Projection(Component):
    def __init__(self, p: Matrix) -> None:
        self.p = p

    @classmethod
    def create(cls, context, field_of_view=math.pi / 4, window_shape=(800, 600), near_plane=0 - 1, far_plane=1000):
        """
        Create a projection component.

        :param context:
        :param field_of_view:
        :param window_shape:
        :param near_plane:
        :param far_plane:
        :return:
        """
        return cls(
            Matrix.perspective(field_of_view, window_shape[0] / window_shape[1], near_plane, far_plane)
        )

    @property
    def matrix(self):
        return self.p


class Model(Component):
    """
    OpenGlModel encapsulates all that belongs to a graphical representation of an object, stored on the GPU.
    """
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

    def __init__(self, vao: int, vbo: int, ibo: int, draw_mode: Constant,
                 index_len: int,
                 index_type: Constant, texture: Optional[Texture],
                 program: OpenGlProgram, ctx_exit: ExitStack,
                 render_exit: Optional[ExitStack] = None) -> None:
        self._vao = vao
        self._vbo = vbo
        self._ibo = ibo
        self._draw_mode = draw_mode
        self._index_len = index_len
        self._index_type = index_type
        self._texture = texture
        self._program = program
        self._ctx_exit = ctx_exit
        self._render_exit = render_exit

    def __del__(self):
        self._ctx_exit.close()

    def __enter__(self):
        """
        Enable the model.

        :return:
        """
        with ExitStack() as ctx_mgr:
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
        if self._render_exit is not None:
            self._render_exit.close()
            self._render_exit = None

        return False


    @classmethod
    def delete_vertex_arrays(cls, num, obj):
        if bool(gl.glDeleteVertexArrays) and obj >= 0:
            gl.glDeleteVertexArrays(num, obj)

    @classmethod
    def delete_buffers(cls, num, obj):
        if bool(gl.glDeleteBuffers) and obj >= 0:
            gl.glDeleteBuffers(num, obj)

    @classmethod
    def create(cls, context, mesh_path, vertex_shader_path=None, fragment_shader_path=None, texture_path=None):
        # Load the mesh into memory.
        mesh = context.model_parser.load(mesh_path)

        if mesh.vertex_shader is None and vertex_shader_path is None:
            raise ValueError("Either the Mesh or the Scene must define a vertex shader. The latter takes precedence.")
        elif vertex_shader_path is not None:
            mesh.vertex_shader = vertex_shader_path.read_text()

        if mesh.fragment_shader is None and fragment_shader_path is None:
            raise ValueError("Either the Mesh or the Scene must define a fragment shader. The latter takes precedence.")
        elif fragment_shader_path is not None:
            mesh.fragment_shader = fragment_shader_path.read_text()

        if mesh.requires_texture and mesh.texture is None and texture_path is None:
            raise ValueError("The Mesh requires a texture, thus either the Mesh or the Scene must provide one. The latter takes precedence.")
        elif mesh.requires_texture and texture_path is not None:
            mesh.texture = PIL.Image.open(texture_path)
        elif not mesh.requires_texture and (mesh.texture is not None or texture_path is not None):
            warnings.warn("Texture data was provided but the Mesh does not require one.", FixmeWarning)

        with ExitStack() as ctx:
            # Create and bind the Vertex Array Object
            vao = int(gl.glGenVertexArrays(1))
            ctx.callback(cls.delete_vertex_arrays, 1, vao)
            gl.glBindVertexArray(vao)

            # Compile the shader program
            vertex_shader = OpenGlShader.create(gl.GL_VERTEX_SHADER, mesh.vertex_shader)
            fragment_shader = OpenGlShader.create(gl.GL_FRAGMENT_SHADER, mesh.fragment_shader)
            program = OpenGlProgram.create(vertex_shader, fragment_shader)

            # Create the texture only if necessary
            tex = None
            if mesh.requires_texture:
                tex = Texture.create(mesh.texture)

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

    def draw(self, matrix: Matrix) -> None:
        """
        Draw the current model.

        :param matrix:
        :return:
        """
        if self._render_exit is not None:
            warnings.warn("I should probably not hard-code the uniform variable names.", FixmeWarning)
            self._program.uniform("mvp_matrix", matrix)
            if self._texture is not None:
                gl.glActiveTexture(gl.GL_TEXTURE0)
                self._program.uniform("active_tex", 0)

            gl.glDrawElements(self._draw_mode, self._index_len, self._index_type, None)
        else:
            raise RuntimeError("Cannot render outside of Model context manager.")


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

    def __init__(self, platform: str, state: MSE) -> None:
        self._platform = platform
        self._state = state

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


class NetworkState(Component):
    """
    Describe the state of the network subsystem.
    """
    def __init__(self, address: int, connected: list) -> None:
        self.address = address
        self.connected = connected


class DisplayBuffer(Component):
    """
    Describe the state of the display buffer of the simulated display.
    """
    def __init__(self, buffer: Matrix, cursor_x: int, cursor_y: int, hasher: xxhash.xxh64, digest: bytes) -> None:
        self._buffer = buffer
        self._cursor_x = cursor_x
        self._cursor_y = cursor_y
        self._hasher = hasher
        self._digest = digest

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


class InputOutputStream(Component):
    """
    Model input and output streams.
    """
    test_output = bytearray(
        "NUL: \0, BEL: \a, BSP: \b, TAB: \t, LF: \n, VT: \v, FF: \f, CR:, \r, SUB: \x1a, ESC: \x1b, DEL: \x7f",
        "utf-8"
    )

    def __init__(self, in_stream: bytearray, out_stream: bytearray) -> None:
        self.input = in_stream
        self.output = out_stream


class ShellState(Component):
    """
    Model the environment of a shell.
    """
    default_env = {
        "PWD": "",
        "SHELL": "",
        "PATH": ""
    }

    def __init__(self, env: dict, line_buffer: bytearray, path_sep: str) -> None:
        self.env = env
        self.line_buffer = line_buffer
        self.path_sep = path_sep

    @property
    def uid(self):
        return -1

    @property
    def gids(self):
        return (-1,)

    @property
    def path(self):
        return list(filter(None, self.env.split(self.path_sep)))
