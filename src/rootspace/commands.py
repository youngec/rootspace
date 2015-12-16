#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
import logging
import os

import click

from ._version import get_versions
from .core import Core
from .exceptions import SetupError

__docformat__ = 'restructuredtext'


@click.command(help="Run Rootspace")
@click.option("--debug", is_flag=True, help="Enable debug mode.")
@click.option("--verbose", is_flag=True, help="Enable verbose output.")
@click.version_option(version=get_versions()["version"])
@click.pass_context
def main(context, debug, verbose):
    """
    Enter into the execution of the Core object.

    :return:
    """
    # Where am I?
    user_home = os.path.expanduser("~")
    current_working_dir = os.getcwd()
    project_location, _ = os.path.split(os.path.abspath(__file__))

    if debug:
        rs_logger = logging.getLogger("rootspace")
        rs_logger.setLevel(logging.DEBUG)
    elif verbose:
        rs_logger = logging.getLogger("rootspace")
        rs_logger.setLevel(logging.INFO)

    # ---- Load the configuration ----
    config = configparser.ConfigParser()
    config_custom = os.path.join(user_home, "rootspace-config.ini")
    config_default = os.path.join(project_location, "config.ini")
    if os.path.isfile(config_custom):
        config.read(config_custom, encoding="utf-8")
    elif os.path.isfile(config_default):
        config.read(config_default, encoding="utf-8")
    else:
        raise SetupError("Could not find the configuration file. You probably didn't install Rootspace correctly.")

    # Store the configuration within the application context
    context.obj = dict(
        debug=debug,
        verbose=verbose,
        project_location=project_location,
        user_home=user_home,
        current_working_dir=current_working_dir,
        delta_time=1 / config.getfloat("Loop", "Frequency", fallback=100),
        max_frame_duration=config.getfloat("Loop", "Maximum frame duration", fallback=0.25),
        epsilon=config.getfloat("Loop", "Epsilon", fallback=0.00001),
        window_title=config.get("Project", "Window title", fallback=""),
        window_shape=tuple(int(x) for x in config.get("Project", "Window shape", fallback="800 600").split(" ")),
        resource_dir=config.get("Project", "Resource directory", fallback="resources"),
        clear_color=tuple(int(x) for x in config.get("Project", "Renderer clear color", fallback="0 0 0 1").split(" "))
    )

    # Create the core instance
    exc = Core.create(context.obj["project_location"], context.obj["resource_dir"], context.obj["window_title"],
                      context.obj["window_shape"], context.obj["clear_color"], context.obj["delta_time"],
                      context.obj["max_frame_duration"], context.obj["epsilon"])

    # Execute the main loop
    try:
        exc.loop()
    finally:
        exc.shutdown()
