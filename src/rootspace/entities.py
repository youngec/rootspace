# -*- coding: utf-8 -*-

import inspect
import uuid

import attr
from attr.validators import instance_of

from .worlds import World


@attr.s
class Entity(object):
    """
    An entity is a container with a unique identifier.
    """
    _world = attr.ib(validator=instance_of(World))
    _ident = attr.ib(default=attr.Factory(uuid.uuid4), validator=instance_of(uuid.UUID))

    @property
    def world(self):
        """
        Return the parent world.

        :return:
        """
        return self._world

    @property
    def ident(self):
        """
        Return the unique identifier of this entity.

        :return:
        """
        return self._ident

    @classmethod
    def create(cls, world):
        """
        Create an entity.

        :param world:
        :return:
        """
        inst = cls(world)
        world.entities.add(inst)
        return inst

    def __hash__(self):
        return hash(self._ident)

    def __getattr__(self, item):
        """
        Allow access to attached component data.

        :param item:
        :return:
        """
        comp_type = self._world.component_types.get(item)
        if comp_type is None:
            raise AttributeError("{!r} has no attribute {!r}".format(self, item))

        return self._world.components[comp_type][self]

    def __setattr__(self, key, value):
        """
        Set data within an attached component.

        :param key:
        :param value:
        :return:
        """
        mro = inspect.getmro(value.__class__)
        if type in mro:
            stop = mro.index(type)
        else:
            stop = mro.index(object)

        mro = mro[0:stop]
        world_comp_types = self._world.component_types
        for class_type in mro:
            if class_type not in world_comp_types:
                self._world.add_componenttype(class_type)
            self._world.components[class_type][self] = value

    def __delattr__(self, item):
        """
        Delete attached component data.

        :param item:
        :return:
        """
        comp_type = self._world.component_types.get(item)
        if comp_type is None:
            raise AttributeError("{!r} has no attribute {!r}".format(self, item))

        del self._world.components[comp_type][self]

    def delete(self):
        """
        Removes the entity from the parent world.

        :return:
        """
        self._world.delete(self)
