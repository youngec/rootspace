#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A collection of exceptions used by Rootspace.
"""

import sdl2.error
import sdl2.sdlttf


class SetupError(Exception):
    """
    This exception indicates that the project was installed incorrectly.
    """
    pass


class SDLError(Exception):
    """
    This exception indicates that there was an issue with the SDL2 library.
    """

    def __init__(self, msg=None):
        super(SDLError, self).__init__()

        if msg is None:
            self.msg = sdl2.error.SDL_GetError().decode("utf-8")
        else:
            self.msg = msg

    def __str__(self):
        return repr(self.msg)


class SDLTTFError(Exception):
    """
    This exception indicates that there was an issue with SDL2 TTF.
    """

    def __init__(self, msg=None):
        super(SDLTTFError, self).__init__()

        if msg is None:
            self.msg = sdl2.sdlttf.TTF_GetError().decode("utf-8")
        else:
            self.msg = msg

    def __str__(self):
        return repr(self.msg)


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
