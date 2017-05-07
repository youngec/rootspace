# -*- coding: utf-8 -*-

"""
The engine core holds the entry point into the game execution.
"""

import collections
import contextlib
import logging
import os
import pathlib
import shutil
import weakref
from typing import Tuple, Type, Optional, Dict, List, Any, Generator, \
    Set, Sequence

import OpenGL.GL as gl
import glfw

from .components import ComponentMeta, Component
from .data_abstractions import KeyMap, ContextData, Scene
from .entities import EntityMeta, Entity, Camera
from .events import Event, KeyEvent, CharEvent, CursorEvent, SceneEvent
from .exceptions import GLFWError
from .model_parser import PlyParser
from .systems import SystemMeta, System, UpdateSystem, RenderSystem, EventSystem


class World(object):
    """
    A simple application world.
    """

    def __init__(self, context: "Context") -> None:
        self._ctx = weakref.ref(context)
        self._entities: Set[Entity] = set()
        self._components: Dict[
            Type[Component], Dict[Entity, Component]] = dict()
        self._update_systems: List[UpdateSystem] = list()
        self._render_systems: List[RenderSystem] = list()
        self._event_systems: List[EventSystem] = list()
        self._event_queue: collections.deque = collections.deque()
        self._scene: Optional[Scene] = None
        self._log = logging.getLogger(
            "{}.{}".format(__name__, self.__class__.__name__))

    @property
    def ctx(self) -> "Context":
        return self._ctx()

    @property
    def systems(self) -> List[System]:
        return self._update_systems + self._render_systems + self._event_systems

    @property
    def scene(self) -> Scene:
        return self._scene

    def _get_components(self, comp_types: Sequence[Type[Component]]
                        ) -> Generator[Sequence[Component], None, None]:
        """
        Combine the sets of components.
        """
        comps = self._components
        key_sets = [set(comps[ctype]) for ctype in comp_types]
        value_sets = [comps[ctype] for ctype in comp_types]
        entities = key_sets[0].intersection(*key_sets[1:])

        for ent_key in entities:
            yield tuple(component[ent_key] for component in value_sets)

    def _add_component(self, entity: Entity, component: Component) -> None:
        """
        Add a supported component instance to the world.
        """
        comp_type = type(component)
        if comp_type not in self._components:
            self._components[comp_type] = dict()
        self._components[comp_type][entity] = component

    def _add_components(self, entity: Entity) -> None:
        """
        Register all components of an entity.
        """
        for c in entity.components:
            self._add_component(entity, c)

    def _remove_component(self, entity: Entity, component: Component) -> None:
        """
        Remove the component instance from the world.
        """
        comp_type = type(component)
        self._components[comp_type].pop(entity)
        if len(self._components[comp_type]) == 0:
            self._components.pop(comp_type)

    def _remove_components(self, entity: Entity) -> None:
        """
        Remove the registered components of an entity.
        """
        for c in entity.components:
            self._remove_component(entity, c)

    def get_entities(self, entity_type: Type[Entity]
                     ) -> Generator[Entity, None, None]:
        """
        Get all Entities of the specified class.
        """
        for e in self._entities:
            if isinstance(e, entity_type):
                yield e

    def _add_entity(self, entity: Entity) -> None:
        """
        Add an entity to the world.
        """
        self._log.debug("Adding Entity '{}'.".format(entity))
        self._add_components(entity)
        self._entities.add(entity)

    def add_entities(self, entities: Sequence[Entity]) -> None:
        """
        Add multiple entities to the world.
        """
        for entity in entities:
            self._add_entity(entity)

    def set_entities(self, entities: Sequence[Entity]) -> None:
        """
        Replace the current entities with the given ones.
        """
        for_removal = [e for e in self._entities if e not in entities]
        for_addition = [e for e in entities if e not in self._entities]
        self.remove_entities(for_removal)
        self.add_entities(for_addition)

    def _remove_entity(self, entity: Entity) -> None:
        """
        Remove an entity and all its data from the world.
        """
        self._remove_components(entity)
        self._entities.discard(entity)

    def remove_entities(self, entities: Sequence[Entity]) -> None:
        """
        Remove the specified Entities from the World.
        """
        for entity in entities:
            self._remove_entity(entity)

    def remove_all_entities(self) -> None:
        """
        Remove all registered Entities.
        """
        self._log.debug("Removing all Entities from this World.")
        self._entities.clear()

    def _add_system(self, system: System) -> None:
        """
        Add the specified system to the world.
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
            self._log.debug(
                "Tried to add a duplicate system: '{}'.".format(type(system))
            )

    def add_systems(self, systems: Sequence[System]) -> None:
        """
        Add multiple systems to the world.
        """
        for system in systems:
            self._add_system(system)

    def set_systems(self, systems: Sequence[System]) -> None:
        """
        Replace the registered Systems with the specified.
        """
        for_removal = [s for s in self.systems if s not in systems]
        for_addition = [s for s in systems if s not in self.systems]
        self.remove_systems(for_removal)
        self.add_systems(for_addition)

    def _remove_system(self, system: System) -> None:
        """
        Remove a system from the world.
        """
        if system in self._update_systems:
            self._update_systems.remove(system)
        elif system in self._render_systems:
            self._render_systems.remove(system)
        elif system in self._event_systems:
            self._event_systems.remove(system)

    def remove_systems(self, systems: Sequence[System]) -> None:
        """
        Remove the specified Systems.
        """
        for system in systems:
            self._remove_system(system)

    def remove_all_systems(self) -> None:
        """
        Remove all systems.
        """
        self._log.debug("Removing all Systems from this World.")
        self._update_systems.clear()
        self._render_systems.clear()
        self._event_systems.clear()

    def update(self, t: float, dt: float) -> None:
        """
        Processes all components within their corresponding systems, 
        except for the render system.
        """
        for system in self._update_systems:
            comps = self._get_components(system.component_types)
            system.update(t, dt, self, comps)

    def render(self) -> None:
        """
        Process the components that correspond to the render system.
        """
        for system in self._render_systems:
            comps = self._get_components(system.component_types)
            system.render(self, comps)

    def dispatch(self, event: Event) -> None:
        """
        Add an event to the queue.
        """
        self._event_queue.append(event)

    def process(self) -> None:
        """
        Process all events.
        """
        while len(self._event_queue) > 0:
            event = self._event_queue.popleft()
            if isinstance(event, SceneEvent):
                self._update_scene(event)
            else:
                for system in self._event_systems:
                    if isinstance(event, system.event_types):
                        comps = self._get_components(system.component_types)
                        system.process(event, self, comps)

    def register_callbacks(self, window: Any) -> None:
        """
        Register the GLFW callbacks with the specified window.
        """
        self._log.debug("Registering GLFW event callbacks with World.")
        glfw.set_window_size_callback(window, self.callback_resize)
        glfw.set_key_callback(window, self.callback_key)
        glfw.set_cursor_pos_callback(window, self.callback_cursor)

    def unregister_callbacks(self, window: Any) -> None:
        """
        Clear the GLFW callbacks for the specified window.
        """
        self._log.debug("Clearing GLFW event callbacks.")
        glfw.set_window_size_callback(window, None)
        glfw.set_key_callback(window, None)
        glfw.set_cursor_pos_callback(window, None)

    def callback_resize(self, window: Any, width: int,
                        height: int) -> None:
        """
        Dispatch a resizing event, as sent by GLFW.
        """
        for camera in self.get_entities(Camera):
            camera.shape = (width, height)

        gl.glViewport(0, 0, width, height)

    def callback_key(self, window: Any, key: int, scan_code: int,
                     action: int, mode: int) -> None:
        """
        Dispatch a Key press event, as sent by GLFW.
        """
        self.dispatch(KeyEvent(window, key, scan_code, action, mode))

    def callback_char(self, window: Any, code_point: int) -> None:
        """
        Dispatch a Character entry event, as sent by GLFW.
        """
        self.dispatch(CharEvent(window, code_point))

    def callback_cursor(self, window: Any, xpos: int,
                        ypos: int) -> None:
        """
        Dispatch a cursor movement event, as sent by GLFW.
        """
        self.dispatch(CursorEvent(window, xpos, ypos))

    def _update_scene(self, event: SceneEvent) -> None:
        """
        Update the current scene based on the supplied event.
        """
        # Create the new scene
        scene_path = self.ctx.resources / self.ctx.data.default_scenes_dir \
             / event.name
        new_scene = Scene.from_json(scene_path)

        # Update the OpenGL context according to the scene data
        self._update_context(self._scene, new_scene)

        # Update the world according to the scene data
        self._update_world(self._scene, new_scene)

        # Set the new scene as current
        self._scene = new_scene

    def _update_context(self, old_scene: Scene, new_scene: Scene) -> None:
        """
        Update the GLFW and OpenGL context according to the Scene change.
        """
        # Set the cursor behavior
        if not self.ctx.debug:
            glfw.set_input_mode(
                self.ctx.window,
                glfw.CURSOR,
                new_scene.cursor_mode
            )
            glfw.set_cursor_pos(
                self.ctx.window,
                *new_scene.cursor_origin
            )

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

    def _load_list_objects(self, scene, object_list, class_registry,
                           reference_tree=None) -> Sequence[Any]:
        objects = list()
        for v in object_list:
            cls = class_registry[v["class"]]
            kwargs = self._parse_arguments(scene, v, reference_tree)

            if hasattr(cls, "create"):
                objects.append(cls.create(self.ctx, **kwargs))
            else:
                objects.append(cls(**kwargs))

        return tuple(objects)

    def _load_dict_objects(self, scene, object_dict, class_registry,
                           reference_tree=None) -> Dict[str, Any]:
        objects: Dict[str, Any] = dict()
        for k, v in object_dict.items():
            cls = class_registry[v["class"]]
            kwargs = self._parse_arguments(scene, v, reference_tree)

            if hasattr(cls, "create"):
                objects[k] = cls.create(self.ctx, **kwargs)
            else:
                objects[k] = cls(**kwargs)

        return objects

    def _parse_arguments(self,
                         scene: Scene,
                         obj: Dict[str, Any],
                         reference_tree: Optional[Dict[str, Any]] = None
                         ) -> Dict[str, Any]:
        """
        Parse the arguments attached to the object serialization
        and return a dictionary of keyword arguments.
        """
        kwargs = dict()
        for name, arg in obj["kwargs"].items():
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

        return kwargs

    def _update_world(self, old_scene: Scene, new_scene: Scene) -> None:
        """
        Update the World according to the Scene change.
        """
        # Load the components into memory
        components = self._load_dict_objects(
            new_scene,
            new_scene.components,
            ComponentMeta.classes
        )

        # Load the entities into memory
        entities = self._load_list_objects(
            new_scene,
            new_scene.entities,
            EntityMeta.classes,
            components
        )

        # Load the systems into memory
        systems = self._load_list_objects(
            new_scene,
            new_scene.systems,
            SystemMeta.classes
        )

        self.set_entities(entities)
        self.set_systems(systems)


class Context(object):
    """
    The Context is used by the Engine to set the main loop parameters,
    the systems, entities, resources, states, etc.
    """

    def __init__(self, name: str, rpath: pathlib.Path, spath: pathlib.Path,
                 ctx_data: ContextData, key_map: KeyMap, debug: bool,
                 log: logging.Logger) -> None:
        self._name = name
        self._resources_root = rpath
        self._states_root = spath
        self._data = ctx_data
        self._key_map = key_map
        self._debug = debug
        self._log = log
        self._window: Optional[Any] = None
        self._model_parser: Optional[PlyParser] = None
        self._world: Optional[World] = None
        self._ctx_exit: Optional[contextlib.ExitStack] = None

    @classmethod
    def _ensure_config(cls, rpath: pathlib.Path, spath: pathlib.Path,
                       force: bool = False
                       ) -> Tuple[pathlib.Path, pathlib.Path]:
        """
        Initialize the persistent configuration of the context. If force is 
        True, overwrite any existing configuration in the current user 
        directory.
        """
        # Specify the configuration file paths
        config_default = rpath / ContextData.default_config_file
        keymap_default = rpath / ContextData.default_keymap_file
        config_user = spath / ContextData.default_config_file
        keymap_user = spath / ContextData.default_keymap_file

        # Ensure that both directories (resources and states) are present
        if not rpath.exists():
            raise FileNotFoundError(rpath)
        elif not rpath.is_dir():
            raise NotADirectoryError(rpath)

        # Create the user config directory, unless it exists
        if not spath.exists():
            spath.mkdir(parents=True)

        # Copy the default configuration to the user-specific directory
        if not config_user.exists() or force:
            shutil.copyfile(str(config_default), str(config_user))

        # Copy the default key map to the user-specific directory
        if not keymap_user.exists() or force:
            shutil.copyfile(str(keymap_default), str(keymap_user))

        return config_user, keymap_user

    @classmethod
    def create(cls, name: str, user_home: pathlib.Path,
               engine_location: pathlib.Path,
               initialize: bool = False, debug: bool = False) -> "Context":
        """
        Create a new project instance.
        """
        # Specify the configuration directory and the resources directory
        rpath = engine_location / ContextData.default_resources_dir / name
        spath = user_home / ContextData.default_config_dir / name

        # Initialize the persistent configuration
        config_user, keymap_user = cls._ensure_config(rpath, spath, initialize)

        # Load the configuration
        data = ContextData.from_json(config_user)

        # Load the keymap
        key_map = KeyMap.from_json(keymap_user)

        # Create the logger
        log = logging.getLogger("{}.{}".format(__name__, cls.__name__))

        return cls(name, rpath, spath, data, key_map, debug, log)

    @property
    def resources(self) -> pathlib.Path:
        """
        Return the path to the resources directory.

        :return:
        """
        return self._resources_root

    @property
    def states(self) -> pathlib.Path:
        """
        Return the path to the states directory.

        :return:
        """
        return self._states_root

    @property
    def data(self) -> ContextData:
        """
        Return the context data.

        :return:
        """
        return self._data

    @property
    def key_map(self) -> KeyMap:
        """
        Return the key map.

        :return:
        """
        return self._key_map

    @property
    def window(self) -> Any:
        """
        Return a reference to the Window or None.

        :return:
        """
        return self._window

    @property
    def model_parser(self) -> PlyParser:
        """
        Return a feference to the model parser or None.

        :return:
        """
        return self._model_parser

    @property
    def world(self) -> World:
        """
        Return a reference to the World or None.

        :return:
        """
        return self._world

    @property
    def debug(self) -> bool:
        """
        Return True if debug functionality should be enabled.

        :return:
        """
        return self._debug

    def _del_glfw(self) -> None:
        """
        Close down GLFW.

        :return:
        """
        self._log.debug("Closing down GLFW.")
        glfw.terminate()

    def _del_window(self) -> None:
        """
        Delete the reference to the Window.

        :return:
        """
        self._log.debug("Destroying the Window and deleting its reference.")
        glfw.destroy_window(self._window)
        self._window = None

    def _del_model_parser(self) -> None:
        """
        Delete the reference to the model parser.

        :return:
        """
        self._log.debug("Destroying the model parser.")
        self._model_parser = None

    def _del_world(self) -> None:
        """
        Delete the reference to the World.

        :return:
        """
        self._log.debug("Deleting the reference to World.")
        self._world = None

    def __enter__(self) -> "Context":
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
            self._log.debug(
                "Actually received an OpenGL Context {}.{}".format(
                    context_major, context_minor))

            # Create the model parser
            self._log.debug("Creating the model parser.")
            self._model_parser = PlyParser.create(
                self.resources / "shaders", self.resources / "textures")
            ctx_mgr.callback(self._del_model_parser)

            # Create the World
            self._log.debug("Creating the world.")
            self._world = World(self)
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

    def __exit__(self, exc_type: Type[Exception], exc_val: Exception,
                 trcbak: Any) -> bool:
        """
        Exit the context provided by this instance.
        """
        if exc_val is not None:
            self._log.error("Context exited prematurely!")

        self._log.info("Exiting the context.")
        self._ctx_exit.close()
        return False


class Loop(object):
    """
    The Loop runs a fixed time step implementation of the main loop.
    """

    def __init__(self, name: str, context_type: Type[Context],
                 initialize: bool, debug: bool) -> None:
        self._name = name
        self._ctx = context_type
        self._initialize = initialize
        self._debug = debug
        self._log = logging.getLogger(
            "{}.{}".format(__name__, self.__class__.__name__))

    def run(self) -> None:
        """
        Run the main loop.
        """
        user_home = pathlib.Path.home()
        engine_location = pathlib.Path(__file__).parent

        self._log.debug("The user home is at '{}'.".format(user_home))
        self._log.debug(
            "The engine is located at '{}'.".format(engine_location))

        with self._ctx.create(self._name, user_home, engine_location,
                              self._initialize, self._debug) as ctx:
            self._log.debug("Entered context {}.".format(ctx))
            self._loop(ctx)

    def _loop(self, ctx: Context) -> None:
        """
        Enter the fixed time-step loop of the game.

        The loop makes sure that the physics update is called at regular 
        intervals based on ctx.data.delta_time.
        The renderer is called when enough simulation intervals have accumulated
        to let it take its time even on slow computers without jeopardizing 
        the physics simulation.
        The maximum duration of a frame is set to ctx.data.max_frame_time.
        """
        self._log.info("Executing within the engine context.")

        # Pull in the necessary references.
        window_should_close = glfw.window_should_close
        get_time = glfw.get_time
        poll_events = glfw.poll_events
        window = ctx.window
        process = ctx.world.process
        update = ctx.world.update
        render = ctx.world.render
        delta_time = ctx.data.delta_time
        max_frame_duration = ctx.data.max_frame_duration

        # Define the time for the event loop
        t = 0.0
        current_time = get_time()
        accumulator = 0.0

        # Create and run the event loop
        while not window_should_close(window):
            # Determine how much time we have to perform the physics
            # simulation.
            new_time = get_time()
            frame_time = min(new_time - current_time, max_frame_duration)
            current_time = new_time
            accumulator += frame_time

            # Run the game update until we have one delta_time for the
            # rendering step.
            while accumulator >= delta_time:
                # Poll and process events
                poll_events()
                process()
                update(t, delta_time)
                t += delta_time
                accumulator -= delta_time

            # Clear the screen and render the world.
            render()
