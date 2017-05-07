# -*- coding: utf-8 -*-

"""Provides wrappers for OpenGL concepts."""

import contextlib
import pathlib
from typing import Tuple, Any, Type

import OpenGL.GL as gl
import PIL.Image

from ._math import Matrix
from .exceptions import OpenGLError


class Shader(object):
    """
    Shader is an on-CPU representation of a shader program.
    """

    def __init__(self, vertex_source: str, fragment_source: str) -> None:
        self.vertex_source = vertex_source
        self.fragment_source = fragment_source

    @classmethod
    def create(cls, vertex_shader_path: pathlib.Path,
               fragment_shader_path: pathlib.Path) -> "Shader":
        """
        Create an on-CPU representation of a shader.
        """
        return cls(vertex_shader_path.read_text(),
                   fragment_shader_path.read_text())


class Texture(object):
    """
    OpenGlTexture encapsulates an OpenGL texture.
    """
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

    def __init__(self, obj: int, shape: Tuple[int, int],
                 ctx_exit: contextlib.ExitStack) -> None:
        self.obj = obj
        self.shape = shape
        self._ctx_exit = ctx_exit

    @classmethod
    def _delete_textures(cls, obj: int) -> None:
        if bool(gl.glDeleteTextures) and obj > 0:
            gl.glDeleteTextures(obj)

    @classmethod
    def create(cls, data: PIL.Image.Image,
               min_filter: int = gl.GL_LINEAR,
               mag_filter: int = gl.GL_LINEAR,
               wrap_mode: int = gl.GL_CLAMP_TO_EDGE,
               flip_lr: bool = False,
               flip_tb: bool = True) -> "Texture":
        # Extract type and size information from the image
        image_format = cls.texture_formats[data.mode]
        image_dtype = cls.texture_data_types[data.mode]
        shape = data.size

        with contextlib.ExitStack() as ctx_mgr:
            # Create the texture object
            obj = gl.glGenTextures(1)
            if obj == 0:
                raise OpenGLError("Failed to create a texture object.")
            ctx_mgr.callback(cls._delete_textures, obj)

            # Set texture parameters
            gl.glBindTexture(gl.GL_TEXTURE_2D, obj)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER,
                               min_filter)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER,
                               mag_filter)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S,
                               wrap_mode)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T,
                               wrap_mode)

            if flip_lr:
                data = data.transpose(PIL.Image.FLIP_LEFT_RIGHT)

            if flip_tb:
                data = data.transpose(PIL.Image.FLIP_TOP_BOTTOM)

            # Set the texture data
            gl.glTexImage2D(
                gl.GL_TEXTURE_2D, 0, image_format, shape[0], shape[1], 0,
                image_format, image_dtype, data.tobytes()
            )
            gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

            return cls(obj, shape, ctx_mgr.pop_all())

    def __del__(self):
        self._ctx_exit.close()

    @property
    def enabled(self) -> bool:
        return gl.glGetIntegerv(gl.GL_TEXTURE_BINDING_2D) == self.obj

    def __enter__(self) -> "Texture":
        """
        Enable the texture.

        :return:
        """
        if not self.enabled:
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.obj)

        return self

    def __exit__(self, exc_type: Type[Exception], exc_val: Exception,
                 exc_tb: Any) -> bool:
        """
        Disable the texture.

        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return:
        """
        if self.enabled:
            gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

        return False


class OpenGlShader(object):
    """OpenGlShader encapsulates an OpenGL shader."""

    def __init__(self, obj: int, ctx_exit: contextlib.ExitStack) -> None:
        self.obj = obj
        self._ctx_exit = ctx_exit

    @classmethod
    def _delete_shader(cls, obj: int) -> None:
        if bool(gl.glDeleteShader) and obj > 0:
            gl.glDeleteShader(obj)

    @classmethod
    def create(cls, shader_type: int, shader_source: str) -> "OpenGlShader":
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

            return cls(obj, ctx_mgr.pop_all())

    def __del__(self):
        self._ctx_exit.close()


class OpenGlProgram(object):
    """
    OpenGlProgram encapsulates an OpenGL shader program.
    """

    def __init__(self, obj: int, ctx_exit: contextlib.ExitStack) -> None:
        self.obj = obj
        self._ctx_exit = ctx_exit

    @classmethod
    def _delete_program(cls, obj: int) -> None:
        if bool(gl.glDeleteProgram) and obj > 0:
            gl.glDeleteProgram(obj)

    @classmethod
    def create(cls, *shaders) -> "OpenGlProgram":
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

            return cls(obj, ctx_mgr.pop_all())

    def __del__(self):
        self._ctx_exit.close()

    @property
    def enabled(self) -> bool:
        return gl.glGetIntegerv(gl.GL_CURRENT_PROGRAM) == self.obj

    def uniform_location(self, name: str) -> int:
        loc = gl.glGetUniformLocation(self.obj, name)
        if loc == -1:
            raise OpenGLError(
                "Could not find the shader uniform '{}'.".format(name))
        else:
            return loc

    def attribute_location(self, name: str) -> int:
        loc = gl.glGetAttribLocation(self.obj, name)
        if loc == -1:
            raise OpenGLError(
                "Could not find the shader attribute '{}'.".format(name))
        else:
            return loc

    def uniform(self, name: str, value: Any) -> None:
        loc = self.uniform_location(name)
        if isinstance(value, Matrix):
            if value.shape == (4, 4):
                gl.glUniformMatrix4fv(loc, 1, True, value.to_bytes())
            else:
                raise NotImplementedError(
                    "Cannot set any other matrix shapes yet.")
        elif isinstance(value, int):
            gl.glUniform1i(loc, value)
        elif isinstance(value, float):
            gl.glUniform1f(loc, value)
        else:
            raise NotImplementedError("Cannot set any other data types yet.")

    def __enter__(self) -> "OpenGlProgram":
        """
        Enable the program.

        :return:
        """
        if not self.enabled:
            gl.glUseProgram(self.obj)

        return self

    def __exit__(self, exc_type: Type[Exception], exc_val: Exception,
                 exc_tb: Any) -> bool:
        """
        Disable the program.

        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return:
        """
        if self.enabled:
            gl.glUseProgram(0)

        return False
