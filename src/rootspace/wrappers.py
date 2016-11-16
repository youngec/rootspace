# -*- coding: utf-8 -*-

import logging
import contextlib

import attr
import OpenGL.GL as gl
from attr.validators import instance_of

from .exceptions import OpenGLError


@attr.s
class Shader(object):
    _obj = attr.ib(validator=instance_of(int))
    _log = attr.ib(validator=instance_of(logging.Logger), repr=False)
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
                log_length = gl.glGetShaderiv(obj, gl.GL_INFO_LOG_LENGTH)
                log_string = gl.glGetShaderInfoLog(obj, log_length, None)
                raise OpenGLError(log_string.decode("utf-8"))

            log = logging.getLogger("{}.{}".format(__name__, cls.__name__))

            ctx_exit = ctx_mgr.pop_all()

            return cls(obj, log, ctx_exit)

    def __del__(self):
        self._ctx_exit.close()

    @property
    def obj(self):
        self._log.debug("Access to Shader location reference")
        return self._obj

@attr.s
class Program(object):
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
                log_length = gl.glGetProgramiv(obj, gl.GL_INFO_LOG_LENGTH)
                log_string = gl.glGetProgramInfoLog(obj, log_length, None)
                raise OpenGLError(log_string.decode("utf-8"))

            log = logging.getLogger("{}.{}".format(__name__, cls.__name__))

            ctx_exit = ctx_mgr.pop_all()

            return cls(obj, log, ctx_exit)

    def __del__(self):
        self._ctx_exit.close()

    @property
    def obj(self):
        self._log.debug("Access to Program location reference.")
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

    def uniform(self, name, values, transpose=True):
        loc = self.uniform_location(name)

    def attribute(self, name, values):
        loc = self.attribute_location(name)

