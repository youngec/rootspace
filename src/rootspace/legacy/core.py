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
