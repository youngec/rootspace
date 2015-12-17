#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

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
