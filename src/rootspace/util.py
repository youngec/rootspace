#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__docformat__ = 'restructuredtext'


def underscore_to_camelcase(text):
    """
    Convert underscored_text to CamelCase text.

    :param str text:
    :return:
    """
    return "".join(x.capitalize() or '_' for x in text.split("_"))
