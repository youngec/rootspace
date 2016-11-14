# -*- coding: utf-8 -*-

import sys
import os

from ._version import get_versions


__version__ = get_versions()['version']
del get_versions

# Add OpenGL to the library path, so that PyOpenGL can find it
if sys.platform == "linux" and os.path.isdir("/run/opengl-driver"):
    os.environ["LIBRARY_PATH"] = "/run/opengl-driver/lib:/run/opengl-driver-32/lib:{}".format(os.environ.get("LIBRARY_PATH", ""))

