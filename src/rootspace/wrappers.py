# -*- coding: utf-8 -*-

"""Provides wrappers for OpenGL concepts."""

import contextlib
import ctypes
import logging
import warnings

import OpenGL.GL as gl
from OpenGL.constant import Constant
import attr
import numpy
from attr.validators import instance_of

from .exceptions import OpenGLError, TodoWarning


@attr.s
class Mesh(object):
    vertices = attr.ib()
    vertex_components = attr.ib(validator=instance_of(int))
    texture_components = attr.ib(validator=instance_of(int))
    vertex_stride = attr.ib(validator=instance_of(int))
    texture_stride = attr.ib(validator=instance_of(int))
    vertex_start_idx = attr.ib(validator=instance_of(int))
    texture_start_idx = attr.ib(validator=instance_of(int))
    draw_mode = attr.ib(validator=instance_of(Constant))
    draw_start_index = attr.ib(validator=instance_of(int))

    @property
    def num_vertices(self):
        return len(self.vertices) // (self.vertex_components + self.texture_components)

    @property
    def vertex_stride_bytes(self):
        return self.vertex_stride * ctypes.sizeof(ctypes.c_float)

    @property
    def texture_stride_bytes(self):
        return self.texture_stride * ctypes.sizeof(ctypes.c_float)

    @property
    def vertex_start_ptr(self):
        return ctypes.c_void_p(self.vertex_start_idx * ctypes.sizeof(ctypes.c_float))

    @property
    def texture_start_ptr(self):
        return ctypes.c_void_p(self.texture_start_idx * ctypes.sizeof(ctypes.c_float))

    @classmethod
    def create_cube(cls):
        return cls(
            numpy.array([
                -1, -1, -1, 0, 0, 1, -1, -1, 1, 0, -1, -1, 1, 0, 1,
                1, -1, -1, 1, 0, 1, -1, 1, 1, 1, -1, -1, 1, 0, 1,
                -1, 1, -1, 0, 0, -1, 1, 1, 0, 1, 1, 1, -1, 1, 0,
                1, 1, -1, 1, 0, -1, 1, 1, 0, 1, 1, 1, 1, 1, 1,
                -1, -1, 1, 1, 0, 1, -1, 1, 0, 0, -1, 1, 1, 1, 1,
                1, -1, 1, 0, 0, 1, 1, 1, 0, 1, -1, 1, 1, 1, 1,
                -1, -1, -1, 0, 0, -1, 1, -1, 0, 1, 1, -1, -1, 1, 0,
                1, -1, -1, 1, 0, -1, 1, -1, 0, 1, 1, 1, -1, 1, 1,
                -1, -1, 1, 0, 1, -1, 1, -1, 1, 0, -1, -1, -1, 0, 0,
                -1, -1, 1, 0, 1, -1, 1, 1, 1, 1, -1, 1, -1, 1, 0,
                1, -1, 1, 1, 1, 1, -1, -1, 1, 0, 1, 1, -1, 0, 0,
                1, -1, 1, 1, 1, 0, 1, -1, 0, 0, 1, 1, 1, 0, 1
            ], dtype=numpy.float32),
            3, 2, 5, 5, 0, 3, gl.GL_TRIANGLES, 0
        )


@attr.s
class Shader(object):
    vertex_source = attr.ib(validator=instance_of(str))
    fragment_source = attr.ib(validator=instance_of(str))
    vertex_coord = attr.ib(validator=instance_of(str))
    texture_coord = attr.ib(validator=instance_of(str))

    @classmethod
    def create(cls, vertex_shader_path, fragment_shader_path, vertex_coord, texture_coord):
        """
        Create an on-CPU representation of a shader.

        :param vertex_shader_path:
        :param fragment_shader_path:
        :param vertex_coord:
        :param texture_coord:
        :return:
        """
        vertex_source = vertex_shader_path.read_text()
        fragment_source = fragment_shader_path.read_text()
        return cls(vertex_source, fragment_source, vertex_coord, texture_coord)


@attr.s
class OpenGlTexture(object):
    """
    OpenGlTexture encapsulates an OpenGL texture.
    """

    _obj = attr.ib(validator=instance_of(int))
    _shape = attr.ib(validator=instance_of(tuple))
    _ctx_exit = attr.ib(validator=instance_of(contextlib.ExitStack), repr=False)

    @classmethod
    def _delete_textures(cls, obj):
        if bool(gl.glDeleteTextures) and obj >= 0:
            gl.glDeleteTextures(obj)

    @classmethod
    def texture_format(cls, data: numpy.ndarray):
        if len(data.shape) == 2:
            return gl.GL_RED
        elif len(data.shape) == 3:
            if data.shape[2] == 2:
                return gl.GL_RG
            elif data.shape[2] == 3:
                return gl.GL_RGB
            elif data.shape[2] == 4:
                return gl.GL_RGBA

        raise ValueError("Cannot determine the texture format for the supplied image data.")

    @classmethod
    def texture_dtype(cls, data: numpy.ndarray):
        if data.dtype == numpy.int8:
            dtype = gl.GL_BYTE
        elif data.dtype == numpy.uint8:
            dtype = gl.GL_UNSIGNED_BYTE
        elif data.dtype == numpy.int16:
            dtype = gl.GL_SHORT
        elif data.dtype == numpy.uint16:
            dtype = gl.GL_UNSIGNED_SHORT
        elif data.dtype == numpy.int32:
            dtype = gl.GL_INT
        elif data.dtype == numpy.uint32:
            dtype = gl.GL_UNSIGNED_INT
        elif data.dtype == numpy.float:
            dtype = gl.GL_FLOAT
        elif data.dtype == numpy.double:
            dtype = gl.GL_DOUBLE
        else:
            raise ValueError("Cannot determine the texture data type for the supplied image data.")

        return dtype

    @classmethod
    def create(cls, data, min_filter=gl.GL_LINEAR, mag_filter=gl.GL_LINEAR, wrap_mode=gl.GL_CLAMP_TO_EDGE):
        with contextlib.ExitStack() as ctx_mgr:
            image_format = cls.texture_format(data)
            image_dtype = cls.texture_dtype(data)
            shape = data.shape[:2]

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
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, image_format, shape[0], shape[1], 0, image_format, image_dtype, data)
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

    def enable(self):
        if not self.enabled:
            gl.glBindTexture(gl.GL_TEXTURE_2D, self._obj)
        else:
            self._log.warning("Attempting to enable an active texture.")

    def disable(self):
        if self.enabled:
            gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
        else:
            self._log.warning("Attempting to disable an inactive texture.")


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

    def enable(self):
        if not self.enabled:
            gl.glUseProgram(self._obj)
        else:
            self._log.warning("Attempting to enable an active shader program.")

    def disable(self):
        if self.enabled:
            gl.glUseProgram(0)
        else:
            self._log.warning("Attempting to disable an inactive shader program.")

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


@attr.s(slots=True)
class OpenGlModel(object):
    """
    OpenGlModel encapsulates all that belongs to a graphical representation of an object, stored on the GPU.
    """
    vao = attr.ib(validator=instance_of(int))
    vbo = attr.ib(validator=instance_of(int))
    mode = attr.ib(validator=instance_of(int))
    start_index = attr.ib(validator=instance_of(int))
    num_vertices = attr.ib(validator=instance_of(int))
    texture = attr.ib(validator=instance_of(OpenGlTexture))
    program = attr.ib(validator=instance_of(OpenGlProgram))
    _ctx_exit = attr.ib(validator=instance_of(contextlib.ExitStack), repr=False)

    @classmethod
    def create(cls, mesh, texture, shader):
        with contextlib.ExitStack() as ctx:
            warnings.warn("Possibly rewrite the GL calls in Direct State Access style.", TodoWarning)
            # Create and bind the Vertex Array Object
            vao = int(gl.glGenVertexArrays(1))
            ctx.callback(gl.glDeleteVertexArrays, 1, vao)
            gl.glBindVertexArray(vao)

            # Compile the shader program
            vertex_shader = OpenGlShader.create(gl.GL_VERTEX_SHADER, shader.vertex_source)
            fragment_shader = OpenGlShader.create(gl.GL_FRAGMENT_SHADER, shader.fragment_source)
            program = OpenGlProgram.create((vertex_shader, fragment_shader))

            # Create the texture
            tex = OpenGlTexture.create(texture)

            # Initialise the vertex buffer
            vbo = int(gl.glGenBuffers(1))
            ctx.callback(gl.glDeleteBuffers, 1, vbo)
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
            gl.glBufferData(gl.GL_ARRAY_BUFFER, mesh.vertices.nbytes, mesh.vertices, gl.GL_STATIC_DRAW)

            # Set the appropriate pointers
            # FIXME: Make pointer assignment more flexible
            position_location = program.attribute_location(shader.vertex_coord)
            gl.glEnableVertexAttribArray(position_location)
            gl.glVertexAttribPointer(
                position_location, mesh.vertex_components, gl.GL_FLOAT, False,
                mesh.vertex_stride_bytes, mesh.vertex_start_ptr
            )
            tex_coord_location = program.attribute_location(shader.texture_coord)
            gl.glEnableVertexAttribArray(tex_coord_location)
            gl.glVertexAttribPointer(
                tex_coord_location, mesh.texture_components, gl.GL_FLOAT, False,
                mesh.texture_stride_bytes, mesh.texture_start_ptr
            )

            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
            gl.glBindVertexArray(0)

            ctx_exit = ctx.pop_all()

            return cls(vao, vbo, mesh.draw_mode, mesh.draw_start_index, mesh.num_vertices, tex, program, ctx_exit)

    def __del__(self):
        self._ctx_exit.close()
