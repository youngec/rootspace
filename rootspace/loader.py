#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Create and execute the Core object."""

import configparser
import logging
import os
import warnings

import click

import rootspace.engine.exceptions as exceptions

@click.command()
@click.option("-g", "--game", type=str, default="engine", help="Select the game to play.")
def main(game):
    """
    Enter into the execution of the Core object.

    :return:
    """
    # ---- Where am I? ----
    user_home = os.path.expanduser("~")
    project_location, _ = os.path.split(os.path.abspath(__file__))

    # ---- Load the configuration ----
    config = configparser.ConfigParser()
    config_custom = os.path.join(user_home, "rootspace-config.ini")
    config_default = os.path.join(project_location, "config.ini")
    if os.path.isfile(config_custom):
        config.read(config_custom, encoding="utf-8")
    elif os.path.isfile(config_default):
        config.read(config_default, encoding="utf-8")
    else:
        raise exceptions.SetupError("Could not find the configuration file. You probably didn't install "
                                    "Rootspace correctly.")

    # General settings
    debug = config.getboolean("General", "Debug", fallback=False)
    log_format = config.get("General", "Log format", fallback="%(asctime)s - %(name)s - %(levelname)s: %(message)s")
    date_format = config.get("General", "Date format", fallback="%Y-%m-%dT%H:%M:%S%Z")

    # Loop settings
    delta_time = 1 / config.getfloat("Loop", "Frequency", fallback=100)
    max_frame_duration = config.getfloat("Loop", "Maximum frame duration", fallback=0.25)
    epsilon = config.getfloat("Loop", "Epsilon", fallback=0.00001)

    # Project settings
    window_title = config.get("Project", "Window title", fallback="")
    window_shape = tuple([int(x) for x in config.get("Project", "Window shape", fallback="800, 600").split(",")])
    resource_dir = config.get("Project", "Resource directory", fallback="resources")
    clear_color = tuple([int(x) for x in config.get(
        "Project", "Renderer clear color", fallback="0, 0, 0, 1").split(",")])

    # ---- Configure the logging system ----
    if debug:
        logging.basicConfig(level=logging.DEBUG, format=log_format, datefmt=date_format)
    else:
        logging.basicConfig(level=logging.INFO, format=log_format, datefmt=date_format)
    warnings.simplefilter("default")
    logging.captureWarnings(True)
    log = logging.getLogger(__name__)

    # Create the core instance
    if game == "pong":
        log.info("The pong game was selected.")
        from rootspace.pong.core import PongCore as Core
    elif game == "engine":
        log.info("The engine was selected (no game).")
        from rootspace.engine.core import Core
    else:
        raise ValueError("The selected game is not known.")

    log.info("Building the Core.")
    exc = Core.create_core(project_location, resource_dir, window_title, window_shape, clear_color, delta_time,
                           max_frame_duration, epsilon)

    # Execute the main loop
    log.info("Starting the main loop.")
    try:
        exc.loop()
    finally:
        exc.shutdown()
        log.info("Goodbye.")
        logging.shutdown()


if __name__ == "__main__":
    main()
