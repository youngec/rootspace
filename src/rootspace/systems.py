# -*- coding: utf-8 -*-

import logging
from typing import Optional, Any, Sequence, Type, Dict, Iterable

import OpenGL.GL as gl
import glfw

from .components import Component, Transform, Projection, Model, \
    PhysicsState, PhysicsProperties, BoundingVolume
from .entities import Camera, StaticObject
from .events import Event, KeyEvent, CursorEvent
from .utilities import camelcase_to_underscore
from .math import Matrix, Quaternion, equations_of_motion, aabb_overlap


class SystemMeta(type):
    """
    SystemMeta registers all Systems in SystemMeta.classes
    """
    classes: Dict[str, Type["System"]] = dict()

    def __new__(mcs, name, bases, cls_dict):
        register = cls_dict.pop("register", True)
        cls_dict["_log"] = logging.getLogger("{}.{}".format(__name__, name))
        cls = super(SystemMeta, mcs).__new__(mcs, name, bases, cls_dict)
        if register:
            mcs.classes[camelcase_to_underscore(cls.__name__)] = cls

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
    component_types: Sequence[Type[Component]] = tuple()

    def __str__(self) -> str:
        return self.__class__.__name__

    def __repr__(self) -> str:
        return "{}()".format(self.__class__.__name__)

    def __eq__(self, other: Any) -> bool:
        return type(self) is type(other)


class UpdateSystem(System):
    """
    A processing system for component data. Business logic variant.
    """
    def update(self, time: float, delta_time: float, world: Any,
               components: Iterable[Sequence[Component]]) -> None:
        """
        Update the current World simulation.
        """
        pass


class RenderSystem(System):
    """
    A processing system for component data. Rendering variant.
    """
    def render(self, world: Any,
               components: Iterable[Sequence[Component]]) -> None:
        """
        Render the current World to display.
        """
        pass


class EventSystem(System):
    """
    A processing system for component data. Event variant.
    """
    event_types: Sequence[Type[Event]] = tuple()

    def process(self, event: Event, world: Any,
                components: Iterable[Sequence[Component]]) -> None:
        """
        Dispatch an Event to the current set of Components.
        """
        pass


class CollisionSystem(UpdateSystem):
    """
    Detect collisions between objects.
    """
    component_types = (Transform, BoundingVolume, PhysicsProperties,
                       PhysicsState)

    def update(self, time: float, delta_time: float, world: Any,
               components: Iterable[Sequence[Component]]) -> None:
        for trf, bv, prp, state in components:
            if any(state.momentum):
                d_mat = trf.t @ trf.r @ trf.s
                d_min = d_mat @ bv.minimum
                d_max = d_mat @ bv.maximum

                for s in world.get_entities(StaticObject):
                    s_mat = s.transform.t @ s.transform.r @ s.transform.s
                    s_min = s_mat @ s.bounding_volume.minimum
                    s_max = s_mat @ s.bounding_volume.maximum
                    if aabb_overlap(d_min, d_max, s_min, s_max):
                        state.momentum = Matrix((3, 1), 0)
                        state.force = -prp.mass * prp.g


class PhysicsSystem(UpdateSystem):
    """
    Simulate the equations of motion.
    """
    component_types = (Transform, PhysicsProperties, PhysicsState)

    def update(self, time: float, delta_time: float, world: Any,
               components: Iterable[Sequence[Component]]) -> None:
        """
        Update the current position of a simulation of a physics-bound object.
        """
        for transform, properties, state in components:
            force = state.force + (properties.mass * properties.g)
            if any(state.momentum) or any(force):
                p, m = equations_of_motion(delta_time, transform.position,
                                           state.momentum, force,
                                           properties.mass)
                transform.position = p
                state.momentum = m


class PlayerMovementSystem(EventSystem):
    """
    PlayerMovementSystem causes the Camera to react on the basis of keyboard 
    button presses.
    """
    component_types = (Transform, PhysicsState, Projection)
    event_types = (KeyEvent,)

    def process(self, event: Event, world: Any,
                components: Iterable[Sequence[Component]]) -> None:
        key_map = world.ctx.key_map
        multiplier = 1

        if event.key in key_map and event.mods == 0:
            for transform, state, projection in components:
                direction = Matrix((3, 1), 0)
                if event.action in (glfw.PRESS, glfw.REPEAT):
                    if event.key == key_map.right:
                        direction += transform.right
                    elif event.key == key_map.left:
                        direction -= transform.right
                    elif event.key == key_map.up:
                        direction += transform.up
                    elif event.key == key_map.down:
                        direction -= transform.up
                    elif event.key == key_map.forward:
                        direction += transform.forward
                    elif event.key == key_map.backward:
                        direction -= transform.forward
                    elif event.key == key_map.reset:
                        transform.reset()
                        state.reset()
                        continue

                if any(direction):
                    state.momentum = multiplier * direction / direction.norm()
                else:
                    state.momentum = direction


class CameraControlSystem(EventSystem):
    component_types = (Transform, Projection)
    event_types = (CursorEvent,)

    def __init__(self):
        self.cursor: Optional[Matrix] = None

    def process(self, event: Event, world: Any,
                components: Iterable[Sequence[Component]]) -> None:
        multiplier = 0.04
        window_shape = world.ctx.data.window_shape
        cursor = Matrix((3, 1), (
            2 * event.xpos / window_shape[0] - 1,
            -(2 * event.ypos / window_shape[1] - 1),
            0
        ))
        if self.cursor is None:
            self.cursor = cursor

        delta = self.cursor - cursor

        if not delta.all_close(0):
            self.cursor = cursor
            delta /= delta.norm() / multiplier
            for transform, projection in components:
                rot_along_right = Quaternion.from_axis(transform.right,
                                                       delta[1])
                transform.r @= rot_along_right.matrix
                rot_along_up = Quaternion.from_axis(Matrix.ey(), -delta[0])
                transform.r @= rot_along_up.matrix


class OpenGlRenderer(RenderSystem):
    """
    The OpenGLRenderer renders those Entities within the World that have 
    Transform and Model components.
    """
    component_types = (Transform, Model)

    def render(self, world: Any,
               components: Iterable[Sequence[Component]]) -> None:
        # Get a reference to the camera
        for camera in world.get_entities(Camera):
            pv = camera.projection.matrix @ camera.transform.s @ \
                 camera.transform.r @ camera.transform.t

            # Clear the render buffers
            gl.glClear(world.scene.clear_bits)

            # Render all models
            for transform, model in components:
                with model:
                    model.draw(pv @ transform.t @ transform.r @ transform.s)

            # Swap the double buffer
            glfw.swap_buffers(world.ctx.window)
