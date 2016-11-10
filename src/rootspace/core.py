#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""The engine core holds the entry point into the game execution."""

import os.path
import logging
import time

import attr
from sdl2 import SDL_QUIT
from sdl2.ext import get_events
from attr.validators import instance_of

from .contexts import Context
from .utilities import subclass_of


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
        user_home = os.path.expanduser("~")
        engine_location = os.path.dirname(os.path.realpath(__file__))

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
        current_time = time.monotonic()
        accumulator = 0.0

        # Create and run the event loop
        running = True
        while running:
            # Determine how much time we have to perform the physics
            # simulation.
            new_time = time.monotonic()
            frame_time = new_time - current_time
            current_time = new_time
            frame_time = min(frame_time, ctx.data.max_frame_duration)
            accumulator += frame_time

            # Run the game update until we have one DELTA_TIME left for the
            # rendering step.
            while accumulator >= ctx.data.delta_time:
                # Process SDL events
                for event in get_events():
                    if event.type == SDL_QUIT:
                        running = False
                    else:
                        ctx.world.dispatch(event)

                ctx.world.update(t, ctx.data.delta_time)
                t += ctx.data.delta_time
                accumulator -= ctx.data.delta_time

            # Clear the screen and render the world.
            ctx.renderer.clear()
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

