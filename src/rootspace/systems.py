# -*- coding: utf-8 -*-

import logging
import warnings
import os.path

import OpenGL.GL as gl
import numpy
import glfw
import attr
from attr.validators import instance_of

from .data_abstractions import Scene
from .components import ComponentMeta, Transform, Projection, Model
from .entities import EntityMeta, Camera
from .events import KeyEvent, CursorEvent, SceneEvent
from .exceptions import FixmeWarning
from .utilities import camelcase_to_underscore


class SystemMeta(type):
    """
    SystemMeta registers all Systems in SystemMeta.classes
    """
    classes = dict()

    def __new__(meta, name, bases, cls_dict):
        register = cls_dict.pop("register", True)
        cls_dict["_log"] = logging.getLogger("{}.{}".format(__name__, name))
        cls = super(SystemMeta, meta).__new__(meta, name, bases, cls_dict)
        if register:
            meta.classes[camelcase_to_underscore(cls.__name__)] = cls

        return cls


class System(object, metaclass=SystemMeta):
    """
    A processing system for component data. Base class of all systems.

    A processing system within an application world consumes the
    components of all entities, for which it was set up. At time of
    processing, the system does not know about any other component type
    that might be bound to any entity.

    Also, the processing system does not know about any specific entity,
    but only is aware of the data carried by all entities.
    """
    component_types = tuple()
    is_applicator = True


class UpdateSystem(System):
    """
    A processing system for component data. Business logic variant.
    """
    def update(self, time, delta_time, world, components):
        """
        Update the current World simulation.

        :param float time:
        :param float delta_time:
        :param World world:
        :param components:
        :return:
        """
        pass


class RenderSystem(System):
    """
    A processing system for component data. Rendering variant.
    """
    def render(self, world, components):
        """
        Render the current World to display.

        :param world:
        :param components:
        :return:
        """
        pass


class EventSystem(System):
    """
    A processing system for component data. Event variant.
    """
    event_types = tuple()

    def dispatch(self, event, world, components):
        """
        Dispatch an Event to the current set of Components.

        :param event:
        :param world:
        :param components:
        :return:
        """
        pass


@attr.s
class CameraControlSystem(EventSystem):
    component_types = (Transform, Projection)
    is_applicator = True
    event_types = (KeyEvent, CursorEvent)

    def dispatch(self, event, world, components):
        key_map = world.ctx.key_map
        scene_system = next(world.get_systems(SceneSystem))
        cursor_origin = scene_system.scene.cursor_origin
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
                delta_cursor[:2] = cursor - cursor_origin
                delta_cursor /= numpy.linalg.norm(delta_cursor)

                target = transform.forward[:3] + 0.01 * delta_cursor
                target /= numpy.linalg.norm(target)

                # transform.look_at(target)


@attr.s
class OpenGlRenderer(RenderSystem):
    """
    The OpenGLRenderer renders those Entities within the World that have Transform and Model components.
    """
    component_types = (Transform, Model)
    is_applicator = True

    def render(self, world, components):
        # Get a reference to the camera
        camera = next(world.get_entities(Camera))
        pv = camera.projection.matrix @ camera.transform.matrix

        # Clear the render buffers
        scene_system = next(world.get_systems(SceneSystem))
        gl.glClear(scene_system.scene.clear_bits)

        # Render all models
        warnings.warn("Optimize rendering with multiple Entities.", FixmeWarning)
        for i, (transform, model) in enumerate(components):
            with model:
                model.draw(pv @ transform.matrix)

        glfw.swap_buffers(world.ctx.window)


@attr.s
class SceneSystem(EventSystem):
    """
    The SceneSystem provides the means to load the contents of a World, eg. a Scene,
    into the current context. This is triggered by a SceneEvent that contains the name of the serialized
    Scene file.
    """
    _scene = attr.ib(default=None, validator=instance_of((type(None), Scene)))

    component_types = tuple()
    is_applicator = True
    event_types = (SceneEvent,)

    @property
    def scene(self):
        return self._scene

    def _update_context(self, context, old_scene, new_scene):
        """
        Update the GLFW and OpenGL context according to the Scene change.

        :param window:
        :param old_scene:
        :param new_scene:
        :return:
        """
        # Set the cursor behavior
        glfw.set_input_mode(context.window, glfw.CURSOR, new_scene.cursor_mode)
        glfw.set_cursor_pos(context.window, *new_scene.cursor_origin)

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

    def _load_objects(self, world, scene, dict_tree, class_registry, reference_tree=None):
        """
        Load all objects from a given serialization dictionary. You must provide a reference to the World,
        the soon-to-be active Scene, a class registry. Optionally, you may provide a reference dictionary to provide
        additional lookup for serialized object references within the Scene.

        :param world:
        :param scene:
        :param dict_tree:
        :param class_registry:
        :param reference_tree:
        :return:
        """
        objects = dict()
        for k, v in dict_tree.items():
            cls = class_registry[v["class"]]
            args = list()
            for arg in v["args"]:
                if isinstance(arg, str):
                    if arg in scene:
                        args.append(scene[arg])
                    elif arg in world.ctx.data:
                        args.append(world.ctx.data[arg])
                    elif reference_tree is not None and arg in reference_tree:
                        args.append(reference_tree[arg])
                    elif any(p in arg for p in (os.path.sep, "/", "\\")):
                        args.append(world.ctx.resources / arg)
                    else:
                        args.append(arg)
                else:
                    args.append(arg)

            if hasattr(cls, "create"):
                objects[k] = cls.create(*args)
            else:
                objects[k] = cls(*args)

        return objects

    def _update_world(self, world, old_scene, new_scene):
        """
        Update the World according to the Scene change.

        :param world:
        :param old_scene:
        :param new_scene:
        :return:
        """
        # Load the components into memory
        components = self._load_objects(
            world,
            new_scene,
            new_scene.components,
            ComponentMeta.classes
        )

        # Load the entities into memory
        entities = self._load_objects(
            world,
            new_scene,
            new_scene.entities,
            EntityMeta.classes,
            components
        )

        # Load the systems into memory
        systems = self._load_objects(
            world,
            new_scene,
            new_scene.systems,
            SystemMeta.classes
        )

        # Inject the SceneSystem into the new systems dictionary
        systems["scene_system"] = self

        world.set_entities(*entities.values())
        world.set_systems(*systems.values())

    def dispatch(self, event, world, components):
        # Create the new scene
        scene_path = world.ctx.resources / world.ctx.data.default_scenes_dir / event.name
        new_scene = Scene.from_json(scene_path)

        # Update the OpenGL context according to the scene data
        self._update_context(world.ctx, self._scene, new_scene)

        # Update the world according to the scene data
        self._update_world(world, self._scene, new_scene)

        # Set the new scene as current
        self._scene = new_scene
