# -*- coding: utf-8 -*-

import logging

import OpenGL.GL as gl
import glfw
import attr

from .components import Transform, Projection, Model, PhysicsState, PhysicsProperties
from .entities import Camera
from .events import KeyEvent, CursorEvent
from .utilities import camelcase_to_underscore
from .math import Matrix, Quaternion, equations_of_motion


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

    def process(self, event, world, components):
        """
        Dispatch an Event to the current set of Components.

        :param event:
        :param world:
        :param components:
        :return:
        """
        pass


@attr.s
class PhysicsSystem(UpdateSystem):
    """
    Simulate the equations of motion.
    """
    component_types = (Transform, PhysicsProperties, PhysicsState)
    is_applicator = True

    def update(self, time, delta_time, world, components):
        """
        Update the current position of a simulation of a physics-bound object.

        :param time:
        :param delta_time:
        :param world:
        :param components:
        :return:
        """
        for transform, properties, state in components:
            if any(state.momentum) or any(state.force):
                pi, mi = equations_of_motion(delta_time, state.momentum, state.force, properties.mass)

                transform.position += pi
                state.momentum += mi


@attr.s
class PlayerMovementSystem(EventSystem):
    """
    PlayerMovementSystem causes the Camera to react on the basis of keyboard button presses.
    """
    component_types = (Transform, PhysicsState, Projection)
    is_applicator = True
    event_types = (KeyEvent,)

    def process(self, event, world, components):
        key_map = world.ctx.key_map
        multiplier = 1

        if event.key in key_map and event.mods == 0:
            for transform, state, projection in components:
                direction = Matrix.zeros(3)
                if event.key == key_map.right:
                    if event.action == glfw.PRESS:
                        direction += transform.right
                    if event.action == glfw.RELEASE:
                        direction -= transform.right
                elif event.key == key_map.left:
                    if event.action == glfw.PRESS:
                        direction -= transform.right
                    elif event.action == glfw.RELEASE:
                        direction += transform.right
                elif event.key == key_map.up:
                    if event.action == glfw.PRESS:
                        direction += transform.up
                    if event.action == glfw.RELEASE:
                        direction -= transform.up
                elif event.key == key_map.down:
                    if event.action == glfw.PRESS:
                        direction -= transform.up
                    elif event.action == glfw.RELEASE:
                        direction += transform.up
                elif event.key == key_map.forward:
                    if event.action == glfw.PRESS:
                        direction -= transform.forward
                    if event.action == glfw.RELEASE:
                        direction += transform.forward
                elif event.key == key_map.backward:
                    if event.action == glfw.PRESS:
                        direction += transform.forward
                    elif event.action == glfw.RELEASE:
                        direction -= transform.forward

                if any(direction):
                    state.momentum += multiplier * direction / direction.norm()


@attr.s
class CameraControlSystem(EventSystem):
    """

    """
    component_types = (Transform, Projection)
    is_applicator = True
    event_types = (CursorEvent,)

    def process(self, event, world, components):
        pass


@attr.s
class OpenGlRenderer(RenderSystem):
    """
    The OpenGLRenderer renders those Entities within the World that have Transform and Model components.
    """
    component_types = (Transform, Model)
    is_applicator = True

    def render(self, world, components):
        # Get a reference to the camera
        for camera in world.get_entities(Camera):
            pv = camera.projection.matrix @ camera.transform.matrix

            # Clear the render buffers
            gl.glClear(world.scene.clear_bits)

            # Render all models
            for transform, model in components:
                with model:
                    model.draw(pv @ transform.matrix)

            # Swap the double buffer
            glfw.swap_buffers(world.ctx.window)
