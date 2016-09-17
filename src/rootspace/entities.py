# -*- coding: utf-8 -*-

import inspect
import uuid

import attr
from attr.validators import instance_of

from .worlds import World
from .components import MachineState, NetworkState, FileSystem, TerminalFrameBuffer, TextureSprite


@attr.s
class Entity(object):
    """
    An entity is a container with a unique identifier.
    """
    _world = attr.ib(validator=instance_of(World), hash=False)
    _ident = attr.ib(validator=instance_of(uuid.UUID))

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
    def create(cls, world, **kwargs):
        """
        Create an entity.

        :param world:
        :param kwargs:
        :return:
        """
        ident = uuid.uuid4()

        if len(kwargs) > 0:
            inst = cls(world, ident, **kwargs)
        else:
            inst = cls(world, ident)

        world.add_entity(inst)
        return inst

    def get_component(self, name):
        """
        Return a reference to an attached component.

        :param name:
        :return:
        """
        return self.__getattr__(name)

    def set_component(self, name, value):
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

    def delete_component(self, name):
        comp_type = self._world.component_types.get(name)
        if comp_type is None:
            raise AttributeError("{!r} has no attribute {!r}".format(self, name))

        del self._world.components[comp_type][self]

    def delete(self):
        """
        Removes the entity from the parent world.

        :return:
        """
        self._world.delete_entity(self)

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


@attr.s
class Computer(Entity):
    """
    Define an entity that models a computer.
    """
    machine_state = attr.ib(validator=instance_of(MachineState), hash=False)
    network_state = attr.ib(validator=instance_of(NetworkState), hash=False)
    file_system = attr.ib(validator=instance_of(FileSystem), hash=False)

    @classmethod
    def create(cls, world, **kwargs):
        """
        Create a computer.

        :param world:
        :param kwargs:
        :return:
        """
        return super(Computer, cls).create(
            world=world,
            machine_state=MachineState(),
            network_state=NetworkState(),
            file_system=FileSystem(),
            **kwargs
        )


@attr.s
class LocalComputer(Computer):
    """
    Define an entity that models the local computer.
    """
    sprite = attr.ib(validator=instance_of(TextureSprite), hash=False)
    terminal_frame_buffer = attr.ib(validator=instance_of(TerminalFrameBuffer), hash=False)

    @classmethod
    def create(cls, world, **kwargs):
        """
        Create a local computer.

        :param world:
        :param kwargs:
        :return:
        """
        renderer = kwargs.pop("renderer")
        texture_sprite = TextureSprite.create(
            renderer=renderer,
            width=80,
            height=25
        )

        return super(LocalComputer, cls).create(
            world=world,
            sprite=texture_sprite,
            terminal_frame_buffer=TerminalFrameBuffer(),
            **kwargs
        )
