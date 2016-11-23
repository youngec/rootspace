# -*- coding: utf-8 -*-

import sys
import os

import OpenGL

from ._version import get_versions


# Determine the project version using versioneer
__version__ = get_versions()['version']
del get_versions

# Add OpenGL to the library path, so that PyOpenGL can find it
if sys.platform == "linux" and os.path.isdir("/run/opengl-driver"):
    os.environ["LIBRARY_PATH"] = "/run/opengl-driver/lib:/run/opengl-driver-32/lib:{}".format(os.environ.get("LIBRARY_PATH", ""))

# Configure PyOpenGL
#OpenGL.ERROR_ON_COPY = True
