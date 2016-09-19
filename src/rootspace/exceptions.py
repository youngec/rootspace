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
            self.msg = sdl2.error.SDL_GetError()
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
            self.msg = sdl2.sdlttf.TTF_GetError()
        else:
            self.msg = msg

    def __str__(self):
        return repr(self.msg)
