#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import collections
import logging
import warnings
from typing import Optional, Any, Union

Loggers = collections.namedtuple("Loggers", ("project", "py_warnings"))


def get_log_level(verbosity: int) -> int:
    """
    Determine the logging level from the verbose and debug flags.
    """
    if verbosity <= 0:
        log_level = logging.ERROR
    elif verbosity == 1:
        log_level = logging.WARN
    elif verbosity == 2:
        log_level = logging.INFO
    elif verbosity >= 3:
        log_level = logging.DEBUG
    else:
        raise ValueError("Only four verbosity levels are understood: 0, 1, 2 and 3.")

    return log_level


def configure_logger(name: str, log_level: int, log_path: Optional[str] = None, with_warnings: Optional[bool] = True) -> Loggers:
    """
    Configure the project logger of the specified name
    using colorlog.

    :param name:
    :param log_level:
    :param log_path:
    :param with_warnings:
    :return:
    """
    default_handler = None
    if log_path is not None:
        default_handler = logging.FileHandler(log_path)
        default_handler.setLevel(log_level)
        plain_formatter = logging.Formatter(
            "{levelname:8s} @{name}: {message}",
            style="{"
        )
        default_handler.setFormatter(plain_formatter)
    else:
        default_handler = logging.StreamHandler()
        default_handler.setLevel(log_level)
        plain_formatter = logging.Formatter(
            "{levelname:8s} @{name}: {message}",
            style="{"
        )
        default_handler.setFormatter(plain_formatter)

    # Configure the rootspace logger
    project_logger = logging.getLogger(name)
    project_logger.setLevel(log_level)
    project_logger.addHandler(default_handler)

    py_warnings = None
    if with_warnings:
        # Configure the warnings logger
        warnings.simplefilter("default")
        logging.captureWarnings(True)
        py_warnings = logging.getLogger("py.warnings")
        py_warnings.setLevel(log_level)
        py_warnings.addHandler(default_handler)

    return Loggers(project_logger, py_warnings)
