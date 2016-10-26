# -*- coding: utf-8 -*-

# Define the project version
from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

# Add the SDL2 library path (this is necessary for some linux versions)
import sys
import os
if sys.platform == "linux" and os.path.isdir("/run/current-system"):
    os.environ["PYSDL2_DLL_PATH"] = "/run/current-system/sw/lib:{}".format(os.environ.get("PYSDL2_DLL_PATH", ""))

