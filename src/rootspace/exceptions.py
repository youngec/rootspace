#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A collection of exceptions used by Rootspace.
"""


class SetupError(Exception):
    """
    This exception indicates that the project was installed incorrectly.
    """
    pass


class NotImplementedWarning(UserWarning):
    pass
