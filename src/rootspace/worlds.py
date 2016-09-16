# -*- coding: utf-8 -*-

import collections

import attr
from attr.validators import instance_of


@attr.s
class World(object):
    """A simple application world.

    Re-implement the sdl2.ext.World to separate rendering from updating.
    Why do this? If you check out the main loop in core.Core, you'll see
    that I use a fixed time-step
    loop that ensures stable regular execution of the physics update,
    even if the rendering step takes long,
    which is the case on slow machines. Thus, I need to keep these two
    steps (update, render) separated.

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
        """
        Gets the systems bound to the world.

        :returns:
        """
        return tuple(self._systems)

    @property
    def component_types(self):
        """
        Gets the supported component types of the world.

        :returns:
        """
        return self._component_types.values()

    def combined_components(self, comp_types):
        """
        Combine the sets of components.

        :param comp_types:
        :return:
        """
        comps = self.components
        key_sets = [set(comps[ctype]) for ctype in comp_types]
        value_sets = [comps[ctype] for ctype in comp_types]
        entities = key_sets[0].intersection(*key_sets[1:])

        for ent_key in entities:
            yield tuple(component[ent_key] for component in value_sets)

    def add_component_type(self, component_type):
        """
        Add a supported component type to the world.

        :param component_type:
        :return:
        """
        if component_type in self._component_types.values():
            return

        self.components[component_type] = dict()
        self._component_types[component_type.__name__.lower()] = component_type

    def delete(self, entity):
        """
        Remove an entity and all its data from the world.

        :param entity:
        :return:
        """
        for comp_set in self.components.values():
            comp_set.pop(entity, None)

        self.entities.discard(entity)

    def get_components(self, comp_type):
        """
        Get all registered components of a specified type.

        :param comp_type:
        :return:
        """
        if comp_type is self.components:
            return self.components[comp_type].values()
        else:
            return []

    def get_entities(self, component):
        """
        Get all registered entities with a particular component.

        :param component:
        :return:
        """
        comp_set = self.components.get(component.__class__, [])
        return [e for e in comp_set if comp_set[e] == component]

    def add_system(self, system):
        """
        Add the specified system to the world.

        :param system:
        :return:
        """
        if self._valid_system(system):
            for component_type in system.component_types:
                if component_type not in self.components:
                    self.add_component_type(component_type)

            self._systems.append(system)
        else:
            raise TypeError("The specified system cannot be used as such.")

    def remove_system(self, system):
        """
        Remove a system from the world.

        :param system:
        :return:
        """
        self._systems.remove(system)

    def update(self, time, delta_time):
        """
        Processes all components within their corresponding systems, except for the render system.

        :param float time:
        :param float delta_time:
        :return:
        """
        for system in self._systems:
            if hasattr(system, "update"):
                if system.is_applicator:
                    comps = self.combined_components(system.component_types)
                    system.update(time, delta_time, self, comps)
                else:
                    for comp_type in system.component_types:
                        system.update(time, delta_time, self, self.components[comp_type].values())

    def render(self):
        """
        Process the components that correspond to the render system.

        :return:
        """
        for system in self._systems:
            if hasattr(system, "render"):
                for comp_type in system.component_types:
                    system.render(self, self.components[comp_type].values())

    def dispatch(self, event):
        """
        Dispatch an SDL2 event.

        :param event:
        :return:
        """
        pass

    def _valid_system(self, system):
        """
        Determine if a supplied system can be used as such.

        :param system:
        :return:
        """
        comp_types = hasattr(system, "component_types") and isinstance(system.component_types, collections.Iterable)
        applicator = hasattr(system, "is_applicator") and isinstance(system.is_applicator, bool)
        update = hasattr(system, "update") and callable(system.update)
        render = hasattr(system, "render") and callable(system.render)

        return comp_types and applicator and (update or render)
