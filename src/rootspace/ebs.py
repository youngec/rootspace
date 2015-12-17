#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import uuid
import inspect
import attr
from attr.validators import instance_of

import sdl2.ext


__docformat__ = 'restructuredtext'


@attr.s
class EventComponent(object):
    """
    EventComponent simply defines a common interface for components that react to events.
    """
    events = attr.ib(default=attr.Factory(dict), validator=instance_of(dict))


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
        pass


@attr.s
class EventDispatcher(System):
    def __init__(self):
        self.component_types = (EventComponent, )

    def _dispatch_event(self, component, event):
        """
        Pass an event to a component. This does not check, whether the component may actually
        handle the event.

        :param component:
        :param event:
        :return:
        """
        component.events[event.type](event)

    def dispatch(self, world, event):
        """
        Pass an event to all relevant objects within the world.

        :param event:
        :return:
        """
        if event is None:
            return

        for ctype in self.componenttypes:
            all_components = world.get_components(ctype)
            relevant_components = [c for c in all_components if event.type in c.events]

            if len(relevant_components) > 0:
                for c in relevant_components:
                    self._dispatch_event(c, event)


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
        return self._component_types.values()

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

    def get_components(self, comp_type):
        if comp_type is self.components:
            return self.components[comp_type].values()
        else:
            return []

    def get_entities(self, component):
        comp_set = self.components.get(component.__class__, [])
        return [e for e in comp_set if comp_set[e] == component]

    def add_system(self, system):
        for class_type in system.component_types:
            if class_type not in self.components:
                self.add_component_type(class_type)

        self._systems.append(system)

    def insert_system(self, index, system):
        for class_type in system.component_types:
            if class_type not in self.components:
                self.add_component_type(class_type)

        self._systems.insert(index, system)

    def remove_system(self, system):
        self._systems.remove(system)

    def update(self, t, dt):
        """
        Processes all components within their corresponding systems, except for the render system.

        :param float t:
        :param float dt:
        :return:
        """
        for system in self._systems:
            if not isinstance(system, sdl2.ext.SpriteRenderSystem):
                if system.is_applicator:
                    comps = self.combined_components(system.component_types)
                    system.update(t, dt, self, comps)
                else:
                    for comp_type in system.component_types:
                        system.update(t, dt, self, self.components[comp_type].values())

    def render(self):
        """
        Process the components that correspond to the render system.

        :return:
        """
        for system in self._systems:
            if isinstance(system, sdl2.ext.SpriteRenderSystem):
                for ctype in system.componenttypes:
                    system.process(self, self.components[ctype].values())


@attr.s
class Entity(object):
    _world = attr.ib(validator=instance_of(World))
    _id = attr.ib(default=attr.Factory(uuid.uuid4), validator=instance_of(uuid.UUID))

    @classmethod
    def create(cls, world, *args, **kwargs):
        inst = cls(world, *args, **kwargs)
        world.entities.add(inst)
        return inst

    def __getattr__(self, item):
        try:
            comp_type = self._world.component_types[item]
        except KeyError:
            raise AttributeError("{!r} has no attribute {!r}".format(self, item))

        return self._world.components[comp_type][self]

    def __setattr__(self, key, value):
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
        try:
            comp_type = self._world.component_types[item]
        except KeyError:
            raise AttributeError("{!r} has no attribute {!r}".format(self, item))

        del self._world.components[comp_type][self]

    def delete(self):
        """Removes the Entity from the world it belongs to."""
        self._world.delete(self)
