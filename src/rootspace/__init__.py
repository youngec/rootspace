# -*- coding: utf-8 -*-

import sys
import os

from ._version import get_versions


__version__ = get_versions()['version']
del get_versions

# Add the SDL2 library path (this is necessary for some linux versions)
if sys.platform == "linux" and os.path.isdir("/run/current-system"):
    pysdl2_dll = "/run/current-system/sw/lib:{}".format(
        os.environ.get("PYSDL2_DLL_PATH", "")
    )
    os.environ["PYSDL2_DLL_PATH"] = pysdl2_dll
