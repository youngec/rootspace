#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module starts the rootspace program.
It provides a simple command line interface.
"""

import logging
import argparse
import pathlib

from ._version import get_versions
from .orchestrator import Orchestrator
from .utilities import get_log_level, configure_logger


def main() -> None:
    """
    Start a game using the rootspace game engine.
    Command line parameters take precedence over configuration values.
    """
    project_name = "rootspace"

    parser = argparse.ArgumentParser(
        prog=project_name,
        description="Start a game using the rootspace game engine."
    )
    parser.add_argument(
        "-V", "--version",
        action="version",
        version="{} {}".format(project_name, get_versions()["version"]),
        help="display the version and exit"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="count",
        default=0,
        help="increase the level of output"
    )
    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        help="enable debug features"
    )
    parser.add_argument(
        "-i", "--initialize",
        action="store_true",
        help="overwrite all user configuration"
    )
    parser.add_argument(
        "-l", "--log-file",
        type=str,
        help="output the log to the specified file"
    )
    args = parser.parse_args()

    # Configure the logging system.
    log_level = get_log_level(args.verbose)
    log = configure_logger(
        project_name, log_level,
        log_path=args.log_file, with_warnings=args.debug
    )

    # Locate the user home directory and the engine directory tree.
    user_home = pathlib.Path.home()
    log.project.debug("User home identified as: '{}'".format(user_home))
    engine_location = pathlib.Path(__file__).parent
    log.project.debug("Engine location identified as: '{}'".format(engine_location))

    # Create the engine instance
    log.project.info("Creating the orchestrator.")
    orchestrator = Orchestrator.new(project_name, user_home, engine_location, args.initialize, args.debug)

    # Run the engine instance
    log.project.info("Entering main loop.")
    orchestrator.run()

    # Kill the logging system
    logging.shutdown()


if __name__ == "__main__":
    main()
