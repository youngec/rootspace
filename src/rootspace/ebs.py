# -*- coding: utf-8 -*-

import inspect
import os.path
import uuid

import attr
import sdl2.ext
import sdl2.video
from attr.validators import instance_of

from .util import merge_configurations

__docformat__ = 'restructuredtext'


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
    component_types = attr.ib(validator=instance_of(tuple))
    is_applicator = attr.ib(validator=instance_of(bool))

    def update(self, time, delta_time, world, components):
        """
        Processes component items.

        :param float time:
        :param float delta_time:
        :param World world:
        :param components:
        :return:
        """
        raise NotImplementedError()


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
        if isinstance(system, (System, sdl2.ext.SpriteRenderSystem)):
            for component_type in system.component_types:
                if component_type not in self.components:
                    self.add_component_type(component_type)

            self._systems.append(system)
        else:
            raise TypeError("The specified system must be an instance of System.")

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
            if not isinstance(system, sdl2.ext.TextureSpriteRenderSystem):
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
            if isinstance(system, sdl2.ext.TextureSpriteRenderSystem):
                for ctype in system.componenttypes:
                    system.process(self, self.components[ctype].values())


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


@attr.s
class Project(object):
    _name = attr.ib(validator=instance_of(str))
    _configuration = attr.ib(validator=instance_of(dict))
    _debug = attr.ib(validator=instance_of(bool))

    _default_config = {
        "delta_time": {
            "value": 0.01,
            "section": "Loop",
            "name": "Delta time"
        },
        "max_frame_duration": {
            "value": 0.25,
            "section": "Loop",
            "name": "Maximum frame duration"
        },
        "epsilon": {
            "value": 1e-5,
            "section": "Loop",
            "name": "Epsilon"
        },
        "window_title": {
            "value": "",
            "section": "Display",
            "name": "Window title"
        },
        "window_shape": {
            "value": (800, 600),
            "section": "Display",
            "name": "Window shape"
        },
        "window_width": {
            "value": 800,
            "section": "Display",
            "name": "Window width"
        },
        "window_height": {
            "value": 600,
            "section": "Display",
            "name": "Window height",
        },
        "window_flags": {
            "value": sdl2.video.SDL_WINDOW_SHOWN | sdl2.video.SDL_WINDOW_RESIZABLE,
            "section": "Display",
            "name": "Window flags"
        },
        "render_scale_quality": {
            "value": b"0",
            "section": "Display",
            "name": "Render scale quality"
        },
        "render_color": {
            "value": (0, 0, 0, 1),
            "section": "Display",
            "name": "Render clear color"
        }
    }

    @property
    def name(self):
        return self._name

    @property
    def configuration(self):
        return self._configuration

    @classmethod
    def create(cls, name, user_home, resource_path, config_path="", debug=False, **kwargs):
        # Define configuration search paths (giving precedence to user configurations)
        cfg_paths = (
            config_path,
            os.path.join(user_home, ".config", name, "config.ini"),
            os.path.join(resource_path, name, "config.ini")
        )

        # Load the conglomerate configuration
        configuration = merge_configurations(cfg_paths, kwargs, cls._default_config)
        configuration["resource_path"] = resource_path

        return cls(name, configuration, debug)

    def create_systems(self):
        return dict()

    def create_entities(self):
        return list()
