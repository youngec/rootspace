# -*- coding: utf-8 -*-

"""Provides wrappers for OpenGL concepts."""

import logging
import contextlib
import warnings
import ctypes

import attr
import numpy
import OpenGL.GL as gl
from attr.validators import instance_of

from .exceptions import OpenGLError, TodoWarning


@attr.s
class Model(object):
    """
    Abstract away the concept of a model: vertices, material, shaders.
    """
    # TODO: Possibly introduce a Lexer that can parse Wavefront OBJ files.
    # Reference to PLY lexer: http://www.dabeaz.com/ply/ply.html
    # Reference to OBJ file format: https://people.cs.clemson.edu/~dhouse/courses/405/docs/brief-obj-file-format.html
    vertices = attr.ib(validator=instance_of(numpy.ndarray))
    texture = attr.ib(validator=instance_of(numpy.ndarray))
    num_vert_components = attr.ib(validator=instance_of(int))
    num_tex_components = attr.ib(validator=instance_of(int))
    vert_stride = attr.ib(validator=instance_of(int))
    tex_stride = attr.ib(validator=instance_of(int))
    vert_start_idx = attr.ib(validator=instance_of(int))
    tex_start_idx = attr.ib(validator=instance_of(int))
    vertex_shader = attr.ib(validator=instance_of(str))
    fragment_shader = attr.ib(validator=instance_of(str))
    vertex_coord_name = attr.ib(validator=instance_of(str))
    texture_coord_name = attr.ib(validator=instance_of(str))
    draw_mode = attr.ib()
    draw_start_index = attr.ib(validator=instance_of(int))

    @property
    def num_vertices(self):
        return len(self.vertices) // (self.num_vert_components + self.num_tex_components)

    @property
    def vert_stride_bytes(self):
        return self.vert_stride * ctypes.sizeof(ctypes.c_float)

    @property
    def tex_stride_bytes(self):
        return self.tex_stride * ctypes.sizeof(ctypes.c_float)

    @property
    def vert_start_ptr(self):
        return ctypes.c_void_p(self.vert_start_idx * ctypes.sizeof(ctypes.c_float))

    @property
    def tex_start_ptr(self):
        return ctypes.c_void_p(self.tex_start_idx * ctypes.sizeof(ctypes.c_float))

    @classmethod
    def create_cube(cls, texture_data, vertex_shader, fragment_shader, vertex_coord_name, texture_coord_name):
        vertices = numpy.array([
            -1, -1, -1, 0, 0,
            1, -1, -1, 1, 0,
            -1, -1, 1, 0, 1,
            1, -1, -1, 1, 0,
            1, -1, 1, 1, 1,
            -1, -1, 1, 0, 1,
            -1, 1, -1, 0, 0,
            -1, 1, 1, 0, 1,
            1, 1, -1, 1, 0,
            1, 1, -1, 1, 0,
            -1, 1, 1, 0, 1,
            1, 1, 1, 1, 1,
            -1, -1, 1, 1, 0,
            1, -1, 1, 0, 0,
            -1, 1, 1, 1, 1,
            1, -1, 1, 0, 0,
            1, 1, 1, 0, 1,
            -1, 1, 1, 1, 1,
            -1, -1, -1, 0, 0,
            -1, 1, -1, 0, 1,
            1, -1, -1, 1, 0,
            1, -1, -1, 1, 0,
            -1, 1, -1, 0, 1,
            1, 1, -1, 1, 1,
            -1, -1, 1, 0, 1,
            -1, 1, -1, 1, 0,
            -1, -1, -1, 0, 0,
            -1, -1, 1, 0, 1,
            -1, 1, 1, 1, 1,
            -1, 1, -1, 1, 0,
            1, -1, 1, 1, 1,
            1, -1, -1, 1, 0,
            1, 1, -1, 0, 0,
            1, -1, 1, 1, 1,
            0, 1, -1, 0, 0,
            1, 1, 1, 0, 1
        ], dtype=numpy.float32)
        num_vert_components = 3
        num_tex_components = 2
        vert_stride = 5
        tex_stride = 5
        vert_start_idx = 0
        tex_start_idx = num_vert_components
        draw_mode = gl.GL_TRIANGLES
        draw_start_index = 0

        return cls(vertices, texture_data, num_vert_components, num_tex_components,
                   vert_stride, tex_stride, vert_start_idx, tex_start_idx,
                   vertex_shader, fragment_shader, vertex_coord_name, texture_coord_name,
                   draw_mode, draw_start_index)


@attr.s
class OpenGlTexture(object):
    """Texture encapsulates an OpenGL texture."""

    _obj = attr.ib(validator=instance_of(int))
    _shape = attr.ib(validator=instance_of(tuple))
    _ctx_exit = attr.ib(validator=instance_of(contextlib.ExitStack), repr=False)

    @classmethod
    def texture_format(cls, data: numpy.ndarray):
        if len(data.shape) == 2:
            return gl.GL_LUMINANCE
        elif len(data.shape) == 3:
            if data.shape[2] == 2:
                return gl.GL_LUMINANCE_ALPHA
            elif data.shape[2] == 3:
                return gl.GL_RGB
            elif data.shape[2] == 4:
                return gl.GL_RGBA

        raise ValueError("Cannot determine the texture format for the supplied image data.")

    @classmethod
    def texture_dtype(cls, data: numpy.ndarray):
        if data.dtype == numpy.uint8:
            return gl.GL_UNSIGNED_BYTE
        if data.dtype == numpy.float:
            return gl.GL_FLOAT
        else:
            raise NotImplementedError("Have not implemented all data type conversions yet.")

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
            ctx_mgr.callback(gl.glDeleteTextures, obj)

            # Set texture parameters
            gl.glBindTexture(gl.GL_TEXTURE_2D, obj)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, min_filter)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, mag_filter)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, wrap_mode)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, wrap_mode)

            # Set the texture data
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, shape[0], shape[1], 0, image_format, image_dtype, data)
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
    """Shader encapsulates an OpenGL shader."""

    _obj = attr.ib(validator=instance_of(int))
    _ctx_exit = attr.ib(validator=instance_of(contextlib.ExitStack), repr=False)

    @classmethod
    def create(cls, shader_type, shader_source):
        with contextlib.ExitStack() as ctx_mgr:
            # Create the shader object
            obj = int(gl.glCreateShader(shader_type))
            if obj == 0:
                raise OpenGLError("Failed to create a shader object.")
            ctx_mgr.callback(gl.glDeleteShader, obj)

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
    """Program encapsulates an OpenGL shader program."""

    _obj = attr.ib(validator=instance_of(int))
    _log = attr.ib(validator=instance_of(logging.Logger), repr=False)
    _ctx_exit = attr.ib(validator=instance_of(contextlib.ExitStack), repr=False)

    @classmethod
    def create(cls, shaders):
        with contextlib.ExitStack() as ctx_mgr:
            # Create the shader program
            obj = int(gl.glCreateProgram())
            if obj == 0:
                raise OpenGLError("Failed to create a shader program.")
            ctx_mgr.callback(gl.glDeleteProgram, obj)

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
    vao = attr.ib(validator=instance_of(int))
    vbo = attr.ib(validator=instance_of(int))
    mode = attr.ib(validator=instance_of(int))
    start_index = attr.ib(validator=instance_of(int))
    num_vertices = attr.ib(validator=instance_of(int))
    texture = attr.ib(validator=instance_of(OpenGlTexture))
    program = attr.ib(validator=instance_of(OpenGlProgram))
    _ctx_exit = attr.ib(validator=instance_of(contextlib.ExitStack), repr=False)

    @classmethod
    def create(cls, model: Model):
        with contextlib.ExitStack() as ctx:
            warnings.warn("Possibly rewrite the GL calls in Direct State Access style.", TodoWarning)
            # Create and bind the Vertex Array Object
            vao = int(gl.glGenVertexArrays(1))
            ctx.callback(gl.glDeleteVertexArrays, 1, vao)
            gl.glBindVertexArray(vao)

            # Compile the shader program
            vertex_shader = OpenGlShader.create(gl.GL_VERTEX_SHADER, model.vertex_shader)
            fragment_shader = OpenGlShader.create(gl.GL_FRAGMENT_SHADER, model.fragment_shader)
            program = OpenGlProgram.create((vertex_shader, fragment_shader))

            position_location = program.attribute_location(model.vertex_coord_name)
            tex_coord_location = program.attribute_location(model.texture_coord_name)

            # Create the texture
            tex = OpenGlTexture.create(model.texture)

            # Initialise the vertex buffer
            vbo = int(gl.glGenBuffers(1))
            ctx.callback(gl.glDeleteBuffers, 1, vbo)
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
            gl.glBufferData(gl.GL_ARRAY_BUFFER, model.vertices.nbytes, model.vertices, gl.GL_STATIC_DRAW)

            # Set the appropriate pointers
            gl.glEnableVertexAttribArray(position_location)
            gl.glVertexAttribPointer(
                position_location, model.num_vert_components, gl.GL_FLOAT, False,
                model.vert_stride_bytes, model.vert_start_ptr
            )
            gl.glEnableVertexAttribArray(tex_coord_location)
            gl.glVertexAttribPointer(
                tex_coord_location, model.num_tex_components, gl.GL_FLOAT, False,
                model.tex_stride_bytes, model.tex_start_ptr
            )

            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
            gl.glBindVertexArray(0)

            ctx_exit = ctx.pop_all()

            return cls(vao, vbo, model.draw_mode, model.draw_start_index, model.num_vertices, tex, program, ctx_exit)

    def __del__(self):
        self._ctx_exit.close()
