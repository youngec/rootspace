# -*- coding: utf-8 -*-

import sys
import os

from ._version import get_versions


# Determine the project version using versioneer
__version__ = get_versions()['version']
del get_versions

# Add OpenGL to the library path, so that PyOpenGL can find it
if sys.platform == "linux" and os.path.isdir("/run/opengl-driver"):
    nixos_lib_path = "/run/opengl-driver/lib:/run/opengl-driver-32/lib"
    os.environ["LIBRARY_PATH"] += os.pathsep + nixos_lib_path
elif sys.platform == "win32":
    project_path = os.path.dirname(__file__)
    win32_lib_path = os.path.join(project_path, "external")
    os.environ["PATH"] += os.pathsep + win32_lib_path

# Configure PyOpenGL
# OpenGL.ERROR_ON_COPY = True

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
