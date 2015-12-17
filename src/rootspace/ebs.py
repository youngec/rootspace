#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import uuid
import inspect
import attr
from attr.validators import instance_of

import sdl2.ext


__docformat__ = 'restructuredtext'


class Entity(object):
    """A simple object entity.

    An entity is a specific object living in the application world. It
    does not carry any data or application logic, but merely acts as
    identifier label for data that is maintained in the application
    world itself.

    As such, it is an composition of components, which would not exist
    without the entity identifier. The entity itself is non-existent to
    the application world as long as it does not carry any data that can
    be processed by a system within the application world.
    """
    def __new__(cls, world, *args, **kwargs):
        if not isinstance(world, World):
            raise TypeError("world must be a World")
        entity = object.__new__(cls)
        entity._id = uuid.uuid4()
        entity._world = world
        world.entities.add(entity)
        return entity

    def __repr__(self):
        return "Entity(id=%s)" % self._id

    def __hash__(self):
        return hash(self._id)

    def __getattr__(self, name):
        """Gets the component data related to the Entity."""
        if name in ("_id", "_world"):
            return getattr(self, name)
        try:
            ctype = self._world._componenttypes[name]
        except KeyError:
            raise AttributeError("object '%r' has no attribute '%r'" % \
                (self.__class__.__name__, name))
        return self._world.components[ctype][self]

    def __setattr__(self, name, value):
        """Sets the component data related to the Entity."""
        if name in ("_id", "_world"):
            object.__setattr__(self, name, value)
        else:
            # If the value is a compound component (e.g. a Button
            # inheriting from a Sprite), it needs to be added to all
            # supported component type instances.
            mro = inspect.getmro(value.__class__)
            if type in mro:
                stop = mro.index(type)
            else:
                stop = mro.index(object)
            mro = mro[0:stop]
            wctypes = self._world.componenttypes
            for clstype in mro:
                if clstype not in wctypes:
                    self._world.add_componenttype(clstype)
                self._world.components[clstype][self] = value

    def __delattr__(self, name):
        """Deletes the component data related to the Entity."""
        if name in ("_id", "_world"):
            raise AttributeError("'%s' cannot be deleted.", name)
        try:
            ctype = self._world._componenttypes[name]
        except KeyError:
            raise AttributeError("object '%s' has no attribute '%s'" % \
                (self.__class__.__name__, name))
        del self._world.components[ctype][self]

    def delete(self):
        """Removes the Entity from the world it belongs to."""
        self.world.delete(self)

    @property
    def id(self):
        """The id of the Entity."""
        return self._id

    @property
    def world(self):
        """The world the Entity resides in."""
        return self._world


@attr.s
class World(object):
    """A simple application world.

    Re-implement the sdl2.ext.World to separate rendering from updating.
    Why do this? If you check out the main loop in core.Core, you'll see that I use a fixed time-step
    loop that ensures stable regular execution of the physics update, even if the rendering step takes long,
    which is the case on slow machines. Thus, I need to keep these two steps (update, render) separated.

    An application world defines the combination of application data and
    processing logic and how the data will be processed. As such, it is
    a container object in which the application is defined.

    The application world maintains a set of entities and their related
    components as well as a set of systems that process the data of the
    entities. Each processing system within the application world only
    operates on a certain set of components, but not all components of
    an entity at once.

    The order in which data is processed depends on the order of the
    added systems.
    """
    entities = attr.ib(default=attr.Factory(set), validator=instance_of(set))
    components = attr.ib(default=attr.Factory(dict), validator=instance_of(dict))
    _systems = attr.ib(default=attr.Factory(list), validator=instance_of(list))
    _component_types = attr.ib(default=attr.Factory(dict), validator=instance_of(dict))

    @property
    def systems(self):
        """Gets the systems bound to the world."""
        return tuple(self._systems)

    @property
    def component_types(self):
        """Gets the supported component types of the world."""
        return self._componenttypes.values()

    def combined_components(self, comp_types):
        comps = self.components
        key_sets = [set(comps[ctype] for ctype in comp_types)]
        val_sets = [comps[ctype] for ctype in comp_types]
        entities = key_sets[0].intersection(*key_sets[1:])
        for ent_key in entities:
            yield tuple(component[ent_key] for component in val_sets)

    def add_component_type(self, class_type):
        if class_type in self._component_types.values():
            return

        self.components[class_type] = dict()
        self._component_types[class_type.__name__.lower()] = class_type

    def delete(self, entity):
        for comp_set in self.components.values():
            comp_set.pop(entity, None)

        self.entities.discard(entity)

    def delete_entities(self, entities):
        ents = set(entities)

        for comp_key, comp_set in self.components.items():
            keys = set(comp_set.keys()) - ents
            self.components[comp_key] = dict((k, comp_set[k]) for k in keys)

        self.entities -= ents

    # def _system_is_valid(self, system):
    #     """Checks, if the passed object fulfills the requirements for being
    #     a processing system.
    #     """
    #     return hasattr(system, "componenttypes") and \
    #         isiterable(system.componenttypes) and \
    #         hasattr(system, "process") and \
    #         callable(system.process)

    def get_components(self, componenttype):
        """Gets all existing components for a sepcific component type.

        If no components could be found for the passed component types, an
        empty list is returned.
        """
        if componenttype in self.components:
            return self.components[componenttype].values()
        return []

    def get_entities(self, component):
        """Gets the entities using the passed component.

        Note: this will not perform an identity check on the component
        but rely on its __eq__ implementation instead.
        """
        compset = self.components.get(component.__class__, None)
        if compset is None:
            return []
        return [e for e in compset if compset[e] == component]

    def add_system(self, system):
        """Adds a processing system to the world.

        The system will be added as last item in the processing order. Every
        object can be added as long as it contains

           * a 'componenttypes' attribute that is iterable and contains the
            class types to be processed
           * a 'process()' method, receiving two arguments, the world and
             components

        If the object contains a 'is_applicator' attribute that evaluates to
        True, the system will operate on combined sets of components.
        """
        if not self._system_is_valid(system):
            raise ValueError("system must have componenttypes and a process method")
        for classtype in system.componenttypes:
            if classtype not in self.components:
                self.add_componenttype(classtype)
        self._systems.append(system)

    def insert_system(self, index, system):
        """Adds a processing system to the world.

        The system will be added at the specific position of the
        processing order.
        """
        if not self._system_is_valid(system):
            raise ValueError("system must have componenttypes and a process method")
        for classtype in system.componenttypes:
            if classtype not in self.components:
                self.add_componenttype(classtype)
        self._systems.insert(index, system)

    def remove_system(self, system):
        """Removes a processing system from the world."""
        self._systems.remove(system)

    def update(self, t, dt):
        """
        Processes all components within their corresponding systems, except for the render system.

        :param float t:
        :param float dt:
        :return:
        """
        components = self.components
        syst = [sys for sys in self._systems if not isinstance(sys, sdl2.ext.SpriteRenderSystem)]
        for system in syst:
            if system.is_applicator:
                comps = self.combined_components(system.componenttypes)
                system.update(t, dt, self, comps)
            else:
                for ctype in system.componenttypes:
                    system.update(t, dt, self, components[ctype].values())

    def render(self):
        """
        Process the components that correspond to the render system.

        :return:
        """
        components = self.components
        render_systems = [sys for sys in self._systems if isinstance(sys, sdl2.ext.SpriteRenderSystem)]
        for system in render_systems:
            for ctype in system.componenttypes:
                system.process(self, components[ctype].values())


@attr.s
class System(object):
    """
    A processing system for component data.

    A processing system within an application world consumes the
    components of all entities, for which it was set up. At time of
    processing, the system does not know about any other component type
    that might be bound to any entity.

    Also, the processing system does not know about any specific entity,
    but only is aware of the data carried by all entities.
    """
    component_types = attr.ib(default=tuple(), validator=instance_of(tuple))
    is_applicator = attr.ib(default=False, validator=instance_of(bool))

    def update(self, t, dt, world, components):
        """
        Processes component items.

        :param float t:
        :param float dt:
        :param World world:
        :param components:
        :return:
        """
        raise NotImplementedError()
