#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
import logging
import os.path
import re
import uuid
import weakref

import click
import attr

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


def merge_configurations(func_params, config_paths, default_config):
    """
    Merge configurations from configuration files, function parameters and default values.

    :param func_params:
    :param config_paths:
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
                configuration[key] = cfg.getint(value["section"], value["name"], fallback=value["value"])
            elif isinstance(value["value"], float):
                configuration[key] = cfg.getfloat(value["section"], value["name"], fallback=value["value"])
            elif isinstance(value["value"], str):
                configuration[key] = cfg.get(value["section"], value["name"], fallback=value["value"])
            elif isinstance(value["value"], bool):
                configuration[key] = cfg.getboolean(value["section"], value["name"], fallback=value["value"])
            else:
                configuration[key] = value["value"]

    return configuration


def to_ref(value):
    """
    Convert the input value using weakref.ref. This function is idempotent and
    passes None unmodified.

    :param value:
    :return:
    """
    if value is not None:
        return weakref.ref(value)
    elif isinstance(value, weakref.ReferenceType):
        return value
    elif value is None:
        return None
    else:
        raise TypeError("Expected 'value' to be either an object, a ReferenceType or None.")


def to_uuid(value):
    """
    Convert the input to a UUID value. This function is idempotent and passes None unmodified.

    :param value:
    :return:
    """
    if isinstance(value, uuid.UUID):
        return value
    elif isinstance(value, (str, bytes, int)):
        return uuid.UUID(value)
    elif value is None:
        return None
    else:
        raise TypeError("Expected 'value' to be either a UUID, a string or None.")


def get_log_level(verbose, debug):
    """
    Determine the logging level from the verbose and debug flags.

    :param verbose:
    :param debug:
    :return:
    """
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

    return log_level


@attr.s(repr=False, slots=True)
class SubclassValidator(object):
    cls = attr.ib()

    def __call__(self, instance, attribute, value):
        if not issubclass(value, self.cls):
            raise TypeError(
                "'{name}' must be {cls!r} (got {value!r} that is a "
                "{actual!r})."
                .format(name=attribute.name, cls=self.cls,
                        actual=value.__class__, value=value),
                attribute, self.cls, value
            )

    def __repr__(self):
        return (
            "<subclass_of validator for class {cls!r}>"
            .format(cls=self.cls)
        )


def subclass_of(cls):
    """
    Return a validator that evaluates issubclass(.) on
    the supplied attribute. To be used with attrs.

    :param cls:
    :return:
    """
    return SubclassValidator(cls)

