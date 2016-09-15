#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import configparser
import os.path

from .exceptions import SetupError


__docformat__ = 'restructuredtext'
FIRST_CAP_RE = re.compile(r"(.)([A-Z][a-z]+)")
ALL_CAP_RE = re.compile(r"([a-z0-9])([A-Z])")


def underscore_to_camelcase(name):
    """
    Convert underscored_text to CamelCase text.

    :param str name:
    :return:
    """
    return "".join(x.capitalize() or '_' for x in name.split("_"))


def camelcase_to_underscore(name):
    """
    Convert CamelCase text to underscored_text.

    :param str name:
    :return:
    """
    s1 = FIRST_CAP_RE.sub(r'\1_\2', name)
    return ALL_CAP_RE.sub(r'\1_\2', s1).lower()


def read_configurations(cfg_paths):
    """
    Read the first available configuration file from a list of paths.

    :param cfg_paths:
    :return:
    """
    cfg = None
    for cfg_path in cfg_paths:
        if isinstance(cfg_path, str) and os.path.isfile(cfg_path):
            cfg = configparser.ConfigParser()
            cfg.read(cfg_path, encoding="utf-8")
            break

    return cfg


def merge_configurations(config_paths, func_params, default_config):
    """
    Merge configurations from configuration files, function parameters and default values.

    :param config_paths:
    :param func_params:
    :param default_config:
    :return:
    """
    # Load the appropriate configuration
    cfg = read_configurations(config_paths)
    if cfg is None:
        raise SetupError("No configuration file found. Searched in: {}".format(config_paths))

    # Merge the various modes of configuration,
    # giving method parameters precedence over configuration file parameters.
    configuration = dict()
    for key, value in default_config.items():
        value_type = type(value["value"])
        if key in func_params:
            if isinstance(func_params[key], value_type):
                configuration[key] = func_params[key]
            else:
                raise ValueError("The value for parameter '{}' must be of type '{}'.".format(key, value_type))
        else:
            if isinstance(value["value"], int):
                configuration[key] = cfg.getint(value["section"], value["name"])
            elif isinstance(value["value"], float):
                configuration[key] = cfg.getfloat(value["section"], value["name"])
            elif isinstance(value["value"], str):
                configuration[key] = cfg.get(value["section"], value["name"])
            elif isinstance(value["value"], bool):
                configuration[key] = cfg.getboolean(value["section"], value["name"])
            else:
                configuration[key] = value["value"]

    return configuration
