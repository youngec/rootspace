# -*- coding: utf-8 -*-

"""Provides wrappers for OpenGL concepts."""

import contextlib
import ctypes
import logging
import warnings
import array

import PIL.Image
import OpenGL.GL as gl
from OpenGL.constant import Constant
import attr
import numpy
from attr.validators import instance_of

from .exceptions import OpenGLError, TodoWarning, FixmeWarning


@attr.s
class Attribute(object):
    components = attr.ib(validator=instance_of(int))
    stride = attr.ib(validator=instance_of(int))
    start_idx = attr.ib(validator=instance_of(int))
    location = attr.ib(validator=instance_of(int))

    @property
    def stride_bytes(self):
        return self.stride * ctypes.sizeof(ctypes.c_float)

    @property
    def start_ptr(self):
        return ctypes.c_void_p(self.start_idx * ctypes.sizeof(ctypes.c_float))


@attr.s
class VertexAttribute(Attribute):
    pass


@attr.s
class TextureAttribute(Attribute):
    pass


@attr.s
class ColorAttribute(Attribute):
    pass


@attr.s
class Mesh(object):
    data = attr.ib(validator=instance_of(array.array))
    index = attr.ib(validator=instance_of(array.array))
    attributes = attr.ib(validator=instance_of(tuple))
    draw_mode = attr.ib(validator=instance_of(Constant))

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

    @property
    def data_bytes(self):
        return self.data.tobytes()

    @property
    def data_type(self):
        return self.data_types[self.data.typecode]

    @property
    def index_bytes(self):
        return self.index.tobytes()

    @property
    def index_type(self):
        return self.data_types[self.index.typecode]

    @classmethod
    def create_cube(cls):
        return cls(
            data=array.array("f", (
                -1, -1, -1, 0, 0, 0,
                1, -1, -1, 1, 0, 0,
                -1, 1, -1, 0, 1, 0,
                1, 1, -1, 1, 1, 0,
                -1, -1, 1, 0, 0, 1,
                1, -1, 1, 1, 0, 1,
                -1, 1, 1, 0, 1, 1,
                1, 1, 1, 1, 1, 1
            )),
            index=array.array("B", (
                0, 2, 1,
                1, 2, 3,
                4, 5, 6,
                5, 7, 6,
                0, 6, 2,
                0, 4, 6,
                1, 3, 7,
                1, 7, 5,
                2, 6, 3,
                3, 6, 7,
                0, 1, 4,
                1, 5, 4
            )),
            attributes=(
                VertexAttribute(3, 6, 0, 0),
                ColorAttribute(3, 6, 3, 2)
            ),
            draw_mode=gl.GL_TRIANGLES
        )


@attr.s
class Shader(object):
    """
    Shader is an on-CPU representation of a shader program.
    """
    vertex_source = attr.ib(validator=instance_of(str))
    fragment_source = attr.ib(validator=instance_of(str))

    @classmethod
    def create(cls, vertex_shader_path, fragment_shader_path):
        """
        Create an on-CPU representation of a shader.

        :param vertex_shader_path:
        :param fragment_shader_path:
        :return:
        """
        vertex_source = vertex_shader_path.read_text()
        fragment_source = fragment_shader_path.read_text()
        return cls(vertex_source, fragment_source)


@attr.s
class Texture(object):
    """
    OpenGlTexture encapsulates an OpenGL texture.
    """
    _obj = attr.ib(validator=instance_of(int))
    _shape = attr.ib(validator=instance_of(tuple))
    _ctx_exit = attr.ib(validator=instance_of(contextlib.ExitStack), repr=False)

    texture_formats = {
        "L": gl.GL_RED,
        "LA": gl.GL_RG,
        "RGB": gl.GL_RGB,
        "RGBA": gl.GL_RGBA
    }

    texture_data_types = {
        "L": gl.GL_UNSIGNED_BYTE,
        "RGB": gl.GL_UNSIGNED_BYTE,
        "RGBA": gl.GL_UNSIGNED_BYTE,
        "I": gl.GL_INT,
        "F": gl.GL_FLOAT
    }

    @classmethod
    def _delete_textures(cls, obj):
        if bool(gl.glDeleteTextures) and obj > 0:
            warnings.warn("glDeleteTextures throws an 'invalid operation (1282)' sometimes.", FixmeWarning)
            gl.glDeleteTextures(obj)

    @classmethod
    def texture_format(cls, data):
        return cls.texture_formats[data.mode]

    @classmethod
    def texture_dtype(cls, data):
        return cls.texture_data_types[data.mode]

    @classmethod
    def create(cls, data, min_filter=gl.GL_LINEAR, mag_filter=gl.GL_LINEAR, wrap_mode=gl.GL_CLAMP_TO_EDGE):
        with contextlib.ExitStack() as ctx_mgr:
            image_format = cls.texture_format(data)
            image_dtype = cls.texture_dtype(data)
            shape = data.size

            # Create the texture object
            obj = gl.glGenTextures(1)
            if obj == 0:
                raise OpenGLError("Failed to create a texture object.")
            ctx_mgr.callback(cls._delete_textures, obj)

            # Set texture parameters
            gl.glBindTexture(gl.GL_TEXTURE_2D, obj)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, min_filter)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, mag_filter)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, wrap_mode)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, wrap_mode)

            # Set the texture data
            gl.glTexImage2D(
                gl.GL_TEXTURE_2D, 0, image_format, shape[0], shape[1], 0, image_format, image_dtype,
                data.transpose(PIL.Image.FLIP_LEFT_RIGHT).transpose(PIL.Image.FLIP_TOP_BOTTOM).tobytes()
            )
            gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

            ctx_exit = ctx_mgr.pop_all()

            return cls(obj, shape, ctx_exit)

    def __del__(self):
        self._ctx_exit.close()

    @property
    def obj(self):
        return self._obj

    @property
    def shape(self):
        return self._shape

    @property
    def enabled(self):
        return gl.glGetIntegerv(gl.GL_TEXTURE_BINDING_2D) == self._obj

    def __enter__(self):
        """
        Enable the texture.

        :return:
        """
        if not self.enabled:
            gl.glBindTexture(gl.GL_TEXTURE_2D, self._obj)
        else:
            self._log.warning("Attempting to enable an active texture.")

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Disable the texture.

        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return:
        """
        if self.enabled:
            gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
        else:
            self._log.warning("Attempting to disable an inactive texture.")

        return False


@attr.s
class OpenGlShader(object):
    """OpenGlShader encapsulates an OpenGL shader."""

    _obj = attr.ib(validator=instance_of(int))
    _ctx_exit = attr.ib(validator=instance_of(contextlib.ExitStack), repr=False)

    @classmethod
    def _delete_shader(cls, obj):
        if bool(gl.glDeleteShader) and obj > 0:
            gl.glDeleteShader(obj)

    @classmethod
    def create(cls, shader_type, shader_source):
        with contextlib.ExitStack() as ctx_mgr:
            # Create the shader object
            obj = int(gl.glCreateShader(shader_type))
            if obj == 0:
                raise OpenGLError("Failed to create a shader object.")
            ctx_mgr.callback(cls._delete_shader, obj)

            # Set the shader source code
            gl.glShaderSource(obj, shader_source)

            # Compile the shader
            gl.glCompileShader(obj)

            # Determine the compile status of the shader
            if not gl.glGetShaderiv(obj, gl.GL_COMPILE_STATUS):
                log_string = gl.glGetShaderInfoLog(obj)
                raise OpenGLError(log_string.decode("utf-8"))

            ctx_exit = ctx_mgr.pop_all()

            return cls(obj, ctx_exit)

    def __del__(self):
        self._ctx_exit.close()

    @property
    def obj(self):
        return self._obj


@attr.s
class OpenGlProgram(object):
    """
    OpenGlProgram encapsulates an OpenGL shader program.
    """
    _obj = attr.ib(validator=instance_of(int))
    _log = attr.ib(validator=instance_of(logging.Logger), repr=False)
    _ctx_exit = attr.ib(validator=instance_of(contextlib.ExitStack), repr=False)

    @classmethod
    def _delete_program(cls, obj):
        if bool(gl.glDeleteProgram) and obj > 0:
            gl.glDeleteProgram(obj)

    @classmethod
    def create(cls, shaders):
        with contextlib.ExitStack() as ctx_mgr:
            # Create the shader program
            obj = int(gl.glCreateProgram())
            if obj == 0:
                raise OpenGLError("Failed to create a shader program.")
            ctx_mgr.callback(cls._delete_program, obj)

            # Attach the shaders
            for shader in shaders:
                gl.glAttachShader(obj, shader.obj)

            # Link the shader program
            gl.glLinkProgram(obj)

            # Detach the shaders
            for shader in shaders:
                gl.glDetachShader(obj, shader.obj)

            # Determine the link status
            if not gl.glGetProgramiv(obj, gl.GL_LINK_STATUS):
                log_string = gl.glGetProgramInfoLog(obj)
                raise OpenGLError(log_string.decode("utf-8"))

            log = logging.getLogger("{}.{}".format(__name__, cls.__name__))

            ctx_exit = ctx_mgr.pop_all()

            return cls(obj, log, ctx_exit)

    def __del__(self):
        self._ctx_exit.close()

    @property
    def obj(self):
        return self._obj

    @property
    def enabled(self):
        return gl.glGetIntegerv(gl.GL_CURRENT_PROGRAM) == self._obj

    def uniform_location(self, name):
        loc = gl.glGetUniformLocation(self._obj, name)
        if loc == -1:
            raise OpenGLError("Could not find the shader uniform '{}'.".format(name))
        else:
            return loc

    def attribute_location(self, name):
        loc = gl.glGetAttribLocation(self._obj, name)
        if loc == -1:
            raise OpenGLError("Could not find the shader attribute '{}'.".format(name))
        else:
            return loc

    def uniform(self, name, value):
        loc = self.uniform_location(name)
        if isinstance(value, numpy.ndarray):
            if value.shape == (4, 4):
                gl.glUniformMatrix4fv(loc, 1, True, value)
            else:
                raise NotImplementedError("Cannot set any other matrix shapes yet.")
        elif isinstance(value, int):
            gl.glUniform1i(loc, value)
        elif isinstance(value, float):
            gl.glUniform1f(loc, value)
        else:
            raise NotImplementedError("Cannot set any other data types yet.")

    def __enter__(self):
        """
        Enable the program.

        :return:
        """
        if not self.enabled:
            gl.glUseProgram(self._obj)
        else:
            self._log.warning("Attempting to enable an active shader program.")

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Disable the program.

        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return:
        """
        if self.enabled:
            gl.glUseProgram(0)
        else:
            self._log.warning("Attempting to disable an inactive shader program.")

        return False


@attr.s(slots=True)
class Model(object):
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

    @classmethod
    def delete_vertex_arrays(cls, num, obj):
        if bool(gl.glDeleteVertexArrays) and obj >= 0:
            gl.glDeleteVertexArrays(num, obj)

    @classmethod
    def delete_buffers(cls, num, obj):
        if bool(gl.glDeleteBuffers) and obj >= 0:
            gl.glDeleteBuffers(num, obj)

    @classmethod
    def create(cls, mesh, shader, texture=None):
        with contextlib.ExitStack() as ctx:
            warnings.warn("Possibly rewrite the GL calls in Direct State Access style.", TodoWarning)
            # Create and bind the Vertex Array Object
            vao = int(gl.glGenVertexArrays(1))
            ctx.callback(cls.delete_vertex_arrays, 1, vao)
            gl.glBindVertexArray(vao)

            # Compile the shader program
            vertex_shader = OpenGlShader.create(gl.GL_VERTEX_SHADER, shader.vertex_source)
            fragment_shader = OpenGlShader.create(gl.GL_FRAGMENT_SHADER, shader.fragment_source)
            program = OpenGlProgram.create((vertex_shader, fragment_shader))

            # Create the texture only if necessary
            tex = None
            if any(isinstance(a, TextureAttribute) for a in mesh.attributes):
                if texture is not None:
                    tex = Texture.create(texture)
            elif texture is not None:
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
                    a.location, a.components, mesh.data_type, False, a.stride_bytes, a.start_ptr
                )

            gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, 0)
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
            gl.glBindVertexArray(0)

            ctx_exit = ctx.pop_all()

            return cls(vao, vbo, ibo, mesh.draw_mode, len(mesh.index), mesh.index_type, tex, program, ctx_exit)

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
