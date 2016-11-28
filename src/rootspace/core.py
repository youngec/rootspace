#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""The engine core holds the entry point into the game execution."""

import math
import abc
import collections
import contextlib
import ctypes
import inspect
import json
import logging
import pathlib
import shutil
import uuid
import weakref
import warnings
import random

import attr
import glfw
import numpy
import OpenGL.GL as gl
from attr.validators import instance_of

from .exceptions import GLFWError, TodoWarning, FixmeWarning
from .utilities import subclass_of, camelcase_to_underscore
from .opengl_math import perspective, translation, Quaternion
from .wrappers import Shader, Program, Texture
from .events import KeyEvent, CharEvent, CursorEvent, CursorEnterEvent, MouseButtonEvent, ScrollEvent, KeyMap


@attr.s
class Entity(object):
    """
    An entity is a container with a unique identifier.
    """
    _ident = attr.ib(validator=instance_of(uuid.UUID))

    @property
    def ident(self):
        """
        Return the unique identifier of this entity.

        :return:
        """
        return self._ident

    @classmethod
    def create(cls, world, **kwargs):
        """
        Create an entity.

        :param world:
        :param kwargs:
        :return:
        """
        inst = cls(uuid.uuid4(), **kwargs)
        # world.add_entity(inst)

        return inst


@attr.s
class UpdateSystem(object, metaclass=abc.ABCMeta):
    """
    A processing system for component data. Business logic variant.

    A processing system within an application world consumes the
    components of all entities, for which it was set up. At time of
    processing, the system does not know about any other component type
    that might be bound to any entity.

    Also, the processing system does not know about any specific entity,
    but only is aware of the data carried by all entities.
    """
    component_types = attr.ib(validator=instance_of(tuple))
    is_applicator = attr.ib(validator=instance_of(bool))
    _log = attr.ib(validator=instance_of(logging.Logger), repr=False)

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

    @classmethod
    def get_logger(cls):
        """
        Get the logger that best describes the specified class.

        :return:
        """
        return logging.getLogger("{}.{}".format(__name__, cls.__name__))

    def _dbg(self, message):
        """
        Send a debug message.

        :param message:
        :return:
        """
        self._log.debug(message)

    def _nfo(self, message):
        """
        Send an info message.

        :param message:
        :return:
        """
        self._log.info(message)

    def _wrn(self, message):
        """
        Send a warning message.

        :param message:
        :return:
        """
        self._log.warn(message)


@attr.s
class RenderSystem(object, metaclass=abc.ABCMeta):
    """
    A processing system for component data. Rendering variant.

    A processing system within an application world consumes the
    components of all entities, for which it was set up. At time of
    processing, the system does not know about any other component type
    that might be bound to any entity.

    Also, the processing system does not know about any specific entity,
    but only is aware of the data carried by all entities.
    """
    component_types = attr.ib(validator=instance_of(tuple))
    is_applicator = attr.ib(validator=instance_of(bool))
    _log = attr.ib(validator=instance_of(logging.Logger), repr=False)

    @abc.abstractmethod
    def render(self, world, components):
        """
        Render the current world to display.

        :param world:
        :param components:
        :return:
        """
        pass

    @classmethod
    def get_logger(cls):
        """
        Get the logger that best describes the specified class.

        :return:
        """
        return logging.getLogger("{}.{}".format(__name__, cls.__name__))

    def _dbg(self, message):
        """
        Send a debug message.

        :param message:
        :return:
        """
        self._log.debug(message)

    def _nfo(self, message):
        """
        Send an info message.

        :param message:
        :return:
        """
        self._log.info(message)

    def _wrn(self, message):
        """
        Send a warning message.

        :param message:
        :return:
        """
        self._log.warn(message)


@attr.s
class EventSystem(object, metaclass=abc.ABCMeta):
    """
    A processing system for component data. Event variant.

    A processing system within an application world consumes the
    components of all entities, for which it was set up. At time of
    processing, the system does not know about any other component type
    that might be bound to any entity.

    Also, the processing system does not know about any specific entity,
    but only is aware of the data carried by all entities.
    """
    component_types = attr.ib(validator=instance_of(tuple))
    is_applicator = attr.ib(validator=instance_of(bool))
    event_types = attr.ib(validator=instance_of(tuple))
    _log = attr.ib(validator=instance_of(logging.Logger), repr=False)

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

    @classmethod
    def get_logger(cls):
        """
        Get the logger that best describes the specified class.

        :return:
        """
        return logging.getLogger("{}.{}".format(__name__, cls.__name__))

    def _dbg(self, message):
        """
        Send a debug message.

        :param message:
        :return:
        """
        self._log.debug(message)

    def _nfo(self, message):
        """
        Send an info message.

        :param message:
        :return:
        """
        self._log.info(message)

    def _wrn(self, message):
        """
        Send a warning message.

        :param message:
        :return:
        """
        self._log.warn(message)


@attr.s(slots=True)
class Transform(object):
    _pos = attr.ib(default=numpy.zeros(3), validator=instance_of(numpy.ndarray), convert=numpy.array)
    _scale = attr.ib(default=numpy.eye(4), validator=instance_of(numpy.ndarray), convert=numpy.array)
    _quat = attr.ib(default=Quaternion(1, 0, 0, 0), validator=instance_of(Quaternion))

    @property
    def position(self):
        return self._pos

    @position.setter
    def position(self, value):
        if isinstance(value, numpy.ndarray) and value.shape == (3,):
            self._pos = value
        else:
            raise TypeError("Position must be a 3-component numpy array.")

    @property
    def scale(self):
        return self._scale
    
    @scale.setter
    def scale(self, value):
        if isinstance(value, numpy.ndarray) and value.shape == (4, 4):
            self._scale = value
        elif isinstance(value, (int, float)):
            self._scale = value * numpy.eye(4)
        else:
            raise TypeError("Scale must be a 4x4 numpy array or a scalar.")

    @property
    def orientation(self):
        return self._quat

    @orientation.setter
    def orientation(self, value):
        if isinstance(value, Quaternion):
            self._quat = value
        else:
            raise TypeError("Orientation must be a Quaternion.")

    @property
    def up(self):
        return self._quat.T.matrix4 @ (0, 1, 0, 1)

    @property
    def right(self):
        return self._quat.T.matrix4 @ (1, 0, 0, 1)

    @property
    def forward(self):
        return self._quat.T.matrix4 @ (0, 0, 1, 1)

    @property
    def matrix(self):
        return translation(self._pos) @ self._scale @ self._quat.matrix4

    def look_at(self, target):
        forward = target - self._pos
        forward /= numpy.linalg.norm(forward)

        forward_dot = self.forward[:3] @ forward
        if math.isclose(forward_dot, -1):
            self._quat = Quaternion(0, 0, 1, 0)
        elif math.isclose(forward_dot, 1):
            self._quat = Quaternion(1, 0, 0, 0)
        else:
            axis = numpy.cross(self.forward[:3], forward)
            angle = math.acos(forward_dot)
            self.rotate(axis, angle, chain=False)

    def rotate(self, axis, angle, chain=True):
        """
        Rotate the component around the given axis by the specified angle.

        :param axis:
        :param angle:
        :return:
        """
        quat = Quaternion.from_axis(axis, angle)

        if chain:
            self._quat = quat @ self._quat
        else:
            self._quat = quat


@attr.s(slots=True)
class RenderData(object):
    Uniform = collections.namedtuple("Uniform", ("type", "location", "value"))

    vao = attr.ib(validator=instance_of(int))
    vbo = attr.ib(validator=instance_of(int))
    mode = attr.ib(validator=instance_of(int))
    start_index = attr.ib(validator=instance_of(int))
    num_vertices = attr.ib(validator=instance_of(int))
    texture = attr.ib(validator=instance_of(Texture))
    program = attr.ib(validator=instance_of(Program))
    _ctx_exit = attr.ib(validator=instance_of(contextlib.ExitStack), repr=False)

    @classmethod
    def create(cls, vertices, mode, start_index, num_vertices, image_data, vertex_shader_src, fragment_shader_src):
        with contextlib.ExitStack() as ctx:
            warnings.warn("Possibly rewrite the GL calls in Direct State Access style.", TodoWarning)
            # Create and bind the Vertex Array Object
            vao = int(gl.glGenVertexArrays(1))
            ctx.callback(gl.glDeleteVertexArrays, 1, vao)
            gl.glBindVertexArray(vao)

            # Compile the shader program
            vertex_shader = Shader.create(gl.GL_VERTEX_SHADER, vertex_shader_src)
            fragment_shader = Shader.create(gl.GL_FRAGMENT_SHADER, fragment_shader_src)
            program = Program.create((vertex_shader, fragment_shader))

            position_location = program.attribute_location("vert_xyz")
            color_location = program.attribute_location("tex_uv")

            # Create the texture
            tex = Texture.create(image_data)

            # Initialise the vertex buffer
            vbo = int(gl.glGenBuffers(1))
            ctx.callback(gl.glDeleteBuffers, 1, vbo)
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
            gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW)

            # Set the appropriate pointers
            gl.glEnableVertexAttribArray(position_location)
            gl.glVertexAttribPointer(
                position_location, 3, gl.GL_FLOAT, False,
                5 * ctypes.sizeof(ctypes.c_float), None
            )
            gl.glEnableVertexAttribArray(color_location)
            gl.glVertexAttribPointer(
                color_location, 2, gl.GL_FLOAT, False,
                5 * ctypes.sizeof(ctypes.c_float), ctypes.c_void_p(3 * ctypes.sizeof(ctypes.c_float))
            )

            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
            gl.glBindVertexArray(0)

            ctx_exit = ctx.pop_all()

            return cls(vao, vbo, mode, start_index, num_vertices, tex, program, ctx_exit)

    def __del__(self):
        self._ctx_exit.close()

    def update_uniforms(self):
        pass


@attr.s
class CameraData(object):
    _fov = attr.ib(default=numpy.pi/4, validator=instance_of(float))
    _aspect = attr.ib(default=1, validator=instance_of(float))
    _near = attr.ib(default=0.1, validator=instance_of(float))
    _far = attr.ib(default=10.0, validator=instance_of(float))

    @property
    def matrix(self):
        return perspective(self._fov, self._aspect, self._near, self._far)

    @property
    def aspect(self):
        return self._aspect

    @aspect.setter
    def aspect(self, value):
        self._aspect = value


@attr.s
class TestEntity(Entity):
    transform = attr.ib(validator=instance_of(Transform), hash=False)
    render_data = attr.ib(validator=instance_of(RenderData), hash=False)

    @classmethod
    def create(cls, world, **kwargs):
        position = kwargs.pop("position")

        vertices = numpy.array([
            -1, -1, -1, 0, 0,
            1, -1, -1, 1, 0,
            -1, -1, 1, 0, 1,
            1, -1, -1, 1, 0,
            1, -1, 1, 1, 1,
            -1, -1, 1, 0, 1,
            -1, 1, -1, 0, 0,
            -1, 1, 1, 0, 1,
            1, 1, -1, 1, 0,
            1, 1, -1, 1, 0,
            -1, 1, 1, 0, 1,
            1, 1, 1, 1, 1,
            -1, -1, 1, 1, 0,
            1, -1, 1, 0, 0,
            -1, 1, 1, 1, 1,
            1, -1, 1, 0, 0,
            1, 1, 1, 0, 1,
            -1, 1, 1, 1, 1,
            -1, -1, -1, 0, 0,
            -1, 1, -1, 0, 1,
            1, -1, -1, 1, 0,
            1, -1, -1, 1, 0,
            -1, 1, -1, 0, 1,
            1, 1, -1, 1, 1,
            -1, -1, 1, 0, 1,
            -1, 1, -1, 1, 0,
            -1, -1, -1, 0, 0,
            -1, -1, 1, 0, 1,
            -1, 1, 1, 1, 1,
            -1, 1, -1, 1, 0,
            1, -1, 1, 1, 1,
            1, -1, -1, 1, 0,
            1, 1, -1, 0, 0,
            1, -1, 1, 1, 1,
            1, 1, -1, 0, 0,
            1, 1, 1, 0, 1
        ], dtype=numpy.float32)
        mode = gl.GL_TRIANGLES
        start_index = 0
        num_vertices = len(vertices) // 5

        image_data = numpy.zeros((1024, 1024), dtype=numpy.uint8)
        image_data.flat[::2] = 0xff

        vertex_path = world.ctx.resources / "shaders" / "simple_vertex.glsl"
        with vertex_path.open(mode="r") as f:
            vertex_shader = f.read()

        fragment_path = world.ctx.resources / "shaders" / "simple_fragment.glsl"
        with fragment_path.open(mode="r") as f:
            fragment_shader = f.read()

        trf = Transform(position)
        trf.rotate((1, 1, 1), math.pi/2)
        trf.scale = random.random()
        dat = RenderData.create(
            vertices, mode, start_index, num_vertices, image_data, vertex_shader, fragment_shader
        )

        inst = super().create(world=world, transform=trf, render_data=dat, **kwargs)

        world.add_component(inst, inst.transform)
        world.add_component(inst, inst.render_data)

        return inst


@attr.s
class Camera(Entity):
    transform = attr.ib(validator=instance_of(Transform), hash=False)
    camera_data = attr.ib(validator=instance_of(CameraData), hash=False)

    @property
    def matrix(self):
        mat = self.camera_data.matrix @ self.transform.matrix
        return mat

    @property
    def aspect(self):
        return self.camera_data.aspect

    @aspect.setter
    def aspect(self, value):
        self.camera_data.aspect = value

    @classmethod
    def create(cls, world, **kwargs):
        fov = kwargs.pop("field_of_view")
        aspect = kwargs.pop("aspect_ratio")
        near = kwargs.pop("near_plane")
        far = kwargs.pop("far_plane")

        transform = Transform()
        camera_data = CameraData(fov=fov, aspect=aspect, near=near, far=far)

        inst = super().create(world=world, transform=transform, camera_data=camera_data, **kwargs)

        world.add_component(inst, inst.transform)
        world.add_component(inst, inst.camera_data)

        return inst


@attr.s
class CameraControlSystem(EventSystem):
    _cursor_origin = attr.ib(validator=instance_of(numpy.ndarray), convert=numpy.array)

    @classmethod
    def create(cls, cursor_origin):
        return cls(
            component_types=(Transform, CameraData),
            is_applicator=True,
            event_types=(KeyEvent, CursorEvent),
            cursor_origin=cursor_origin,
            log=cls.get_logger()
        )

    def dispatch(self, event, world, components):
        key_map = world.ctx.data.key_map
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

                #transform.look_at(target)


@attr.s
class OpenGLRenderer(RenderSystem):
    @classmethod
    def create(cls):
        return cls(
            component_types=(Transform, RenderData),
            is_applicator=True,
            log=cls.get_logger()
        )

    def render(self, world, components):
        # Get a reference to the camera
        warnings.warn("Have to be smarter about getting the camera entity.", FixmeWarning)
        camera = world.get_entities(Camera)[0]
        pv = camera.matrix

        # Clear the render buffers
        gl.glClear(world.ctx.data.clear_bits)

        # Sort and enumerate the components
        warnings.warn("Optimize rendering with multiple Entities.", FixmeWarning)
        sorted_components = sorted(components, key=lambda c: c[1].program.obj)

        for i, (transform, data) in enumerate(sorted_components):
            # Bind the shader program and the VAO
            data.program.enable()
            gl.glActiveTexture(gl.GL_TEXTURE0)
            data.texture.enable()
            gl.glBindVertexArray(data.vao)

            data.program.uniform("mvp_matrix", pv @ transform.matrix)
            data.program.uniform("active_tex", 0)

            gl.glDrawArrays(data.mode, data.start_index, data.num_vertices)

            # Unbind the shader program and the VAO
            gl.glBindVertexArray(0)
            data.texture.disable()
            data.program.disable()

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
    _systems = attr.ib(default=attr.Factory(list), validator=instance_of(list), repr=False)
    _update_systems = attr.ib(default=attr.Factory(list), validator=instance_of(list))
    _render_systems = attr.ib(default=attr.Factory(list), validator=instance_of(list))
    _event_systems = attr.ib(default=attr.Factory(list), validator=instance_of(list))
    _component_types = attr.ib(default=attr.Factory(dict), validator=instance_of(dict), repr=False)
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

    def combined_components(self, comp_types):
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

    def add_component_type(self, component_type):
        """
        Add a supported component type to the world.

        :param component_type:
        :return:
        """
        if component_type not in self._component_types.values():
            self._components[component_type] = dict()
            self._component_types[camelcase_to_underscore(component_type.__name__)] = component_type

    def add_component(self, entity, component):
        """
        Add a supported component instance to the world.

        :param entity:
        :param component:
        :return:
        """
        # If the value is a compound component (e.g. a Button
        # inheriting from a Sprite), it needs to be added to all
        # supported component type instances.
        mro = inspect.getmro(component.__class__)
        if type in mro:
            stop = mro.index(type)
        else:
            stop = mro.index(object)

        for comp_type in mro[0:stop]:
            self.add_component_type(comp_type)
            self._components[comp_type][entity] = component

    def add_entity(self, entity):
        """
        Add an entity to the world.

        :param entity:
        :return:
        """
        self._log.debug("Adding Entity '{}'.".format(entity))
        self._entities.add(entity)

    def remove_entity(self, entity):
        """
        Remove an entity and all its data from the world.

        :param entity:
        :return:
        """
        for comp_set in self._components.values():
            comp_set.pop(entity, None)

        self._entities.discard(entity)

    def remove_entities(self):
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
        return [e for e in comp_set if comp_set[e] == component]

    def get_entities(self, entity_type):
        """
        Get
        :param entity_type:
        :return:
        """
        return [e for e in self._entities if isinstance(e, entity_type)]

    def add_system(self, system):
        """
        Add the specified system to the world.

        :param system:
        :return:
        """
        if self._is_valid_system(system):
            self._log.debug("Adding System '{}'.".format(system))
            for component_type in system.component_types:
                if component_type not in self._components:
                    self.add_component_type(component_type)

            self._systems.append(system)
            if self._is_update_system(system):
                self._update_systems.append(system)
            elif self._is_render_system(system):
                self._render_systems.append(system)
            elif self._is_event_system(system):
                self._event_systems.append(system)
        else:
            raise TypeError("The specified system cannot be used as such.")

    def remove_system(self, system):
        """
        Remove a system from the world.

        :param system:
        :return:
        """
        self._systems.remove(system)
        if system in self._update_systems:
            self._update_systems.remove(system)
        elif system in self._render_systems:
            self._render_systems.remove(system)
        elif system in self._event_systems:
            self._event_systems.remove(system)

    def remove_systems(self):
        self._log.debug("Removing all Systems from this World.")
        self._systems.clear()
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
                comps = self.combined_components(system.component_types)
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
                comps = self.combined_components(system.component_types)
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
                    comps = self.combined_components(system.component_types)
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
    Data = collections.namedtuple("Data", (
        "delta_time", "max_frame_duration", "epsilon", "window_title", "window_shape",
        "window_hints", "swap_interval", "clear_color", "clear_bits", "field_of_view",
        "near_plane", "far_plane", "key_map", "extra"
    ))

    default_ctx = Data(
        delta_time=0.01,
        max_frame_duration=0.25,
        epsilon=1e-5,
        window_title="Untitled",
        window_shape=(800, 600),
        window_hints={
            glfw.CONTEXT_VERSION_MAJOR: 3,
            glfw.CONTEXT_VERSION_MINOR: 3,
            glfw.OPENGL_FORWARD_COMPAT: True,
            glfw.OPENGL_PROFILE: glfw.OPENGL_CORE_PROFILE
        },
        swap_interval=1,
        clear_color=(0, 0, 0, 1),
        clear_bits=(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT),
        field_of_view=math.pi,
        near_plane=0.1,
        far_plane=100.0,
        key_map=KeyMap(glfw.KEY_A, glfw.KEY_D, glfw.KEY_Z, glfw.KEY_X, glfw.KEY_W, glfw.KEY_S),
        extra=None
    )
    default_config_dir = ".config"
    default_resources_dir = "resources"
    default_config_file = "config.json"

    _name = attr.ib(validator=instance_of(str))
    _resources_root = attr.ib(validator=instance_of(pathlib.Path), repr=False)
    _states_root = attr.ib(validator=instance_of(pathlib.Path), repr=False)
    _data = attr.ib(validator=instance_of(Data), repr=False)
    _window = attr.ib()
    _world = attr.ib(validator=instance_of((type(None), World)))
    _debug = attr.ib(validator=instance_of(bool))
    _log = attr.ib(validator=instance_of(logging.Logger), repr=False)
    _ctx_exit = attr.ib(validator=instance_of((type(None), contextlib.ExitStack)), repr=False)

    @classmethod
    def create(cls, name, user_home, engine_location, debug=False):
        """
        Create a new project instance.

        :param name:
        :param user_home:
        :param engine_location:
        :param debug:
        :return:
        """
        # Specify the configuration directory and the resources directory
        resources_path = engine_location / cls.default_resources_dir / name
        states_path = user_home / cls.default_config_dir / name

        # Specify the configuration file paths
        config_default = resources_path / cls.default_config_file
        config_user = states_path / cls.default_config_file

        # Ensure that both directories (resources and states) are present
        if not resources_path.exists():
            raise FileNotFoundError(resources_path)
        elif not resources_path.is_dir():
            raise NotADirectoryError(resources_path)

        if not states_path.exists():
            states_path.mkdir(parents=True)

        # Copy the default configuration to the user-specific directory
        if not config_user.exists():
            shutil.copyfile(str(config_default), str(config_user))

        # Load the configuration
        with config_user.open(mode="r") as f:
            ctx = cls.default_ctx._replace(**json.load(f))

        # Create the logger
        log = logging.getLogger("{}.{}".format(__name__, cls.__name__))

        return cls(name, resources_path, states_path, ctx, None, None, debug, log, None)

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

    def _dbg(self, message):
        """
        Send a debug message.

        :param message:
        :return:
        """
        self._log.debug(message)

    def _nfo(self, message):
        """
        Send an info message.

        :param message:
        :return:
        """
        self._log.info(message)

    def _wrn(self, message):
        """
        Send a warning message.

        :param message:
        :return:
        """
        self._log.warn(message)

    def _register_events(self):
        """
        Register event callbacks of World with GLFW.

        :return:
        """
        self._dbg("Registering GLFW event callbacks with World.")
        glfw.set_window_size_callback(self._window, self._world.dispatch_resize)
        glfw.set_key_callback(self._window, self._world.dispatch_key)
        glfw.set_cursor_pos_callback(self._window, self._world.dispatch_cursor)

    def _clear_callbacks(self):
        """
        Clear the callbacks registered with GLFW.

        :return:
        """
        self._dbg("Clearing GLFW event callbacks.")
        glfw.set_window_size_callback(self._window, None)
        glfw.set_key_callback(self._window, None)
        glfw.set_cursor_pos_callback(self._window, None)

    def _del_glfw(self):
        """
        Close down GLFW.

        :return:
        """
        self._dbg("Closing down GLFW.")
        glfw.terminate()

    def _del_window(self):
        """
        Delete the reference to the Window.

        :return:
        """
        self._dbg("Destroying the Window and deleting its reference.")
        glfw.destroy_window(self._window)
        self._window = None

    def _del_world(self):
        """
        Delete the reference to the World.

        :return:
        """
        self._dbg("Deleting the reference to World.")
        self._world = None

    def __enter__(self):
        """
        Enter the context provided by this instance.

        :return:
        """
        with contextlib.ExitStack() as ctx_mgr:
            self._nfo("Initializing the context.")

            self._dbg("Initializing GLFW.")
            if not glfw.init():
                raise GLFWError("Cannot initialize GLFW.")
            ctx_mgr.callback(self._del_glfw)

            # Add the GLFW window hints
            for k, v in self._data.window_hints.items():
                glfw.window_hint(k, v)

            # Create the Window
            self._dbg("Creating the window.")
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
            num_extensions = gl.glGetIntegerv(gl.GL_NUM_EXTENSIONS)
            extensions = (gl.glGetStringi(gl.GL_EXTENSIONS, i).decode("utf-8") for i in range(num_extensions))
            self._dbg("Actual OpenGL Context {}.{}".format(context_major, context_minor))
            self._dbg("Extensions: {}".format(", ".join(extensions)))

            # Set the buffer swap interval (i.e. VSync)
            glfw.swap_interval(self._data.swap_interval)

            # Enable the OpenGL depth buffer
            gl.glEnable(gl.GL_DEPTH_TEST)
            gl.glDepthFunc(gl.GL_LESS)

            # Enable OpenGL face culling
            gl.glEnable(gl.GL_CULL_FACE)
            gl.glFrontFace(gl.GL_CCW)
            gl.glCullFace(gl.GL_BACK)

            # Create the World
            self._dbg("Creating the world.")
            self._world = World.create(self)
            ctx_mgr.callback(self._del_world)

            # Register the GLFW event callbacks
            self._register_events()
            ctx_mgr.callback(self._clear_callbacks)

            # Add the initial systems
            self._world.add_system(OpenGLRenderer.create())
            self._world.add_system(CameraControlSystem.create(cursor_origin))
            ctx_mgr.callback(self._world.remove_systems)

            self._world.add_entity(Camera.create(
                self._world,
                field_of_view=self._data.field_of_view,
                aspect_ratio=(self._data.window_shape[0] / self._data.window_shape[1]),
                near_plane=self._data.near_plane,
                far_plane=self._data.far_plane
            ))
            self._world.add_entity(TestEntity.create(self._world, position=(0, -1, -3)))
            self._world.add_entity(TestEntity.create(self._world, position=(0, 1, -3)))
            ctx_mgr.callback(self._world.remove_entities)

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

        self._nfo("Exiting the context.")
        self._ctx_exit.close()
        return False


@attr.s
class Loop(object):
    """
    The Loop runs a fixed time step implementation of the main loop.
    """
    _name = attr.ib(validator=instance_of(str))
    _ctx = attr.ib(default=Context, validator=subclass_of(Context), repr=False)
    _debug = attr.ib(default=False, validator=instance_of(bool))
    _log = attr.ib(default=logging.getLogger(__name__), validator=instance_of(logging.Logger), repr=False)

    def run(self):
        """
        Run the main loop.

        :return:
        """
        user_home = pathlib.Path.home()
        engine_location = pathlib.Path(__file__).parent

        self._dbg("The user home is at '{}'.".format(user_home))
        self._dbg("The engine is located at '{}'.".format(engine_location))

        with self._ctx.create(self._name, user_home, engine_location, self._debug) as ctx:
            self._dbg("Entered context {}.".format(ctx))
            self._loop(ctx)

    def _loop(self, ctx):
        """
        Enter the fixed time-step loop of the game.

        The loop makes sure that the physics update is called at regular intervals based on DELTA_TIME
        from generic.py. The renderer is called when enough simulation intervals have accumulated
        to let it take its time even on slow computers without jeopardizing the physics simulation.
        The maximum duration of a frame is set to FRAME_TIME_MAX in generic.py.

        :param ctx:
        :return:
        """
        self._nfo("Executing within the engine context.")

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

    def _dbg(self, message):
        """
        Send a debug message.

        :param message:
        :return:
        """
        self._log.debug(message)

    def _nfo(self, message):
        """
        Send an info message.

        :param message:
        :return:
        """
        self._log.info(message)

    def _wrn(self, message):
        """
        Send a warning message.

        :param message:
        :return:
        """
        self._log.warn(message)
