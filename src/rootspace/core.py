#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""The engine core holds the entry point into the game execution."""

import contextlib
import logging
import pathlib
import shutil
import weakref
import collections
import os
import warnings

import OpenGL.GL as gl
import attr
import glfw
from attr.validators import instance_of

from .systems import SystemMeta, UpdateSystem, RenderSystem, EventSystem
from .entities import EntityMeta, Camera
from .components import ComponentMeta
from .events import KeyEvent, CharEvent, CursorEvent, SceneEvent
from .exceptions import GLFWError, FixmeWarning
from .utilities import subclass_of
from .data_abstractions import KeyMap, ContextData, Scene


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
    _ctx = attr.ib(validator=instance_of(weakref.ReferenceType), repr=False)
    _entities = attr.ib(default=attr.Factory(set), validator=instance_of(set))
    _components = attr.ib(default=attr.Factory(dict), validator=instance_of(dict), repr=False)
    _update_systems = attr.ib(default=attr.Factory(list), validator=instance_of(list))
    _render_systems = attr.ib(default=attr.Factory(list), validator=instance_of(list))
    _event_systems = attr.ib(default=attr.Factory(list), validator=instance_of(list))
    _event_queue = attr.ib(default=attr.Factory(collections.deque), validator=instance_of(collections.deque))
    _scene = attr.ib(default=None, validator=instance_of((type(None), Scene)))
    _log = attr.ib(default=logging.getLogger(__name__), validator=instance_of(logging.Logger), repr=False)

    @property
    def ctx(self):
        return self._ctx()

    @property
    def systems(self):
        return self._update_systems + self._render_systems + self._event_systems

    @property
    def scene(self):
        return self._scene

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

    def _combined_components(self, comp_types):
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

    def _add_component(self, entity, component):
        """
        Add a supported component instance to the world.

        :param entity:
        :param component:
        :return:
        """
        comp_type = type(component)
        if comp_type not in self._components:
            self._components[comp_type] = dict()
        self._components[type(component)][entity] = component

    def _add_components(self, entity):
        """
        Register all components of an entity.

        :param entity:
        :return:
        """
        for c in entity.components:
            self._add_component(entity, c)

    def _remove_component(self, entity, component):
        """
        Remove the component instance from the world.

        :param entity:
        :param component:
        :return:
        """
        comp_type = type(component)
        self._components[comp_type].pop(entity)
        if len(self._components[comp_type]) == 0:
            self._components.pop(comp_type)

    def _remove_components(self, entity):
        """
        Remove the registered components of an entity.

        :param entity:
        :return:
        """
        for c in entity.components:
            self._remove_component(entity, c)

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

    def get_entities_by_component(self, component):
        """
        Get all registered entities with a particular component.

        :param component:
        :return:
        """
        comp_set = self._components.get(component.__class__, [])
        return (e for e in comp_set if comp_set[e] == component)

    def get_entities(self, entity_type):
        """
        Get all Entities of the specified class.

        :param entity_type:
        :return:
        """
        return (e for e in self._entities if isinstance(e, entity_type))

    def get_systems(self, system_type):
        """
        Get all Systems of the specified class.

        :param system_type:
        :return:
        """
        return (e for e in self.systems if isinstance(e, system_type))

    def add_entity(self, entity):
        """
        Add an entity to the world.

        :param entity:
        :return:
        """
        self._add_components(entity)
        self._entities.add(entity)

    def add_entities(self, *entities):
        """
        Add multiple entities to the world.

        :param entities:
        :return:
        """
        for entity in entities:
            self.add_entity(entity)

    def set_entities(self, *entities):
        """
        Replace the current entities with the given ones.

        :param entities:
        :return:
        """
        for_removal = [e for e in self._entities if e not in entities]
        for_addition = [e for e in entities if e not in self._entities]
        self.remove_entities(*for_removal)
        self.add_entities(*for_addition)

    def remove_entity(self, entity):
        """
        Remove an entity and all its data from the world.

        :param entity:
        :return:
        """
        self._remove_components(entity)
        self._entities.discard(entity)

    def remove_entities(self, *entities):
        """
        Remove the specified Entities fomr the World.

        :param entities:
        :return:
        """
        for entity in entities:
            self.remove_entity(entity)

    def remove_all_entities(self):
        """
        Remove all registered Entities.

        :return:
        """
        self._log.debug("Removing all Entities from this World.")
        self._entities.clear()

    def add_system(self, system):
        """
        Add the specified system to the world.

        :param system:
        :return:
        """
        if system not in self.systems:
            self._log.debug("Adding System '{}'.".format(system))
            if isinstance(system, UpdateSystem):
                self._update_systems.append(system)
            elif isinstance(system, RenderSystem):
                self._render_systems.append(system)
            elif isinstance(system, EventSystem):
                self._event_systems.append(system)
            else:
                raise TypeError("The specified system cannot be used as such.")
        else:
            raise ValueError("You cannot add multiple instances of a particular systme class.")

    def add_systems(self, *systems):
        """
        Add multiple systems to the world.

        :param systems:
        :return:
        """
        for system in systems:
            self.add_system(system)

    def set_systems(self, *systems):
        """
        Replace the registered Systems with the specified.

        :param systems:
        :return:
        """
        for_removal = [s for s in self.systems if s not in systems]
        for_addition = [s for s in systems if s not in self.systems]
        self.remove_systems(*for_removal)
        self.add_systems(*for_addition)

    def remove_system(self, system):
        """
        Remove a system from the world.

        :param system:
        :return:
        """
        if system in self._update_systems:
            self._update_systems.remove(system)
        elif system in self._render_systems:
            self._render_systems.remove(system)
        elif system in self._event_systems:
            self._event_systems.remove(system)

    def remove_systems(self, *systems):
        """
        Remove the specified Systems.

        :param systems:
        :return:
        """
        for system in systems:
            self.remove_system(system)

    def remove_all_systems(self):
        """
        Remove all systems.

        :return:
        """
        self._log.debug("Removing all Systems from this World.")
        self._update_systems.clear()
        self._render_systems.clear()
        self._event_systems.clear()

    def update(self, t, dt):
        """
        Processes all components within their corresponding systems, except for the render system.

        :param float t:
        :param float dt:
        :return:
        """
        for system in self._update_systems:
            if system.is_applicator:
                comps = self._combined_components(system.component_types)
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
                comps = self._combined_components(system.component_types)
                system.render(self, comps)
            else:
                for comp_type in system.component_types:
                    system.render(self, self._components[comp_type].values())

    def dispatch(self, event):
        """
        Add an event to the queue.

        :param event:
        :return:
        """
        self._event_queue.append(event)

    def process(self):
        """
        Process all events.

        :return:
        """
        while len(self._event_queue) > 0:
            event = self._event_queue.popleft()
            if isinstance(event, SceneEvent):
                self._update_scene(event)
            else:
                for system in self._event_systems:
                    if isinstance(event, system.event_types):
                        if system.is_applicator:
                            comps = self._combined_components(system.component_types)
                            system.process(event, self, comps)
                        else:
                            for comp_type in system.component_types:
                                system.process(event, self, self._components[comp_type].values())

    def register_callbacks(self, window):
        """
        Register the GLFW callbacks with the specified window.

        :param window:
        :return:
        """
        self._log.debug("Registering GLFW event callbacks with World.")
        glfw.set_window_size_callback(window, self.callback_resize)
        glfw.set_key_callback(window, self.callback_key)
        glfw.set_cursor_pos_callback(window, self.callback_cursor)

    def unregister_callbacks(self, window):
        """
        Clear the GLFW callbacks for the specified window.

        :param window:
        :return:
        """
        self._log.debug("Clearing GLFW event callbacks.")
        glfw.set_window_size_callback(window, None)
        glfw.set_key_callback(window, None)
        glfw.set_cursor_pos_callback(window, None)

    def callback_resize(self, window, width, height):
        for camera in self.get_entities(Camera):
            camera.shape = (width, height)

        gl.glViewport(0, 0, width, height)

    def callback_key(self, window, key, scancode, action, mode):
        """
        Dispatch a Key press event, as sent by GLFW.

        :param window:
        :param key:
        :param scancode:
        :param action:
        :param mode:
        :return:
        """
        self.dispatch(KeyEvent(window, key, scancode, action, mode))

    def callback_char(self, window, codepoint):
        """
        Dispatch a Character entry event, as sent by GLFW.

        :param window:
        :param codepoint:
        :return:
        """
        self.dispatch(CharEvent(window, codepoint))

    def callback_cursor(self, window, xpos, ypos):
        """
        Dispatch a cursor movement event, as sent by GLFW.

        :param window:
        :param xpos:
        :param ypos:
        :return:
        """
        self.dispatch(CursorEvent(window, xpos, ypos))

    def _update_scene(self, event):
        """

        :param event:
        :return:
        """
        # Create the new scene
        scene_path = self.ctx.resources / self.ctx.data.default_scenes_dir / event.name
        new_scene = Scene.from_json(scene_path)

        # Update the OpenGL context according to the scene data
        self._update_context(self._scene, new_scene)

        # Update the world according to the scene data
        self._update_world(self._scene, new_scene)

        # Set the new scene as current
        self._scene = new_scene

    def _update_context(self, old_scene, new_scene):
        """
        Update the GLFW and OpenGL context according to the Scene change.

        :param old_scene:
        :param new_scene:
        :return:
        """
        # Set the cursor behavior
        if not self.ctx.debug:
            glfw.set_input_mode(self.ctx.window, glfw.CURSOR, new_scene.cursor_mode)
            glfw.set_cursor_pos(self.ctx.window, *new_scene.cursor_origin)

        # Enable the OpenGL depth buffer
        if new_scene.enable_depth_test:
            gl.glEnable(gl.GL_DEPTH_TEST)
            gl.glDepthFunc(new_scene.depth_function)
        else:
            gl.glDisable(gl.GL_DEPTH_TEST)

        # Enable OpenGL face culling
        if new_scene.enable_face_culling:
            gl.glEnable(gl.GL_CULL_FACE)
            gl.glFrontFace(new_scene.front_face)
            gl.glCullFace(new_scene.cull_face)
        else:
            gl.glDisable(gl.GL_CULL_FACE)

    def _load_objects(self, scene, object_tree, class_registry, reference_tree=None):
        """
        Load all objects from a given serialization dictionary. You must provide a reference to the World,
        the soon-to-be active Scene, a class registry. Optionally, you may provide a reference dictionary to provide
        additional lookup for serialized object references within the Scene.

        :param scene:
        :param object_tree:
        :param class_registry:
        :param reference_tree:
        :return:
        """
        warnings.warn("Loading objects is terribly ugly.", FixmeWarning)
        if isinstance(object_tree, dict):
            objects = dict()
            for k, v in object_tree.items():
                cls = class_registry[v["class"]]
                kwargs = dict()
                for name, arg in v["kwargs"].items():
                    if isinstance(arg, str):
                        if arg in scene:
                            kwargs[name] = scene[arg]
                        elif arg in self.ctx.data:
                            kwargs[name] = self.ctx.data[arg]
                        elif reference_tree is not None and arg in reference_tree:
                            kwargs[name] = reference_tree[arg]
                        elif any(p in arg for p in (os.path.sep, "/", "\\")):
                            kwargs[name] = self.ctx.resources / arg
                        else:
                            kwargs[name] = arg
                    else:
                        kwargs[name] = arg

                if hasattr(cls, "create"):
                    objects[k] = cls.create(**kwargs)
                else:
                    objects[k] = cls(**kwargs)
        else:
            objects = list()
            for v in object_tree:
                cls = class_registry[v["class"]]
                kwargs = dict()
                for name, arg in v["kwargs"].items():
                    if isinstance(arg, str):
                        if arg in scene:
                            kwargs[name] = scene[arg]
                        elif arg in self.ctx.data:
                            kwargs[name] = self.ctx.data[arg]
                        elif reference_tree is not None and arg in reference_tree:
                            kwargs[name] = reference_tree[arg]
                        elif any(p in arg for p in (os.path.sep, "/", "\\")):
                            kwargs[name] = self.ctx.resources / arg
                        else:
                            kwargs[name] = arg
                    else:
                        kwargs[name] = arg

                if hasattr(cls, "create"):
                    objects.append(cls.create(**kwargs))
                else:
                    objects.append(cls(**kwargs))

        return objects

    def _update_world(self, old_scene, new_scene):
        """
        Update the World according to the Scene change.

        :param old_scene:
        :param new_scene:
        :return:
        """
        # Load the components into memory
        components = self._load_objects(
            new_scene,
            new_scene.components,
            ComponentMeta.classes
        )

        # Load the entities into memory
        entities = self._load_objects(
            new_scene,
            new_scene.entities,
            EntityMeta.classes,
            components
        )

        # Load the systems into memory
        systems = self._load_objects(
            new_scene,
            new_scene.systems,
            SystemMeta.classes
        )

        self.set_entities(*entities.values())
        self.set_systems(*systems)


@attr.s
class Context(object):
    """
    The Context is used by the Engine to set the main loop parameters,
    the systems, entities, resources, states, etc.
    """
    _name = attr.ib(validator=instance_of(str))
    _resources_root = attr.ib(validator=instance_of(pathlib.Path), repr=False)
    _states_root = attr.ib(validator=instance_of(pathlib.Path), repr=False)
    _data = attr.ib(validator=instance_of(ContextData))
    _key_map = attr.ib(validator=instance_of(KeyMap))
    _debug = attr.ib(validator=instance_of(bool))
    _log = attr.ib(validator=instance_of(logging.Logger), repr=False)
    _window = attr.ib(default=None, repr=False)
    _world = attr.ib(default=None, validator=instance_of((type(None), World)))
    _ctx_exit = attr.ib(default=None, validator=instance_of((type(None), contextlib.ExitStack)), repr=False)

    @classmethod
    def _ensure_config(cls, resources_path, states_path, force=False):
        """
        Initialize the persistent configuration of the context. If force is True,
        overwrite any existing configuration in the current user directory.

        :param resources_path:
        :param states_path:
        :param force:
        :return:
        """
        # Specify the configuration file paths
        config_default = resources_path / ContextData.default_config_file
        keymap_default = resources_path / ContextData.default_keymap_file
        config_user = states_path / ContextData.default_config_file
        keymap_user = states_path / ContextData.default_keymap_file

        # Ensure that both directories (resources and states) are present
        if not resources_path.exists():
            raise FileNotFoundError(resources_path)
        elif not resources_path.is_dir():
            raise NotADirectoryError(resources_path)

        # Create the user config directory, unless it exists
        if not states_path.exists():
            states_path.mkdir(parents=True)

        # Copy the default configuration to the user-specific directory
        if not config_user.exists() or force:
            shutil.copyfile(str(config_default), str(config_user))

        # Copy the default key map to the user-specific directory
        if not keymap_user.exists() or force:
            shutil.copyfile(str(keymap_default), str(keymap_user))

        return config_user, keymap_user

    @classmethod
    def create(cls, name, user_home, engine_location, initialize=False, debug=False):
        """
        Create a new project instance.

        :param name:
        :param user_home:
        :param engine_location:
        :param initialize:
        :param debug:
        :return:
        """
        # Specify the configuration directory and the resources directory
        resources_path = engine_location / ContextData.default_resources_dir / name
        states_path = user_home / ContextData.default_config_dir / name

        # Initialize the persistent configuration
        config_user, keymap_user = cls._ensure_config(resources_path, states_path, initialize)

        # Load the configuration
        data = ContextData.from_json(config_user)

        # Load the keymap
        key_map = KeyMap.from_json(keymap_user)

        # Create the logger
        log = logging.getLogger("{}.{}".format(__name__, cls.__name__))

        return cls(name, resources_path, states_path, data, key_map, debug, log)

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
    def key_map(self):
        """
        Return the key map.

        :return:
        """
        return self._key_map

    @property
    def window(self):
        """
        Return a reference to the Window or None.

        :return:
        """
        return self._window

    @property
    def world(self):
        """
        Return a reference to the World or None.

        :return:
        """
        return self._world

    @property
    def debug(self):
        """
        Return True if debug functionality should be enabled.

        :return:
        """
        return self._debug

    def _del_glfw(self):
        """
        Close down GLFW.

        :return:
        """
        self._log.debug("Closing down GLFW.")
        glfw.terminate()

    def _del_window(self):
        """
        Delete the reference to the Window.

        :return:
        """
        self._log.debug("Destroying the Window and deleting its reference.")
        glfw.destroy_window(self._window)
        self._window = None

    def _del_world(self):
        """
        Delete the reference to the World.

        :return:
        """
        self._log.debug("Deleting the reference to World.")
        self._world = None

    def __enter__(self):
        """
        Enter the context provided by this instance.

        :return:
        """
        with contextlib.ExitStack() as ctx_mgr:
            self._log.info("Initializing the context.")

            self._log.debug("Initializing GLFW.")
            if not glfw.init():
                raise GLFWError("Cannot initialize GLFW.")
            ctx_mgr.callback(self._del_glfw)

            # Add the GLFW window hints
            for k, v in self.data.window_hints.items():
                glfw.window_hint(k, v)

            # Create the Window
            self._log.debug("Creating the window.")
            self._window = glfw.create_window(
                self.data.window_shape[0],
                self.data.window_shape[1],
                self.data.window_title,
                None,
                None
            )
            if not self._window:
                raise GLFWError("Cannot create a GLFW Window.")
            else:
                ctx_mgr.callback(self._del_window)

            # Make the OpenGL context current
            glfw.make_context_current(self._window)

            # Set the buffer swap interval (i.e. VSync)
            glfw.swap_interval(self.data.swap_interval)

            # Determine the actual context version information
            context_major = gl.glGetIntegerv(gl.GL_MAJOR_VERSION)
            context_minor = gl.glGetIntegerv(gl.GL_MINOR_VERSION)
            self._log.debug("Actually received an OpenGL Context {}.{}".format(context_major, context_minor))

            # Determine available OpenGL extensions
            # num_extensions = gl.glGetIntegerv(gl.GL_NUM_EXTENSIONS)
            # extensions = (gl.glGetStringi(gl.GL_EXTENSIONS, i).decode("utf-8") for i in range(num_extensions))
            # self._log.debug("Extensions: {}".format(", ".join(extensions)))

            # Create the World
            self._log.debug("Creating the world.")
            self._world = World.create(self)
            ctx_mgr.callback(self._del_world)

            # Register the GLFW event callbacks
            self._world.register_callbacks(self._window)
            ctx_mgr.callback(self._world.unregister_callbacks, self._window)

            # Register the World cleanup callbacks
            ctx_mgr.callback(self._world.remove_all_systems)
            ctx_mgr.callback(self._world.remove_all_entities)

            # Load the initial scene
            self._world.dispatch(SceneEvent(self.data.default_scene_file))

            self._ctx_exit = ctx_mgr.pop_all()

            return self

    def __exit__(self, exc_type, exc_val, trcbak):
        """
        Exit the context provided by this instance.

        :param exc_type:
        :param exc_val:
        :param trcbak:
        :return:
        """
        if exc_val is not None:
            self._log.error("Context exited prematurely!")

        self._log.info("Exiting the context.")
        self._ctx_exit.close()
        return False


@attr.s
class Loop(object):
    """
    The Loop runs a fixed time step implementation of the main loop.
    """
    _name = attr.ib(validator=instance_of(str))
    _ctx = attr.ib(default=Context, validator=subclass_of(Context), repr=False)
    _initialize = attr.ib(default=False, validator=instance_of(bool))
    _debug = attr.ib(default=False, validator=instance_of(bool))
    _log = attr.ib(default=logging.getLogger(__name__), validator=instance_of(logging.Logger), repr=False)

    def run(self):
        """
        Run the main loop.

        :return:
        """
        user_home = pathlib.Path.home()
        engine_location = pathlib.Path(__file__).parent

        self._log.debug("The user home is at '{}'.".format(user_home))
        self._log.debug("The engine is located at '{}'.".format(engine_location))

        with self._ctx.create(self._name, user_home, engine_location, self._initialize, self._debug) as ctx:
            self._log.debug("Entered context {}.".format(ctx))
            self._loop(ctx)

    def _loop(self, ctx):
        """
        Enter the fixed time-step loop of the game.

        The loop makes sure that the physics update is called at regular intervals based on DELTA_TIME.
        The renderer is called when enough simulation intervals have accumulated
        to let it take its time even on slow computers without jeopardizing the physics simulation.
        The maximum duration of a frame is set to FRAME_TIME_MAX.

        :param ctx:
        :return:
        """
        self._log.info("Executing within the engine context.")

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
                # Poll and process events
                glfw.poll_events()
                ctx.world.process()

                ctx.world.update(t, ctx.data.delta_time)
                t += ctx.data.delta_time
                accumulator -= ctx.data.delta_time

            # Clear the screen and render the world.
            ctx.world.render()
