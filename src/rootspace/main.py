#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os.path
import warnings

import click

from ._version import get_versions
from .core import Engine
from .ebs import Project


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
    # Determine the project location.
    user_home = os.path.expanduser("~")
    project_location = os.path.dirname(os.path.realpath(__file__))
    resource_path = os.path.join(project_location, "resources")

    # Determine the log level.
    log_level = logging.WARN
    if verbose == 1:
        log_level = logging.INFO
    elif verbose == 2:
        log_level = logging.DEBUG
    else:
        click.echo("Only three verbosity levels are understood: 0, 1 and 2.")

    # Configure the logging system.
    root_logger = logging.getLogger("rootspace")
    logging_default_handler = logging.StreamHandler()
    logging_default_formatter = logging.Formatter(
        fmt="[%(name)s:%(levelname)s] %(message)s"
    )
    logging_default_handler.setFormatter(logging_default_formatter)
    root_logger.addHandler(logging_default_handler)
    root_logger.setLevel(log_level)
    warnings.simplefilter("default")
    logging.captureWarnings(True)

    # Create the project
    project = Project.create("rootspace", user_home, resource_path, debug=debug)

    # Create the engine instance
    engine = Engine(project, debug)

    # Run the engine instance
    root_logger.debug("Dispatching: {}".format(engine))
    if profile:
        import cProfile
        cProfile.runctx("engine.run()", None, {"engine": engine}, sort="time")
    else:
        engine.run()


if __name__ == "__main__":
    main()
