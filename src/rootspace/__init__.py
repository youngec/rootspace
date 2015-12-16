#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import warnings

# Define the project version
from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

# Configure the logging system
rs_logger = logging.getLogger("rootspace")
logging_default_handler = logging.StreamHandler()
logging_default_formatter = logging.Formatter(
    fmt="%(asctime)s - %(name)s - %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logging_default_handler.setFormatter(logging_default_formatter)
rs_logger.addHandler(logging_default_handler)
rs_logger.setLevel(logging.WARNING)
warnings.simplefilter("default")
logging.captureWarnings(True)
