#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
import importlib
import logging
import os

import click

from ._version import get_versions
from .core import Core
from .exceptions import SetupError
from .util import underscore_to_camelcase

__docformat__ = 'restructuredtext'


@click.command(help="Run Rootspace")
@click.argument("game", type=str, default="")
@click.option("--debug", is_flag=True, help="Enable debug mode.")
@click.option("--verbose", is_flag=True, help="Enable verbose output.")
@click.version_option(version=get_versions()["version"])
@click.pass_context
def main(context, game, debug, verbose):
    """
    Enter into the execution of the Core object.

    :param click.Context context:
    :param str game:
    :param bool debug:
    :param bool verbose:
    :return:
    """
    # Where am I?
    user_home = os.path.expanduser("~")
    current_working_dir = os.getcwd()
    project_location, _ = os.path.split(os.path.abspath(__file__))

    rs_logger = logging.getLogger("rootspace")
    if debug:
        rs_logger.setLevel(logging.DEBUG)
    elif verbose:
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
    debug = debug or config.getboolean("General", "Debug", fallback=False)
    verbose = verbose or config.getboolean("General", "Verbose", fallback=False)
    delta_time = 1 / config.getfloat("Loop", "Frequency", fallback=100)
    max_frame_duration = config.getfloat("Loop", "Maximum frame duration", fallback=0.25)
    epsilon = config.getfloat("Loop", "Epsilon", fallback=0.00001)
    project_name = game if len(game) > 0 else config.get("Project", "Name", fallback="pong")
    window_title = config.get("Project", "Window title", fallback="")
    window_shape = tuple(int(x) for x in config.get("Project", "Window shape", fallback="800 600").split(" "))
    resource_dir = config.get("Project", "Resource directory", fallback="resources")
    clear_color = tuple(int(x) for x in config.get("Project", "Renderer clear color", fallback="0 0 0 1").split(" "))
    context.obj = dict(
        debug=debug,
        verbose=verbose,
        project_location=project_location,
        user_home=user_home,
        current_working_dir=current_working_dir,
        delta_time=delta_time,
        max_frame_duration=max_frame_duration,
        epsilon=epsilon,
        project_name=project_name,
        window_title=window_title,
        window_shape=window_shape,
        resource_dir=resource_dir,
        clear_color=clear_color
    )

    try:
        project_core_module = importlib.import_module("rootspace.{}.core".format(project_name))
        print(dir(project_core_module))
        project_class = getattr(project_core_module, underscore_to_camelcase(project_name))

        # Create the core instance
        exc = Core.create(project_class, context.obj["project_location"], context.obj["resource_dir"],
                          context.obj["window_title"], context.obj["window_shape"], context.obj["clear_color"],
                          context.obj["delta_time"], context.obj["max_frame_duration"], context.obj["epsilon"])

        # Execute the main loop
        try:
            exc.loop()
        finally:
            exc.shutdown()
    except ImportError:
        if debug:
            rs_logger.exception("Could not find the selected project")
        else:
            rs_logger.error("Could not find the selected project.")
