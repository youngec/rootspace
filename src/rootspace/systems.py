# -*- coding: utf-8 -*-

import logging
import warnings

import OpenGL.GL as gl
import numpy
import glfw
import attr

from .components import Transform, Projection, Model
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
class CameraControlSystem(EventSystem):
    component_types = (Transform, Projection)
    is_applicator = True
    event_types = (KeyEvent, CursorEvent)

    def process(self, event, world, components):
        key_map = world.ctx.key_map
        cursor_origin = world.scene.cursor_origin
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
