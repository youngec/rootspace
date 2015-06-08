#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Docstring"""

import sdl2.ext

import engine.components


class EventDispatcher(sdl2.ext.System):
    def __init__(self, world):
        super(EventDispatcher, self).__init__()

        self.componenttypes = (engine.components.EventComponent, )

        self._world = world

    def _dispatch_event(self, component, event):
        """
        Pass an event to a component. This does not check, whether the component may actually
        handle the event.

        :param component:
        :param event:
        :return:
        """

        component.events[event.type](event)

    def dispatch(self, event):
        """
        Pass an event to all relevant objects within the world.

        :param event:
        :return:
        """

        if event is None:
            return

        for ctype in self.componenttypes:
            all_components = self._world.get_components(ctype)
            relevant_components = [c for c in all_components if event.type in c.events]

            if len(relevant_components) > 0:
                for c in relevant_components:
                    self._dispatch_event(c, event)

    def process(self, world, components):
        """
        The EventDispatcher does not implement a process method by default. Manually
        use dispatch to send events to relevant components.

        :param world:
        :param components:
        :return:
        """
        pass
