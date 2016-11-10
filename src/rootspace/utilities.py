#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import collections
import logging
import re
import uuid
import weakref
import warnings

import click
import attr
import colorlog


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


def configure_logger(name, log_level, with_warnings=True):
    """
    Configure the project logger of the specified name
    using colorlog.

    :param name:
    :param log_level:
    :param with_warnings:
    :return:
    """
    logging_default_handler = logging.StreamHandler()
    logging_default_handler.setLevel(log_level)
    logging_default_formatter = colorlog.ColoredFormatter(
        "{log_color}{levelname:8s}{reset} @{white}{name}{reset}: {log_color}{message}{reset}",
        style="{"
    )
    logging_default_handler.setFormatter(logging_default_formatter)

    # Configure the rootspace logger
    project_logger = logging.getLogger(name)
    project_logger.addHandler(logging_default_handler)
    project_logger.setLevel(log_level)

    py_warnings = None
    if with_warnings:
        # Configure the warnings logger
        warnings.simplefilter("default")
        logging.captureWarnings(True)
        py_warnings = logging.getLogger("py.warnings")
        py_warnings.addHandler(logging_default_handler)
        py_warnings.setLevel(log_level)

    loggers = collections.namedtuple("loggers", ("project", "py_warnings"))
    return loggers(project_logger, py_warnings)


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

