# -*- coding: utf-8 -*-

import inspect
import uuid

import attr
import sdl2.render
from attr.validators import instance_of

from .components import MachineState, NetworkState, FileSystemState, DisplayBuffer, Sprite
from .worlds import World


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
        inst = cls(world, uuid.uuid4(), **kwargs)
        world.add_entity(inst)

        return inst

    def register_component(self, instance):
        """
        Register a component with the world.

        :param instance:
        :return:
        """
        # If the value is a compound component (e.g. a Button
        # inheriting from a Sprite), it needs to be added to all
        # supported component type instances.
        mro = inspect.getmro(instance.__class__)
        if type in mro:
            stop = mro.index(type)
        else:
            stop = mro.index(object)

        for comp_type in mro[0:stop]:
            if comp_type not in self._world.component_types:
                self._world.add_component_type(comp_type)
            self._world.components[comp_type][self] = instance

    def get_component(self, name):
        """
        Get a reference to a registered component.

        :param name:
        :return:
        """
        comp_type = self._world.component_types.get(name)
        if comp_type is None:
            raise AttributeError("{!r} has no attribute {!r}".format(self, name))

        return self._world.components[comp_type][self]

    def delete(self):
        """
        Removes the entity from the parent world.

        :return:
        """
        self._world.delete_entity(self)


@attr.s
class Computer(Entity):
    """
    Define an entity that models a computer.
    """
    machine_state = attr.ib(validator=instance_of(MachineState), hash=False)
    network_state = attr.ib(validator=instance_of(NetworkState), hash=False)
    file_system_state = attr.ib(validator=instance_of(FileSystemState), hash=False)

    @classmethod
    def create(cls, world, **kwargs):
        """
        Create a computer.

        :param world:
        :param kwargs:
        :return:
        """
        inst = super(Computer, cls).create(
            world=world,
            machine_state=MachineState(),
            network_state=NetworkState(),
            file_system_state=FileSystemState(),
            **kwargs
        )

        # Register the components
        inst.register_component(inst.machine_state)
        inst.register_component(inst.network_state)
        inst.register_component(inst.file_system_state)

        return inst


@attr.s
class LocalComputer(Computer):
    """
    Define an entity that models the local computer.
    """
    sprite = attr.ib(validator=instance_of(Sprite), hash=False)
    terminal_display_buffer = attr.ib(validator=instance_of(DisplayBuffer), hash=False)

    @classmethod
    def create(cls, world, **kwargs):
        """
        Create a local computer.

        :param world:
        :param kwargs:
        :return:
        """
        position = (0, 0)
        display_shape = (700, 500)
        text_matrix_shape = (10, 10)
        args = {k: kwargs.pop(k) for k in ("depth", "renderer", "pixel_format", "bpp", "masks") if
                k in kwargs}

        inst = super(LocalComputer, cls).create(
            world=world,
            sprite=Sprite.create(position, display_shape, access=sdl2.render.SDL_TEXTUREACCESS_TARGET, **args),
            terminal_display_buffer=DisplayBuffer.create(text_matrix_shape),
            **kwargs
        )

        # Register the components
        inst.register_component(inst.sprite)
        inst.register_component(inst.terminal_display_buffer)
