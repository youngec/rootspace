#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

import click

from ._version import get_versions
from .core import Loop, Context
from .utilities import get_log_level, configure_logger


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
    project_name = "rootspace"

    # Configure the logging system.
    log_level = get_log_level(verbose, debug)
    log = configure_logger(project_name, log_level, with_warnings=debug)

    # Create the engine instance
    loop = Loop(project_name, Context, debug)

    # Run the engine instance
    log.project.debug("Dispatching: {}".format(loop))
    if profile:
        import cProfile
        cProfile.runctx("loop.run()", None, {"loop": loop}, sort="time")
    else:
        loop.run()

    # Kill the logging system
    logging.shutdown()


if __name__ == "__main__":
    main()
