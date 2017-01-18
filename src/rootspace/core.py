#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""The engine core holds the entry point into the game execution."""

import abc
import collections
import contextlib
import json
import logging
import pathlib
import shutil
import uuid
import warnings
import weakref

import OpenGL.GL as gl
import attr
import glfw
import numpy
from attr.validators import instance_of
from PIL import Image

from .events import KeyEvent, CharEvent, CursorEvent
from .exceptions import GLFWError, FixmeWarning
from .components import Transform, CameraData
from .utilities import subclass_of
from .wrappers import Model, Shader
from .model_parser import PlyParser
from .data_abstractions import KeyMap, ContextData


@attr.s(hash=False)
class Entity(object):
    """
    An entity is a container with a unique identifier.
    """
    _ident = attr.ib(validator=instance_of(uuid.UUID))

    @property
    def ident(self):
        return self._ident

    @property
    def components(self):
        return attr.astuple(self, recurse=False, filter=lambda a, c: not a.name.startswith("_"))

    @classmethod
    def make_ident(cls):
        return uuid.uuid4()

    @classmethod
    def from_dict(cls, **config):
        """
        Create an instance from a config dictionary. Non-recursive, single level.

        :param config:
        :return:
        """
        return cls(ident=cls.make_ident(), **config)

    def to_dict(self):
        """
        Serialize the instance to a dictionary. Non-recursive, single level.

        :return:
        """
        return attr.asdict(self, recurse=False, filter=lambda a, c: not a.name.startswith("_"))

    def __hash__(self):
        return self._ident.int


@attr.s
class System(object, metaclass=abc.ABCMeta):
    """
    A processing system for component data. Base class of all systems.

    A processing system within an application world consumes the
    components of all entities, for which it was set up. At time of
    processing, the system does not know about any other component type
    that might be bound to any entity.

    Also, the processing system does not know about any specific entity,
    but only is aware of the data carried by all entities.
    """
    _log = attr.ib(validator=instance_of(logging.Logger), repr=False)

    component_types = tuple()
    is_applicator = True

    @classmethod
    def get_logger(cls):
        """
        Get the logger that best describes the specified class.

        :return:
        """
        return logging.getLogger("{}.{}".format(__name__, cls.__name__))

    @classmethod
    def from_dict(cls, **config):
        """
        Create an instance from a config dictionary. Non-recursive, single level.

        :param config:
        :return:
        """
        return cls(log=cls.get_logger(), **config)

    def to_dict(self):
        """
        Serialize the instance to a dictionary. Non-recursive, single level.

        :return:
        """
        return attr.asdict(self, recurse=False, filter=lambda a, c: not a.name.startswith("_"))


@attr.s
class UpdateSystem(System):
    """
    A processing system for component data. Business logic variant.
    """

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


@attr.s
class RenderSystem(System):
    """
    A processing system for component data. Rendering variant.
    """

    @abc.abstractmethod
    def render(self, world, components):
        """
        Render the current world to display.

        :param world:
        :param components:
        :return:
        """
        pass


@attr.s
class EventSystem(System):
    """
    A processing system for component data. Event variant.
    """
    event_types = tuple()

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


@attr.s(hash=False)
class TestEntity(Entity):
    transform = attr.ib(validator=instance_of(Transform))
    open_gl_model = attr.ib(validator=instance_of(Model))


@attr.s(hash=False)
class Camera(Entity):
    transform = attr.ib(validator=instance_of(Transform))
    camera_data = attr.ib(validator=instance_of(CameraData))

    @property
    def matrix(self):
        return self.camera_data.matrix @ self.transform.matrix

    @property
    def aspect(self):
        return self.camera_data.aspect

    @aspect.setter
    def aspect(self, value):
        self.camera_data.aspect = value


@attr.s
class CameraControlSystem(EventSystem):
    _cursor_origin = attr.ib(validator=instance_of(numpy.ndarray), convert=numpy.array)

    component_types = (Transform, CameraData)
    is_applicator = True
    event_types = (KeyEvent, CursorEvent)

    def dispatch(self, event, world, components):
        key_map = world.ctx.key_map
        dt = world.ctx.data.delta_time

        if isinstance(event, KeyEvent) and event.key in key_map and event.mods == 0:
            if event.action in (glfw.PRESS, glfw.REPEAT):
                for transform, data in components:
                    absolute_speed = 10
                    speed = numpy.zeros(4)
                    if event.key == key_map.right:
                        speed = absolute_speed * transform.right
                    elif event.key == key_map.left:
                        speed = absolute_speed * -transform.right
                    elif event.key == key_map.up:
                        speed = absolute_speed * transform.up
                    elif event.key == key_map.down:
                        speed = absolute_speed * -transform.up
                    elif event.key == key_map.forward:
                        speed = absolute_speed * transform.forward
                    elif event.key == key_map.backward:
                        speed = absolute_speed * -transform.forward

                    transform.position += speed[:3] * dt

        elif isinstance(event, CursorEvent):
            cursor = numpy.array((event.xpos, event.ypos))
            for transform, data in components:
                # Determine the position differential of the cursor
                delta_cursor = numpy.zeros(3)
                delta_cursor[:2] = cursor - self._cursor_origin
                delta_cursor /= numpy.linalg.norm(delta_cursor)

                target = transform.forward[:3] + 0.01 * delta_cursor
                target /= numpy.linalg.norm(target)

                # transform.look_at(target)


@attr.s
class OpenGlRenderer(RenderSystem):
    component_types = (Transform, Model)
    is_applicator = True

    def render(self, world, components):
        # Get a reference to the camera
        camera = next(world.get_entities(Camera))
        pv = camera.matrix

        # Clear the render buffers
        gl.glClear(world.ctx.data.clear_bits)

        # Render all models
        warnings.warn("Optimize rendering with multiple Entities.", FixmeWarning)
        for i, (transform, model) in enumerate(components):
            with model:
                model.draw(pv @ transform.matrix)

        glfw.swap_buffers(world.ctx.window)


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
    _log = attr.ib(default=logging.getLogger(__name__), validator=instance_of(logging.Logger), repr=False)

    @property
    def ctx(self):
        return self._ctx()

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

    def remove_entity(self, entity):
        """
        Remove an entity and all its data from the world.

        :param entity:
        :return:
        """
        self._remove_components(entity)
        self._entities.discard(entity)

    def remove_all_entities(self):
        self._log.debug("Removing all Entities from this World.")
        self._entities.clear()

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
        Get
        :param entity_type:
        :return:
        """
        return (e for e in self._entities if isinstance(e, entity_type))

    def add_system(self, system):
        """
        Add the specified system to the world.

        :param system:
        :return:
        """
        if self._is_valid_system(system):
            self._log.debug("Adding System '{}'.".format(system))
            if self._is_update_system(system):
                self._update_systems.append(system)
            elif self._is_render_system(system):
                self._render_systems.append(system)
            elif self._is_event_system(system):
                self._event_systems.append(system)
        else:
            raise TypeError("The specified system cannot be used as such.")

    def add_systems(self, *systems):
        """
        Add multiple systems to the world.

        :param systems:
        :return:
        """
        for system in systems:
            self.add_system(system)

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

    def remove_all_systems(self):
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

    def dispatch_resize(self, window, width, height):
        for camera in self.get_entities(Camera):
            camera.aspect = width / height

        gl.glViewport(0, 0, width, height)

    def dispatch_key(self, window, key, scancode, action, mode):
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

    def dispatch_char(self, window, codepoint):
        """
        Dispatch a Character entry event, as sent by GLFW.

        :param window:
        :param codepoint:
        :return:
        """
        self.dispatch(CharEvent(window, codepoint))

    def dispatch_cursor(self, window, xpos, ypos):
        """
        Dispatch a cursor movement event, as sent by GLFW.

        :param window:
        :param xpos:
        :param ypos:
        :return:
        """
        self.dispatch(CursorEvent(window, xpos, ypos))

    def dispatch(self, event):
        """
        Dispatch an SDL2 event.

        :param event:
        :return:
        """
        for system in self._event_systems:
            if isinstance(event, system.event_types):
                if system.is_applicator:
                    comps = self._combined_components(system.component_types)
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
        with config_user.open(mode="r") as f:
            data = ContextData.from_dict(**json.load(f))

        # Load the keymap
        with keymap_user.open(mode="r") as f:
            key_map = KeyMap.from_dict(**json.load(f))

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

    def _register_events(self):
        """
        Register event callbacks of World with GLFW.

        :return:
        """
        self._log.debug("Registering GLFW event callbacks with World.")
        glfw.set_window_size_callback(self._window, self._world.dispatch_resize)
        glfw.set_key_callback(self._window, self._world.dispatch_key)
        glfw.set_cursor_pos_callback(self._window, self._world.dispatch_cursor)

    def _clear_callbacks(self):
        """
        Clear the callbacks registered with GLFW.

        :return:
        """
        self._log.debug("Clearing GLFW event callbacks.")
        glfw.set_window_size_callback(self._window, None)
        glfw.set_key_callback(self._window, None)
        glfw.set_cursor_pos_callback(self._window, None)

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
            for k, v in self._data.window_hints.items():
                glfw.window_hint(k, v)

            # Create the Window
            self._log.debug("Creating the window.")
            self._window = glfw.create_window(
                self._data.window_shape[0],
                self._data.window_shape[1],
                self._data.window_title,
                None,
                None
            )
            if not self._window:
                raise GLFWError("Cannot create a GLFW Window.")
            else:
                ctx_mgr.callback(self._del_window)

            # Set the cursor behavior
            glfw.set_input_mode(self._window, glfw.CURSOR, glfw.CURSOR_DISABLED)
            cursor_origin = (self._data.window_shape[0] // 2, self._data.window_shape[1] // 2)
            glfw.set_cursor_pos(self._window, *cursor_origin)

            # Make the OpenGL context current
            glfw.make_context_current(self._window)

            # Determine the actual context version information
            context_major = gl.glGetIntegerv(gl.GL_MAJOR_VERSION)
            context_minor = gl.glGetIntegerv(gl.GL_MINOR_VERSION)
            self._log.debug("Actually received an OpenGL Context {}.{}".format(context_major, context_minor))

            # Determine available OpenGL extensions
            # num_extensions = gl.glGetIntegerv(gl.GL_NUM_EXTENSIONS)
            # extensions = (gl.glGetStringi(gl.GL_EXTENSIONS, i).decode("utf-8") for i in range(num_extensions))
            # self._log.debug("Extensions: {}".format(", ".join(extensions)))

            # Set the buffer swap interval (i.e. VSync)
            glfw.swap_interval(self._data.swap_interval)

            # Enable the OpenGL depth buffer
            if self._data.enable_depth_test:
                gl.glEnable(gl.GL_DEPTH_TEST)
                gl.glDepthFunc(self._data.depth_function)

            # Enable OpenGL face culling
            if self._data.enable_face_culling:
                gl.glEnable(gl.GL_CULL_FACE)
                gl.glFrontFace(self._data.front_face)
                gl.glCullFace(self._data.cull_face)

            # Create the World
            self._log.debug("Creating the world.")
            self._world = World.create(self)
            ctx_mgr.callback(self._del_world)

            # Register the GLFW event callbacks
            self._register_events()
            ctx_mgr.callback(self._clear_callbacks)

            # Initialize System and Entity data
            camera_data = CameraData(
                self._data.field_of_view,
                (self._data.window_shape[0] / self._data.window_shape[1]),
                self._data.near_plane,
                self._data.far_plane
            )
            with Image.open(self.resources / "textures/test-texture.png") as txdata:
                parser = PlyParser.create()
                mesh = parser.load(self.resources / "models/cube.ply")
                simple_shader = Shader.create(
                    self.resources / "shaders/simple_vertex.glsl",
                    self.resources / "shaders/simple_fragment.glsl"
                )
                gpu_cube = Model.create(mesh, simple_shader, txdata)

            # Add the initial systems
            ctx_mgr.callback(self._world.remove_all_systems)
            self._world.add_systems(
                OpenGlRenderer.from_dict(),
                CameraControlSystem.from_dict(cursor_origin=cursor_origin)
            )

            # Add the initial entities
            ctx_mgr.callback(self._world.remove_all_entities)
            self._world.add_entities(
                Camera.from_dict(transform=Transform(), camera_data=camera_data),
                # TestEntity.from_dict(transform=Transform((0, -2, -1), (2, 0.1, 2)), open_gl_model=gpu_cube),
                # TestEntity.from_dict(transform=Transform((-2, 0, -1), (0.1, 2, 2)), open_gl_model=gpu_cube),
                TestEntity.from_dict(transform=Transform((0, -1, -1), (1, 1, 1)), open_gl_model=gpu_cube)
            )

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
                glfw.poll_events()

                ctx.world.update(t, ctx.data.delta_time)
                t += ctx.data.delta_time
                accumulator -= ctx.data.delta_time

            # Clear the screen and render the world.
            ctx.world.render()
