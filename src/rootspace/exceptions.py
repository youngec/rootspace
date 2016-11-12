#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A collection of exceptions used by Rootspace.
"""


class SetupError(Exception):
    """
    This exception indicates that the project was installed incorrectly.
    """
    pass


class GLFWError(Exception):
    """
    This exception indicates that the GLFW library failed in some respect.
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


class FixmeWarning(Warning):
    """
    This warning is raised if something should be fixed.
    """
    pass
