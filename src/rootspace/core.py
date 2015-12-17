#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""The engine core holds the entry point into the game execution."""

import collections
import logging
import time

import sdl2
import sdl2.ext
import attr
from attr.validators import instance_of

from .ebs import World, EventDispatcher


@attr.s
class Core(object):
    """
    The Core is in a sense the general object manager.
    """
    location = attr.ib(validator=instance_of(str))
    delta_time = attr.ib(validator=instance_of(float))
    max_frame_duration = attr.ib(validator=instance_of(float))
    epsilon = attr.ib(validator=instance_of(float))
    _log = attr.ib(validator=instance_of(logging.Logger))
    _resources = attr.ib(validator=instance_of(sdl2.ext.Resources))
    _window = attr.ib(validator=instance_of(sdl2.ext.Window))
    _renderer = attr.ib(validator=instance_of(sdl2.ext.Renderer))
    _factory = attr.ib(validator=instance_of(sdl2.ext.SpriteFactory))
    _world = attr.ib(validator=instance_of(World))
    _event_dispatcher = attr.ib(validator=instance_of(EventDispatcher))
    _entities = attr.ib(validator=instance_of(dict))
    _systems = attr.ib(validator=instance_of(collections.OrderedDict))

    @classmethod
    def create(cls, project_class, project_location, resource_dir, window_title, window_shape, clear_color, delta_time,
               max_frame_duration, epsilon):
        """
        Start up the Core.

        1. Initialise SDL2
        2. Create the resource database based on RESOURCE_DIR in generic.py
        3. Create and show the window based on WINDOW_TITLE and WINDOW_SHAPE in generic.py
        4. Create the renderer based on WINDOW_SHAPE and CLEAR_COLOR in generic.py
        5. Create the world (using UpdateRenderWorld instead of sdl2.ext.World)
        6. Create the sprite factory
        7. Create custom systems and then the render system
        8. Add all systems to the world in order of creation
        9. Create and add custom entities to the world
        10. Return the initialized Core instance

        :param Project project_class:
        :param str project_location:
        :param str resource_dir:
        :param str window_title:
        :param tuple[int] window_shape:
        :param tuple[float] clear_color:
        :param float delta_time:
        :param float max_frame_duration:
        :param float epsilon:
        :return:
        """
        # Get the Logger instance
        log = logging.getLogger(__name__)
        log.info("Starting up the Core.")

        # Start up SDL2
        log.debug("Initialising SDL2.")
        sdl2.ext.init()

        # Create the resource manager
        log.debug("Creating the resource manager.")
        resources = sdl2.ext.Resources(project_location, resource_dir)

        # Create a window
        log.debug("Creating the Window with title '{}' and shape {}.".format(window_title, window_shape))
        window = sdl2.ext.Window(window_title, window_shape, flags=sdl2.SDL_WINDOW_RESIZABLE)
        window.show()

        # Create the renderer and set the clear color
        log.debug("Creating the Renderer with clear color {}.".format(clear_color))
        sdl2.SDL_SetHint(sdl2.SDL_HINT_RENDER_SCALE_QUALITY, b"0")  # Use nearest neighbour scaling
        renderer = sdl2.ext.Renderer(window)
        sdl2.SDL_RenderSetLogicalSize(renderer.renderer, *window_shape)
        renderer.color = sdl2.ext.Color(*clear_color)

        # Create a world
        log.debug("Creating the World.")
        world = World()

        # Create the sprite factory (use hardware accelerated rendering)
        log.debug("Creating the SpriteFactory with hardware accelerated rendering.")
        factory = sdl2.ext.SpriteFactory(sdl2.ext.TEXTURE, renderer=renderer)

        # Create the project instance
        proj = project_class(window, world, factory)

        # Create the systems
        # Create your custom systems BEFORE the renderer (addition order dictates execution order)
        log.debug("Adding Systems to the World.")
        systems = proj.init_systems(collections.OrderedDict())
        systems['render_system'] = sdl2.ext.TextureSpriteRenderSystem(renderer)

        # Add all systems to the world
        for system in systems.values():
            world.add_system(system)

        # Create the event dispatcher
        event_dispatcher = EventDispatcher()

        # Create the game entities
        log.debug("Adding Entities to the World.")
        entities = proj.init_entities(systems, dict())

        return cls(
            project_location, delta_time, max_frame_duration, epsilon, log, resources, window, renderer,
            factory, world, event_dispatcher, entities, systems)

    def loop(self):
        """
        Enter the fixed time-step loop of the game.

        The loop makes sure that the physics update is called at regular intervals based on DELTA_TIME
        from generic.py. The renderer is called when enough simulation intervals have accumulated
        to let it take its time even on slow computers without jeopardizing the physics simulation.
        The maximum duration of a frame is set to FRAME_TIME_MAX in generic.py.

        :return:
        """
        # Execute the main loop
        self._log.info("=========== Engage. ===========")

        # Eliminate as much lookup as possible during the game loop
        renderer = self._renderer
        world = self._world
        dispatch = self._event_dispatcher.dispatch
        monotonic = time.monotonic
        min_fun = min
        max_frame_duration = self.max_frame_duration
        delta_time = self.delta_time

        # Define the time for the event loop
        t = 0.0
        current_time = monotonic()
        accumulator = 0.0

        # Create and run the event loop
        running = True
        while running:
            # Determine how much time we have to perform the physics
            # simulation.
            new_time = monotonic()
            frame_time = new_time - current_time
            current_time = new_time
            frame_time = min_fun(frame_time, max_frame_duration)
            accumulator += frame_time

            # Run the game update until we have one DELTA_TIME left for the
            # rendering step.
            while accumulator >= delta_time:
                # Process SDL events
                events = sdl2.ext.get_events()
                for event in events:
                    if event.type == sdl2.SDL_QUIT:
                        running = False
                        break
                    else:
                        dispatch(world, event)

                world.process(t, delta_time)
                t += delta_time
                accumulator -= delta_time

            # Clear the screen and render the world.
            renderer.clear()
            world.render()

        self._log.info("=========== All stop. ===========")

    def shutdown(self):
        """
        Close down the Core.

        :return:
        """
        # Close down and clean up SDL2
        self._log.debug("Closing down SDL2.")
        sdl2.ext.quit()

        self._log.info("The Core has safely shut down.")


@attr.s
class Project(object):
    """
    Base class for a project.
    """
    _window = attr.ib(validator=instance_of(sdl2.ext.Window))
    _world = attr.ib(validator=instance_of(World))
    _factory = attr.ib(validator=instance_of(sdl2.ext.SpriteFactory))

    def init_systems(self, systems):
        """
        Add project-specific systems.

        :param dict systems:
        :return:
        """
        return systems

    def init_entities(self, systems, entities):
        """
        Add project-specific entities based on the supplied systems.

        :param dict systems:
        :param dict entities:
        :return:
        """
        return entities
