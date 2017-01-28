# -*- coding: utf-8 -*-

import logging
import warnings

import OpenGL.GL as gl
import numpy
import glfw
import attr

from .components import Transform, Projection, Model, Physics
from .entities import Camera
from .events import KeyEvent, CursorEvent
from .exceptions import FixmeWarning
from .utilities import camelcase_to_underscore
from .opengl_math import identity


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
    component_types = (Transform, Physics)
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
        for transform, physics in components:
            transform.position, physics.velocity = self._integrate(
                transform.position, physics.velocity, physics.acceleration, time, delta_time
            )

    def _integrate(self, position, velocity, acceleration, time, delta_time):
        """
        Perform a fourth-order Runge Kutta integration of the equations of motion.
        Based on http://gafferongames.com/game-physics/physics-in-3d/

        :param position:
        :param velocity:
        :param acceleration:
        :param time:
        :param delta_time:
        :return:
        """
        dr_a, dv_a = self._evaluate(position, velocity, acceleration, 0, 0, time, 0)
        dr_b, dv_b = self._evaluate(position, velocity, acceleration, dr_a, dv_a, time, delta_time * 0.5)
        dr_c, dv_c = self._evaluate(position, velocity, acceleration, dr_b, dv_b, time, delta_time * 0.5)
        dr_d, dv_d = self._evaluate(position, velocity, acceleration, dr_c, dv_c, time, delta_time)

        dx_dt = 1 / 6 * (dr_a + 2 * (dr_b + dr_c) + dr_d)
        dv_dt = 1 / 6 * (dv_a + 2 * (dv_b + dv_c) + dv_d)

        new_position = position + dx_dt * delta_time
        new_velocity = velocity + dv_dt * delta_time

        return new_position, new_velocity

    def _evaluate(self, r, v, a, dr, dv, t, dt):
        """
        Evaluate the current derivative in an Euler step.

        :param r:
        :param v:
        :param a:
        :param dr:
        :param dv:
        :param t:
        :param dt:
        :return:
        """
        return v + dv * dt, a


@attr.s
class PlayerMovementSystem(EventSystem):
    component_types = (Transform, Physics, Projection)
    is_applicator = True
    event_types = (KeyEvent,)

    def process(self, event, world, components):
        key_map = world.ctx.key_map
        multiplier = 1

        if event.key in key_map and event.mods == 0:
            for transform, physics, projection in components:
                if event.key == key_map.right:
                    if event.action in (glfw.PRESS, glfw.REPEAT):
                        physics.velocity = multiplier * transform.right[:3]
                    else:
                        physics.velocity = transform.zero[:3]
                elif event.key == key_map.left:
                    if event.action in (glfw.PRESS, glfw.REPEAT):
                        physics.velocity = multiplier * -transform.right[:3]
                    else:
                        physics.velocity = transform.zero[:3]
                elif event.key == key_map.up:
                    if event.action in (glfw.PRESS, glfw.REPEAT):
                        physics.velocity = multiplier * transform.up[:3]
                    else:
                        physics.velocity = transform.zero[:3]
                elif event.key == key_map.down:
                    if event.action in (glfw.PRESS, glfw.REPEAT):
                        physics.velocity = multiplier * -transform.up[:3]
                    else:
                        physics.velocity = transform.zero[:3]
                elif event.key == key_map.forward:
                    if event.action in (glfw.PRESS, glfw.REPEAT):
                        physics.velocity = multiplier * transform.forward[:3]
                    else:
                        physics.velocity = transform.zero[:3]
                elif event.key == key_map.backward:
                    if event.action in (glfw.PRESS, glfw.REPEAT):
                        physics.velocity = multiplier * -transform.forward[:3]
                    else:
                        physics.velocity = transform.zero[:3]


@attr.s
class CameraControlSystem(EventSystem):
    component_types = (Transform, Projection)
    is_applicator = True
    event_types = (CursorEvent,)

    def process(self, event, world, components):
        cursor_origin = world.scene.cursor_origin
        cursor = numpy.array((event.xpos, event.ypos))

        for transform, projection in components:
            # Determine the position differential of the cursor
            delta_cursor = numpy.zeros(3)
            delta_cursor[:2] = cursor - cursor_origin
            delta_cursor /= numpy.linalg.norm(delta_cursor)

            target = transform.forward[:3] + 0.01 * delta_cursor
            target /= numpy.linalg.norm(target)

            transform.look_at(target)


@attr.s
class OpenGlRenderer(RenderSystem):
    """
    The OpenGLRenderer renders those Entities within the World that have Transform and Model components.
    """
    component_types = (Transform, Model)
    is_applicator = True

    def render(self, world, components):
        # Get a reference to the camera
        try:
            camera = next(world.get_entities(Camera))
            pv = camera.projection.matrix @ camera.transform.matrix
        except StopIteration:
            pv = identity()

        # Clear the render buffers
        gl.glClear(world.scene.clear_bits)

        # Render all models
        warnings.warn("Optimize rendering with multiple Entities.", FixmeWarning)
        for i, (transform, model) in enumerate(components):
            with model:
                model.draw(pv @ transform.matrix)

        glfw.swap_buffers(world.ctx.window)
