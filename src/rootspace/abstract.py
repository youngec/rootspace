#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import weakref
import uuid
import sdl2.ext
import attr
from attr.validators import instance_of

from .util import camelcase_to_underscore


@attr.s
class Component(object):
    pass


@attr.s
class Entity(object):
    _id = attr.ib(validator=instance_of(uuid.UUID))

    @classmethod
    def create(cls, *args, **kwargs):
        unique_id = uuid.uuid4()
        return cls(unique_id, *args, **kwargs)


@attr.s
class System(object):
    is_applicator = attr.ib(validator=instance_of(bool))
    component_types = attr.ib(validator=instance_of(tuple))

    def update(self, world, components, time, delta_time):
        raise NotImplementedError()


@attr.s
class World(object):
    systems = attr.ib(validator=instance_of(list))
    entities = attr.ib()
    components = attr.ib()

    def update(self, time, delta_time):
        for system in self.systems:
            if system.is_applicator:
                components = self._combined_components(system.component_types)
                system.update(self, components, time, delta_time)
            else:
                for comp_type in system.component_types:
                    components = self.components[comp_type]
                    system.update(self, components, time, delta_time)

    def _combined_components(self, component_types):
        return []