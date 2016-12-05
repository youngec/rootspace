# -*- coding: utf-8 -*-

"""Provides wrappers for OpenGL concepts."""

import logging
import contextlib

import attr
import numpy
import OpenGL.GL as gl
from attr.validators import instance_of

from .exceptions import OpenGLError


# TODO: Possibly introduce a Lexer that can parse Wavefront OBJ files.
# Reference to PLY lexer: http://www.dabeaz.com/ply/ply.html
# Reference to OBJ file format: https://people.cs.clemson.edu/~dhouse/courses/405/docs/brief-obj-file-format.html


@attr.s
class Texture(object):
    """Texture encapsulates an OpenGL texture."""

    _obj = attr.ib(validator=instance_of(int))
    _shape = attr.ib(validator=instance_of(tuple))
    _ctx_exit = attr.ib(validator=instance_of(contextlib.ExitStack), repr=False)

    @classmethod
    def texture_format(cls, image_data):
        if len(image_data.shape) == 2:
            return gl.GL_LUMINANCE
        elif len(image_data.shape) == 3:
            if image_data.shape[2] == 2:
                return gl.GL_LUMINANCE_ALPHA
            elif image_data.shape[2] == 3:
                return gl.GL_RGB
            elif image_data.shape[2] == 4:
                return gl.GL_RGBA

        raise ValueError("Cannot determine the texture format for the supplied image data.")

    @classmethod
    def texture_dtype(cls, image_data):
        if image_data.dtype == numpy.uint8:
            return gl.GL_UNSIGNED_BYTE
        if image_data.dtype == numpy.float:
            return gl.GL_FLOAT
        else:
            raise NotImplementedError("Have not implemented all data type conversions yet.")

    @classmethod
    def create(cls, image_data, min_filter=gl.GL_LINEAR, mag_filter=gl.GL_LINEAR, wrap_mode=gl.GL_CLAMP_TO_EDGE):
        with contextlib.ExitStack() as ctx_mgr:
            image_format = cls.texture_format(image_data)
            image_dtype = cls.texture_dtype(image_data)
            shape = image_data.shape[:2]

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
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, shape[0], shape[1], 0, image_format, image_dtype, image_data)
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
class Shader(object):
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
class Program(object):
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
