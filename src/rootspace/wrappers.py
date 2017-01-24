# -*- coding: utf-8 -*-

"""Provides wrappers for OpenGL concepts."""

import contextlib
import logging
import warnings

import PIL.Image
import OpenGL.GL as gl
import attr
import numpy
from attr.validators import instance_of

from .exceptions import OpenGLError, FixmeWarning


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
    def create(cls, *shaders):
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
