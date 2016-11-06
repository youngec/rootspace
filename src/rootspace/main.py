#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import warnings

import click
import colorlog

from ._version import get_versions
from .core import Engine
from .projects import RootSpace
from .utilities import get_log_level


@click.command()
@click.option("-v", "--verbose", count=True, help="Select the level of verbosity.")
@click.option("--debug", is_flag=True, help="Enable debug mode.")
@click.option("--profile", is_flag=True, help="Enable the profiler.")
@click.version_option(get_versions()["version"])
def main(verbose, debug, profile):
    """
    Start a game using the rootspace game engine.
    Command line parameters take precedence over configuration values.
    """
    # Configure the logging system.
    log_level = get_log_level(verbose, debug)
    warnings.simplefilter("default")
    logging.captureWarnings(True)
    logging_default_handler = logging.StreamHandler()
    logging_default_handler.setLevel(log_level)
    logging_default_formatter = colorlog.ColoredFormatter(
        "{log_color}{levelname:8s}{reset} @{white}{name}{reset}: {log_color}{message}{reset}",
        style="{"
    )
    logging_default_handler.setFormatter(logging_default_formatter)

    # Configure the rootspace logger
    root_logger = logging.getLogger("rootspace")
    root_logger.addHandler(logging_default_handler)
    root_logger.setLevel(log_level)

    # Configure the warnings logger
    py_warnings = logging.getLogger("py.warnings")
    py_warnings.addHandler(logging_default_handler)
    py_warnings.setLevel(log_level)

    # Determine the location of the user home directory and the engine
    user_home = os.path.expanduser("~")
    engine_location = os.path.dirname(os.path.realpath(__file__))

    # Create the project
    config_dir = os.path.join(user_home, ".config", "rootspace")
    resource_path = os.path.join(engine_location, "resources", "rootspace")
    state_path = os.path.join(config_dir, "state-data")
    config_path = os.path.join(config_dir, "config.ini")
    project = RootSpace.create(resource_path, state_path, config_path=config_path, debug=debug)

    # Create the engine instance
    engine = Engine(project, debug)

    # Run the engine instance
    root_logger.debug("Dispatching: {}".format(engine))
    if profile:
        import cProfile
        cProfile.runctx("engine.run()", None, {"engine": engine}, sort="time")
    else:
        engine.run()

    # Kill the logging system
    logging.shutdown()


if __name__ == "__main__":
    main()
