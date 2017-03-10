#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module starts the rootspace program.
It provides a simple command line interface.
"""

import logging
import argparse

from ._version import get_versions
from .core import Loop, Context
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
        action="store_true",
        help="display the version and exit"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="count",
        help="increase the level of output"
    )
    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        help="enable debug features"
    )
    parser.add_argument(
        "-p", "--profile",
        action="store_true",
        help="enable the profiler"
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

    if args.version:
        print("{}, version {}".format(project_name, get_versions()["version"]))
    else:
        # Configure the logging system.
        log_level = get_log_level(args.verbose, args.debug)
        log = configure_logger(
            project_name, log_level,
            log_path=args.log_file, with_warnings=args.debug
        )

        # Create the engine instance
        loop = Loop(project_name, Context, args.initialize, args.debug)

        # Run the engine instance
        log.project.debug("Dispatching: {}".format(loop))
        if args.profile:
            import cProfile
            cProfile.runctx("loop.run()", globals(), locals())
        else:
            loop.run()

        # Kill the logging system
        logging.shutdown()


if __name__ == "__main__":
    main()
