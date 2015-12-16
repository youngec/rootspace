#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Collection of components in an Entity-Component-System architecture."""


class EventComponent(object):
    """
    EventComponent simply defines a common interface for components that react to events.
    """

    def __init__(self):
        self.events = dict()
