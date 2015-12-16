#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""The engine core holds the entry point into the game execution."""

import collections
import logging
import time
import warnings

import sdl2
import sdl2.ext
import attr
from attr.validators import instance_of

from .exceptions import NotImplementedWarning
from .systems import EventDispatcher


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
    _world = attr.ib(validator=instance_of(sdl2.ext.World))
    _event_dispatcher = attr.ib(validator=instance_of(EventDispatcher))
    _entities = attr.ib(validator=instance_of(dict))
    _systems = attr.ib(validator=instance_of(collections.OrderedDict))

    @classmethod
    def create(cls, project_location, resource_dir, window_title, window_shape, clear_color, delta_time,
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

        :param project_location:
        :param resource_dir:
        :param window_title:
        :param window_shape:
        :param clear_color:
        :param delta_time:
        :param max_frame_duration:
        :param epsilon:
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
        world = UpdateRenderWorld()

        # Create the sprite factory (use hardware accelerated rendering)
        log.debug("Creating the SpriteFactory with hardware accelerated rendering.")
        factory = sdl2.ext.SpriteFactory(sdl2.ext.TEXTURE, renderer=renderer)

        # Create the systems
        # Create your custom systems BEFORE the renderer (addition order dictates execution order)
        log.debug("Adding Systems to the World.")
        systems = collections.OrderedDict()
        # TODO: self._create_systems()
        systems['render_system'] = sdl2.ext.TextureSpriteRenderSystem(renderer)

        # Add all systems to the world
        for system in systems.values():
            world.add_system(system)

        # Create the event dispatcher
        event_dispatcher = EventDispatcher(world)

        # Create the game entities
        log.debug("Adding Entities to the World.")
        entities = dict()
        # TODO: self._add_entities()

        return cls(
            project_location, delta_time, max_frame_duration, epsilon, log, resources, window, renderer,
            factory, world, event_dispatcher, entities, systems)

    def _create_systems(self):
        """
        Create the systems that manipulate the world. They will later be added
        to the world automatically.

        Use: self._systems['name'] = System()

        :return:
        """
        warnings.warn("You are calling an abstract method. No Systems added.", NotImplementedWarning)

    def _add_entities(self):
        """
        Create and add entities to the world.

        Use: self._entities['name'] = Entity(self._world, *args, **kwargs)

        :return:
        """
        warnings.warn("You are calling an abstract method. No Entities added.", NotImplementedWarning)

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
                        dispatch(event)

                # This function should take both t and dt as arguments I
                # circumvented this by creating a module_level constant in
                # generic.py, DELTA_TIME.
                world.process()

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


class UpdateRenderWorld(sdl2.ext.World):
    """
    Re-implement the sdl2.ext.World to separate rendering from updating.
    Why do this? If you check out the main loop in core.Core, you'll see that I use a fixed time-step
    loop that ensures stable regular execution of the physics update, even if the rendering step takes long,
    which is the case on slow machines. Thus, I need to keep these two steps (update, render) separated.
    """

    def update(self):
        """
        Processes all components within their corresponding systems, except for the render system.

        :return:
        """
        components = self.components
        syst = [sys for sys in self._systems if not isinstance(sys, sdl2.ext.SpriteRenderSystem)]
        for system in syst:
            s_process = system.process
            if getattr(system, "is_applicator", False):
                comps = self.combined_components(system.componenttypes)
                s_process(self, comps)
            else:
                for ctype in system.componenttypes:
                    s_process(self, components[ctype].values())

    def render(self):
        """
        Process the components that correspond to the render system.

        :return:
        """

        components = self.components
        render_systems = [sys for sys in self._systems if isinstance(sys, sdl2.ext.SpriteRenderSystem)]
        for system in render_systems:
            s_process = system.process
            for ctype in system.componenttypes:
                s_process(self, components[ctype].values())
