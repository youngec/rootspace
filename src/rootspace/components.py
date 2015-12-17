#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Collection of components in an Entity-Component-System architecture."""

import attr
from attr.validators import instance_of


@attr.s
class EventComponent(object):
    """
    EventComponent simply defines a common interface for components that react to events.
    """
    events = attr.ib(default=attr.Factory(dict), validator=instance_of(dict))
