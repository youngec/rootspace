# -*- coding: utf-8 -*-

import os
import sys

# Add the SDL2 library path (this is necessary for some linux versions)
if sys.platform == "linux" and os.path.isdir("/run/current-system"):
    os.environ["PYSDL2_DLL_PATH"] = "/run/current-system/sw/lib:{}".format(os.environ.get("PYSDL2_DLL_PATH", ""))
