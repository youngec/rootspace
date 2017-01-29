# -*- coding: utf-8 -*-

import logging
import warnings

import OpenGL.GL as gl
import numpy
import glfw
import attr

from .components import Transform, Projection, Model, PhysicsState, PhysicsProperties
from .entities import Camera
from .events import KeyEvent
from .exceptions import FixmeWarning
from .utilities import camelcase_to_underscore
from .opengl_math import identity, Quaternion


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
            self._integrate(transform, properties, state, time, delta_time)

    def _integrate(self, transform, properties, state, time, delta_time):
        """
        Perform a fourth-order Runge Kutta integration of the equations of motion.
        Based on http://gafferongames.com/game-physics/

        :param transform:
        :param properties:
        :param state:
        :param time:
        :param delta_time:
        :return:
        """
        if any(state.momentum) or any(state.force):
            # Calculate the derivative state
            derivative_state = self._runge_kutta(state, delta_time)

            # Calculate the linear component
            transform.position += derivative_state.momentum / properties.mass * delta_time
            state.momentum += derivative_state.force * delta_time

            # Calculate the angular component
            r = transform.position - properties.center_of_mass
            torque = numpy.cross(derivative_state.force, r)
            angular_momentum = torque * delta_time
            transform.orientation += derivative_state.spin / properties.inertia * delta_time
            state.spin += 0.5 * (Quaternion(0, *angular_momentum) @ transform.orientation)

    def _runge_kutta(self, state: PhysicsState, delta_time: float) -> PhysicsState:
        """
        Perform a fourth-order Runge Kutta integration.
        Based on http://gafferongames.com/game-physics/

        :param state:
        :param delta_time:
        :return:
        """
        derivative_a = self._evaluate(state, PhysicsState(), 0)
        derivative_b = self._evaluate(state, derivative_a, delta_time * 0.5)
        derivative_c = self._evaluate(state, derivative_b, delta_time * 0.5)
        derivative_d = self._evaluate(state, derivative_c, delta_time)

        return (derivative_a + 2 * (derivative_b + derivative_c) + derivative_d) / 6

    def _evaluate(self, state: PhysicsState, derivative: PhysicsState, delta_time: float) -> PhysicsState:
        """
        Evaluate the current derivative in an Euler step.

        :param state:
        :param derivative:
        :param delta_time:
        :return:
        """
        return state + derivative * delta_time


@attr.s
class PlayerMovementSystem(EventSystem):
    """
    PlayerMovementSystem causes the Camera to react on the basis of keyboard button presses.
    """
    component_types = (Transform, PhysicsState, Projection)
    is_applicator = True
    event_types = (KeyEvent,)

    def process(self, event, world, components):
        warnings.warn("PlayerMovementSystem does not handle simultaneous key-presses.", FixmeWarning)
        key_map = world.ctx.key_map
        multiplier = 1

        if event.key in key_map and event.mods == 0:
            for transform, state, projection in components:
                if event.key == key_map.right:
                    if event.action in (glfw.PRESS, glfw.REPEAT):
                        state.momentum = multiplier * transform.right
                    else:
                        state.momentum = transform.zero
                elif event.key == key_map.left:
                    if event.action in (glfw.PRESS, glfw.REPEAT):
                        state.momentum = multiplier * -transform.right
                    else:
                        state.momentum = transform.zero
                elif event.key == key_map.up:
                    if event.action in (glfw.PRESS, glfw.REPEAT):
                        state.momentum = multiplier * transform.up
                    else:
                        state.momentum = transform.zero
                elif event.key == key_map.down:
                    if event.action in (glfw.PRESS, glfw.REPEAT):
                        state.momentum = multiplier * -transform.up
                    else:
                        state.momentum = transform.zero
                elif event.key == key_map.forward:
                    if event.action in (glfw.PRESS, glfw.REPEAT):
                        state.momentum = multiplier * transform.forward
                    else:
                        state.momentum = transform.zero
                elif event.key == key_map.backward:
                    if event.action in (glfw.PRESS, glfw.REPEAT):
                        state.momentum = multiplier * -transform.forward
                    else:
                        state.momentum = transform.zero


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
