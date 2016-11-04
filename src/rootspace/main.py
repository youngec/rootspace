#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import sys
import warnings

import click
import colorlog

from ._version import get_versions
from .core import Engine
from .projects import RootSpace


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
    # Determine the log level.
    if debug:
        log_level = logging.DEBUG
    else:
        if verbose == 0:
            log_level = logging.ERROR
        elif verbose == 1:
            log_level = logging.WARN
        elif verbose == 2:
            log_level = logging.INFO
        elif verbose == 3:
            log_level = logging.DEBUG
        else:
            click.echo("Only four verbosity levels are understood: 0, 1, 2 and 3.")
            log_level = logging.ERROR

    # Configure the logging system.
    root_logger = logging.getLogger("rootspace")
    logging_default_handler = logging.StreamHandler()
    logging_default_handler.setLevel(log_level)
    logging_default_formatter = colorlog.ColoredFormatter(
        "{log_color}{levelname:8s}{reset} @{white}{name}{reset}: {log_color}{message}{reset}",
        style="{"
    )
    logging_default_handler.setFormatter(logging_default_formatter)
    root_logger.addHandler(logging_default_handler)
    root_logger.setLevel(log_level)

    root_logger.debug("Hi there!")
    root_logger.info("Hi there!")
    root_logger.warn("Hi there!")
    root_logger.error("Hi there!")
    root_logger.critical("Hi there!")
    return

    # TODO: Why does captureWarnings suppress warnings?
    # logging.captureWarnings(True)
    warnings.simplefilter("default")

    # Create the project
    user_home = os.path.expanduser("~")
    engine_location = os.path.dirname(os.path.realpath(__file__))
    resource_path = os.path.join(engine_location, "resources", "rootspace")
    config_path = os.path.join(user_home, ".config", "rootspace", "config.ini")
    project = RootSpace.create(resource_path, config_path=config_path, debug=debug)

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
