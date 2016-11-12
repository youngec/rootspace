#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""The engine core holds the entry point into the game execution."""

import abc
import collections
import contextlib
import inspect
import json
import logging
import pathlib
import shutil
import uuid
import weakref

import attr
import glfw
from attr.validators import instance_of

from .exceptions import GLFWError
from .utilities import subclass_of, camelcase_to_underscore


@attr.s
class Entity(object):
    """
    An entity is a container with a unique identifier.
    """
    _ident = attr.ib(validator=instance_of(uuid.UUID))

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
        inst = cls(uuid.uuid4(), **kwargs)
        world.add_entity(inst)

        return inst


@attr.s
class UpdateSystem(object, metaclass=abc.ABCMeta):
    """
    A processing system for component data. Business logic variant.

    A processing system within an application world consumes the
    components of all entities, for which it was set up. At time of
    processing, the system does not know about any other component type
    that might be bound to any entity.

    Also, the processing system does not know about any specific entity,
    but only is aware of the data carried by all entities.
    """
    component_types = attr.ib(validator=instance_of(tuple))
    is_applicator = attr.ib(validator=instance_of(bool))
    _log = attr.ib(validator=instance_of(logging.Logger))

    @abc.abstractmethod
    def update(self, time, delta_time, world, components):
        """
        Update the current world.

        :param float time:
        :param float delta_time:
        :param World world:
        :param components:
        :return:
        """
        pass

    @classmethod
    def get_logger(cls):
        """
        Get the logger that best describes the specified class.

        :return:
        """
        return logging.getLogger("{}.{}".format(__name__, cls.__name__))

    def _dbg(self, message):
        """
        Send a debug message.

        :param message:
        :return:
        """
        self._log.debug(message)

    def _nfo(self, message):
        """
        Send an info message.

        :param message:
        :return:
        """
        self._log.info(message)

    def _wrn(self, message):
        """
        Send a warning message.

        :param message:
        :return:
        """
        self._log.warn(message)


@attr.s
class RenderSystem(object, metaclass=abc.ABCMeta):
    """
    A processing system for component data. Rendering variant.

    A processing system within an application world consumes the
    components of all entities, for which it was set up. At time of
    processing, the system does not know about any other component type
    that might be bound to any entity.

    Also, the processing system does not know about any specific entity,
    but only is aware of the data carried by all entities.
    """
    component_types = attr.ib(validator=instance_of(tuple))
    is_applicator = attr.ib(validator=instance_of(bool))
    sort_func = attr.ib()
    _log = attr.ib(validator=instance_of(logging.Logger))

    @abc.abstractmethod
    def render(self, world, components):
        """
        Render the current world to display.

        :param world:
        :param components:
        :return:
        """
        pass

    @classmethod
    def get_logger(cls):
        """
        Get the logger that best describes the specified class.

        :return:
        """
        return logging.getLogger("{}.{}".format(__name__, cls.__name__))

    def _dbg(self, message):
        """
        Send a debug message.

        :param message:
        :return:
        """
        self._log.debug(message)

    def _nfo(self, message):
        """
        Send an info message.

        :param message:
        :return:
        """
        self._log.info(message)

    def _wrn(self, message):
        """
        Send a warning message.

        :param message:
        :return:
        """
        self._log.warn(message)


@attr.s
class EventSystem(object, metaclass=abc.ABCMeta):
    """
    A processing system for component data. Event variant.

    A processing system within an application world consumes the
    components of all entities, for which it was set up. At time of
    processing, the system does not know about any other component type
    that might be bound to any entity.

    Also, the processing system does not know about any specific entity,
    but only is aware of the data carried by all entities.
    """
    component_types = attr.ib(validator=instance_of(tuple))
    is_applicator = attr.ib(validator=instance_of(bool))
    event_types = attr.ib(validator=instance_of(tuple))
    _log = attr.ib(validator=instance_of(logging.Logger))

    @abc.abstractmethod
    def dispatch(self, event, world, components):
        """
        Dispatch the SDL2 event to the current set of components.

        :param event:
        :param world:
        :param components:
        :return:
        """
        pass

    @classmethod
    def get_logger(cls):
        """
        Get the logger that best describes the specified class.

        :return:
        """
        return logging.getLogger("{}.{}".format(__name__, cls.__name__))

    def _dbg(self, message):
        """
        Send a debug message.

        :param message:
        :return:
        """
        self._log.debug(message)

    def _nfo(self, message):
        """
        Send an info message.

        :param message:
        :return:
        """
        self._log.info(message)

    def _wrn(self, message):
        """
        Send a warning message.

        :param message:
        :return:
        """
        self._log.warn(message)


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
    _ctx = attr.ib(validator=instance_of(weakref.ReferenceType))
    _entities = attr.ib(default=attr.Factory(set), validator=instance_of(set))
    _components = attr.ib(default=attr.Factory(dict), validator=instance_of(dict))
    _systems = attr.ib(default=attr.Factory(list), validator=instance_of(list))
    _update_systems = attr.ib(default=attr.Factory(list), validator=instance_of(list))
    _render_systems = attr.ib(default=attr.Factory(list), validator=instance_of(list))
    _event_systems = attr.ib(default=attr.Factory(list), validator=instance_of(list))
    _component_types = attr.ib(default=attr.Factory(dict), validator=instance_of(dict))
    _log = attr.ib(default=logging.getLogger(__name__), validator=instance_of(logging.Logger), repr=False)

    @classmethod
    def create(cls, ctx):
        """
        Create a World from a given context.

        :param ctx:
        :return:
        """
        ctx = weakref.ref(ctx)
        log = logging.getLogger("{}.{}".format(__name__, cls.__name__))

        return cls(ctx, log=log)

    def combined_components(self, comp_types):
        """
        Combine the sets of components.

        :param comp_types:
        :return:
        """
        comps = self._components
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
        if component_type not in self._component_types.values():
            self._components[component_type] = dict()
            self._component_types[camelcase_to_underscore(component_type.__name__)] = component_type

    def add_component(self, entity, component):
        """
        Add a supported component instance to the world.

        :param entity:
        :param component:
        :return:
        """
        # If the value is a compound component (e.g. a Button
        # inheriting from a Sprite), it needs to be added to all
        # supported component type instances.
        mro = inspect.getmro(component.__class__)
        if type in mro:
            stop = mro.index(type)
        else:
            stop = mro.index(object)

        for comp_type in mro[0:stop]:
            self.add_component_type(comp_type)
            self._components[comp_type][entity] = component

    def add_entity(self, entity):
        """
        Add an entity to the world.

        :param entity:
        :return:
        """
        self._entities.add(entity)

    def delete_entity(self, entity):
        """
        Remove an entity and all its data from the world.

        :param entity:
        :return:
        """
        for comp_set in self._components.values():
            comp_set.pop(entity, None)

        self._entities.discard(entity)

    def get_components(self, comp_type):
        """
        Get all registered components of a specified type.

        :param comp_type:
        :return:
        """
        if comp_type is self._components:
            return self._components[comp_type].values()
        else:
            return []

    def get_entities(self, component):
        """
        Get all registered entities with a particular component.

        :param component:
        :return:
        """
        comp_set = self._components.get(component.__class__, [])
        return [e for e in comp_set if comp_set[e] == component]

    def add_system(self, system):
        """
        Add the specified system to the world.

        :param system:
        :return:
        """
        if self._is_valid_system(system):
            for component_type in system.component_types:
                if component_type not in self._components:
                    self.add_component_type(component_type)

            self._systems.append(system)
            if self._is_update_system(system):
                self._update_systems.append(system)
            elif self._is_render_system(system):
                self._render_systems.append(system)
            elif self._is_event_system(system):
                self._event_systems.append(system)
        else:
            raise TypeError("The specified system cannot be used as such.")

    def remove_system(self, system):
        """
        Remove a system from the world.

        :param system:
        :return:
        """
        self._systems.remove(system)

    def update(self, t, dt):
        """
        Processes all components within their corresponding systems, except for the render system.

        :param float t:
        :param float dt:
        :return:
        """
        for system in self._update_systems:
            if system.is_applicator:
                comps = self.combined_components(system.component_types)
                system.update(t, dt, self, comps)
            else:
                for comp_type in system.component_types:
                    system.update(t, dt, self, self._components[comp_type].values())

    def render(self):
        """
        Process the components that correspond to the render system.

        :return:
        """
        for system in self._render_systems:
            if system.is_applicator:
                comps = self.combined_components(system.component_types)
                system.render(self, comps)
            else:
                for comp_type in system.component_types:
                    system.render(self, self._components[comp_type].values())

    def dispatch(self, event):
        """
        Dispatch an SDL2 event.

        :param event:
        :return:
        """
        for system in self._event_systems:
            if event.type in system.event_types:
                if system.is_applicator:
                    comps = self.combined_components(system.component_types)
                    system.dispatch(event, self, comps)
                else:
                    for comp_type in system.component_types:
                        system.dispatch(event, self, self._components[comp_type].values())

    def _is_update_system(self, system):
        """
        Determine if a supplied system is an update system.

        :param system:
        :return:
        """
        comp_types = hasattr(system, "component_types") and isinstance(system.component_types, collections.Iterable)
        applicator = hasattr(system, "is_applicator") and isinstance(system.is_applicator, bool)
        update = hasattr(system, "update") and callable(system.update)

        return comp_types and applicator and update

    def _is_render_system(self, system):
        """
        Determine if a supplied system is a render system.

        :param system:
        :return:
        """
        comp_types = hasattr(system, "component_types") and isinstance(system.component_types, collections.Iterable)
        applicator = hasattr(system, "is_applicator") and isinstance(system.is_applicator, bool)
        render = hasattr(system, "render") and callable(system.render)

        return comp_types and applicator and render

    def _is_event_system(self, system):
        """
        Determine if a supplied system is an event system.

        :param system:
        :return:
        """
        comp_types = hasattr(system, "component_types") and isinstance(system.component_types, collections.Iterable)
        applicator = hasattr(system, "is_applicator") and isinstance(system.is_applicator, bool)
        event_types = hasattr(system, "event_types") and isinstance(system.event_types, collections.Iterable)
        dispatch = hasattr(system, "dispatch") and callable(system.dispatch)

        return comp_types and applicator and event_types and dispatch

    def _is_valid_system(self, system):
        """
        Determine if a supplied system can be used as such.

        :param system:
        :return:
        """
        return self._is_update_system(system) or self._is_render_system(system) or self._is_event_system(system)


@attr.s
class Context(object):
    """
    The Context is used by the Engine to set the main loop parameters,
    the systems, entities, resources, states, etc.
    """
    Data = collections.namedtuple("Data", (
        "delta_time", "max_frame_duration", "epsilon", "window_title", "window_shape",
        "render_color", "extra"
    ))

    default_ctx = Data(
        delta_time=0.01,
        max_frame_duration=0.25,
        epsilon=1e-5,
        window_title="Untitled",
        window_shape=(800, 600),
        render_color=(0, 0, 0, 1),
        extra=None
    )
    default_config_dir = ".config"
    default_resources_dir = "resources"
    default_config_file = "config.json"

    _name = attr.ib(validator=instance_of(str))
    _resources_root = attr.ib(validator=instance_of(pathlib.Path), repr=False)
    _states_root = attr.ib(validator=instance_of(pathlib.Path), repr=False)
    _data = attr.ib(validator=instance_of(Data), repr=False)
    _window = attr.ib()
    _world = attr.ib(validator=instance_of((type(None), World)))
    _debug = attr.ib(validator=instance_of(bool))
    _log = attr.ib(validator=instance_of(logging.Logger), repr=False)
    _ctx_exit = attr.ib(validator=instance_of((type(None), contextlib.ExitStack)))

    @classmethod
    def create(cls, name, user_home, engine_location, debug=False):
        """
        Create a new project instance.

        :param name:
        :param user_home:
        :param engine_location:
        :param debug:
        :return:
        """
        # Specify the configuration directory and the resources directory
        resources_path = engine_location / cls.default_resources_dir / name
        states_path = user_home / cls.default_config_dir / name

        # Specify the configuration file paths
        config_default = resources_path / cls.default_config_file
        config_user = states_path / cls.default_config_file

        # Ensure that both directories (resources and states) are present
        if not resources_path.exists():
            raise FileNotFoundError(resources_path)
        elif not resources_path.is_dir():
            raise NotADirectoryError(resources_path)

        if not states_path.exists():
            states_path.mkdir(parents=True)

        # Copy the default configuration to the user-specific directory
        if not config_user.exists():
            shutil.copyfile(str(config_default), str(config_user))

        # Load the configuration
        with config_user.open(mode="r") as f:
            ctx = cls.default_ctx._replace(**json.load(f))

        # Create the logger
        log = logging.getLogger("{}.{}".format(__name__, cls.__name__))

        return cls(name, resources_path, states_path, ctx, None, None, debug, log, None)

    @property
    def resources(self):
        """
        Return the path to the resources directory.

        :return:
        """
        return self._resources_root

    @property
    def states(self):
        """
        Return the path to the states directory.

        :return:
        """
        return self._states_root

    @property
    def data(self):
        """
        Return the context data.

        :return:
        """
        return self._data

    @property
    def window(self):
        """
        Return a reference to the Window or None.

        :return:
        """
        return self._window

    @property
    def renderer(self):
        """
        Return a reference to the Renderer or None.

        :return:
        """
        return self._renderer

    @property
    def world(self):
        """
        Return a reference to the World or None.

        :return:
        """
        return self._world

    def _dbg(self, message):
        """
        Send a debug message.

        :param message:
        :return:
        """
        self._log.debug(message)

    def _nfo(self, message):
        """
        Send an info message.

        :param message:
        :return:
        """
        self._log.info(message)

    def _wrn(self, message):
        """
        Send a warning message.

        :param message:
        :return:
        """
        self._log.warn(message)

    def __enter__(self):
        """
        Enter the context provided by this instance.

        :return:
        """
        with contextlib.ExitStack() as ctx_mgr:
            self._nfo("Initializing the context.")

            self._dbg("Initializing GLFW.")
            if not glfw.init():
                raise GLFWError("Cannot initialize GLFW.")
            ctx_mgr.callback(glfw.terminate)

            # Create the Window, Renderer and World
            self._dbg("Creating the window.")
            self._window = glfw.create_window(
                self._data.window_shape[0],
                self._data.window_shape[1],
                self._data.window_title,
                None,
                None
            )
            if not self._window:
                raise GLFWError("Cannot create a GLFW Window.")

            # Make the OpenGL context current
            glfw.make_context_current(self._window)

            # Create the World
            self._dbg("Creating the world.")
            self._world = World.create(self)

            self._ctx_exit = ctx_mgr.pop_all().close

            return self

    def __exit__(self, exc_type, exc_val, trcbak):
        """
        Exit the context provided by this instance.

        :param exc_type:
        :param exc_val:
        :param trcbak:
        :return:
        """
        self._ctx_exit()
        return False


@attr.s
class Loop(object):
    """
    The Loop runs a fixed time step implementation of the main loop.
    """
    _name = attr.ib(validator=instance_of(str))
    _ctx = attr.ib(default=Context, validator=subclass_of(Context), repr=False)
    _debug = attr.ib(default=False, validator=instance_of(bool))
    _log = attr.ib(default=logging.getLogger(__name__), validator=instance_of(logging.Logger), repr=False)

    def run(self):
        """
        Run the main loop.

        :return:
        """
        user_home = pathlib.Path.home()
        engine_location = pathlib.Path(__file__).parent

        self._dbg("The user home is at '{}'.".format(user_home))
        self._dbg("The engine is located at '{}'.".format(engine_location))

        with self._ctx.create(self._name, user_home, engine_location, self._debug) as ctx:
            self._dbg("Entered context {}.".format(ctx))
            self._loop(ctx)

    def _loop(self, ctx):
        """
        Enter the fixed time-step loop of the game.

        The loop makes sure that the physics update is called at regular intervals based on DELTA_TIME
        from generic.py. The renderer is called when enough simulation intervals have accumulated
        to let it take its time even on slow computers without jeopardizing the physics simulation.
        The maximum duration of a frame is set to FRAME_TIME_MAX in generic.py.

        :param ctx:
        :return:
        """
        self._nfo("Executing within the engine context.")

        # Define the time for the event loop
        t = 0.0
        current_time = glfw.get_time()
        accumulator = 0.0

        # Create and run the event loop
        while not glfw.window_should_close(ctx.window):
            # Determine how much time we have to perform the physics
            # simulation.
            new_time = glfw.get_time()
            frame_time = new_time - current_time
            current_time = new_time
            frame_time = min(frame_time, ctx.data.max_frame_duration)
            accumulator += frame_time

            # Run the game update until we have one DELTA_TIME left for the
            # rendering step.
            while accumulator >= ctx.data.delta_time:
                glfw.poll_events()

                ctx.world.update(t, ctx.data.delta_time)
                t += ctx.data.delta_time
                accumulator -= ctx.data.delta_time

            # Clear the screen and render the world.
            ctx.world.render()
            glfw.swap_buffers(ctx.window)

    def _dbg(self, message):
        """
        Send a debug message.

        :param message:
        :return:
        """
        self._log.debug(message)

    def _nfo(self, message):
        """
        Send an info message.

        :param message:
        :return:
        """
        self._log.info(message)

    def _wrn(self, message):
        """
        Send a warning message.

        :param message:
        :return:
        """
        self._log.warn(message)
