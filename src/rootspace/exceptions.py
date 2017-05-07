# -*- coding: utf-8 -*-

"""
A collection of exceptions used by Rootspace.
"""


class TodoWarning(Warning):
    """
    This warning is raised if something remains to be done, but is not necessary.
    """
    pass


class FixmeWarning(Warning):
    """
    This warning is raised if something should be fixed.
    """
    pass


class SerializationError(Exception):
    """
    This exception indicates that the (de)-serialization of objects failed.
    """
    pass


class GLFWError(Exception):
    """
    This exception indicates that the GLFW library failed in some respect.
    """
    pass


class OpenGLError(Exception):
    """
    This exception indicates that some OpenGL call failed.
    """
    pass


class RootspaceFileNotFoundError(Exception):
    """
    This exception stands for an in-game FileNotFoundError.
    """
    pass


class RootspaceFileExistsError(Exception):
    """
    This exception stands for an in-game FileExistsError.
    """
    pass


class RootspaceIsADirectoryError(Exception):
    """
    This exception stands for an in-game IsADirectoryError.
    """
    pass


class RootspaceNotADirectoryError(Exception):
    """
    This exception stands for an in-game NotADirectoryError.
    """
    pass


class RootspacePermissionError(Exception):
    """
    This exception stands for an in-game PermissionError.
    """
    pass


class RootspaceNotAnExecutableError(Exception):
    """
    This exception is raised if a particular file system node is not executable but has permissions set as such.
    """
    pass

