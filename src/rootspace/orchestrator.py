# -*- coding: utf-8 -*-

import contextlib
import logging
import pathlib
import warnings
from typing import Optional, Tuple, Type, Any

import glfw
import OpenGL.GL as gl

from .config import Config
from .key_map import KeyMap
from .ecs import World, SceneEvent, Scene
from .rootspace_assembly import RootspaceAssembly


class Orchestrator(object):
    default_resources_dir = "resources"
    default_config_dir = ".config"
    default_config_file = "config.json"
    default_key_map_file = "key_map.json"
    default_shaders_dir = "shaders"
    default_textures_dir = "textures"
    default_scenes_dir = "scenes"
    default_scene_file = "main.json"
    default_json_indent = 2

    def __init__(self, rpath: pathlib.Path, ppath: pathlib.Path, config: Config, key_map: KeyMap, debug: bool, log: logging.Logger) -> None:
        self.resources = rpath
        self.persistence = ppath
        self.config = config
        self.key_map = key_map
        self.debug = debug
        self.log = log
        self.ctx_exit: Optional[contextlib.ExitStack] = None
        self.window: Optional[glfw._GLFWwindow] = None
        self.world: Optional[World] = None

    @classmethod
    def new(cls, name: str, persistence_path: pathlib.Path, engine_path: pathlib.Path, initialize: bool = False, debug: bool = False) -> "Orchestrator":
        # Specify the configuration directory and the resources directory
        rpath = engine_path / cls.default_resources_dir / name
        ppath = persistence_path / cls.default_config_dir / name

        # Ensure that the resources directory is actually there.
        if not rpath.exists():
            raise FileNotFoundError(rpath)
        elif not rpath.is_dir():
            raise NotADirectoryError(rpath)

        # Initialize the persistent configuration
        config_user, keymap_user = cls._ensure_config(ppath, initialize)

        # Load the configuration
        config = Config.from_json(config_user)

        # Load the keymap
        key_map = KeyMap.from_json(keymap_user)

        # Create the logger
        log = logging.getLogger("{}.{}".format(__name__, cls.__name__))

        return cls(rpath, ppath, config, key_map, debug, log)

    @classmethod
    def _ensure_config(cls, ppath: pathlib.Path, force: bool = False) -> Tuple[pathlib.Path, pathlib.Path]:
        """
        Initialize the persistent configuration of the context. If force is 
        True, overwrite any existing configuration in the current user 
        directory.
        """
        # Specify the configuration file paths
        config_user = ppath / cls.default_config_file
        keymap_user = ppath / cls.default_key_map_file

        # Create the user config directory, unless it exists
        if not ppath.exists():
            ppath.mkdir(parents=True)

        # Copy the default configuration to the user-specific directory
        if not config_user.exists() or force:
            Config.new().to_json(config_user, indent=cls.default_json_indent)

        # Copy the default key map to the user-specific directory
        if not keymap_user.exists() or force:
            KeyMap.new().to_json(keymap_user, indent=cls.default_json_indent)

        return config_user, keymap_user

    def run(self) -> None:
        with self:
            if not (isinstance(self.window, glfw._GLFWwindow) and isinstance(self.world, World)):
                raise AttributeError("The Orchestrator context was not properly initialized.")

            # Pull in the necessary references for speed (damn Python)
            window_should_close = glfw.window_should_close
            get_time = glfw.get_time
            poll_events = glfw.poll_events
            swap_buffers = glfw.swap_buffers
            window = self.window
            process_events = self.world.process_events
            update = self.world.update
            render = self.world.render
            delta_time = self.config.delta_time
            max_frame_duration = self.config.max_frame_duration

            # Announce the start of the main loop
            self.log.info("Engage!")

            # Define the time for the event loop
            t = 0.0
            current_time = get_time()
            accumulator = 0.0

            # Create and run the event loop
            while not window_should_close(window):
                # Determine how much time we have to perform the physics
                # simulation.
                new_time = get_time()
                accumulator += min(new_time - current_time, max_frame_duration)
                current_time = new_time

                # Run the game update until we have one delta_time for the
                # rendering step.
                while accumulator >= delta_time:
                    update(t, delta_time)
                    t += delta_time
                    accumulator -= delta_time

                # Clear the screen and render the world.
                render()
                swap_buffers(window)

                # Poll for (and directly process) GLFW events
                poll_events()

                # Process all World-internal events
                process_events()

    def __enter__(self) -> "Orchestrator":
        with contextlib.ExitStack() as ctx_mgr:
            self.log.info("Entering the orchestrator context.")

            self.log.debug("Initializing GLFW.")
            if not glfw.init():
                raise RuntimeError("Cannot initialize GLFW.")
            ctx_mgr.callback(glfw.terminate)

            # Add the GLFW window hints
            glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
            glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
            glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)
            glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

            # Create the Window
            self.log.debug("Creating the window.")
            self.window = glfw.create_window(
                self.config.shape[0],
                self.config.shape[1],
                self.config.title,
                None,
                None
            )
            if not self.window:
                raise RuntimeError("Cannot create a GLFW Window.")
            else:
                ctx_mgr.callback(glfw.destroy_window, self.window)

            # Make the OpenGL context current
            glfw.make_context_current(self.window)

            # Set the buffer swap interval (i.e. VSync)
            glfw.swap_interval(self.config.vsync)

            # Set the cursor behavior
            if not self.debug:
                glfw.set_input_mode(self.window, glfw.CURSOR, self.config.cursor_mode)
                glfw.set_cursor_pos(self.window, *self.config.cursor_origin)
            
            # Enable the OpenGL depth buffer
            if self.config.depth_test:
                gl.glEnable(gl.GL_DEPTH_TEST)
                gl.glDepthFunc(self.config.depth_function)
            else:
                gl.glDisable(gl.GL_DEPTH_TEST)

            # Enable OpenGL face culling
            if self.config.face_culling:
                gl.glEnable(gl.GL_CULL_FACE)
                gl.glFrontFace(self.config.front_face)
                gl.glCullFace(self.config.cull_face)
            else:
                gl.glDisable(gl.GL_CULL_FACE)

            # Determine the actual context version information
            context_major = gl.glGetIntegerv(gl.GL_MAJOR_VERSION)
            context_minor = gl.glGetIntegerv(gl.GL_MINOR_VERSION)
            self.log.debug(
                "Actually received an OpenGL context {}.{}".format(
                    context_major, context_minor))

            # Create the World
            self.log.debug("Creating the world.")
            self.world = World.new(
                RootspaceAssembly.new(), 
                scene=Scene.from_json(self.resources / self.default_scenes_dir / self.default_scene_file)
            )
            def del_world() -> None:
                del self.world
            ctx_mgr.callback(del_world)

            # Register the GLFW event callbacks
            self.log.debug("Registering GLFW event callbacks.")
            raise NotImplementedError()

            # Pop the context
            self.log.debug("Orchestrator context creation complete.")
            self.ctx_exit = ctx_mgr.pop_all()

            return self

    def __exit__(self, exc_type: Type[Exception], exc_val: Exception, trcbak: Any) -> bool:
        if exc_val is not None:
            self.log.error("Orchestrator context exited prematurely!")
        if self.ctx_exit is not None:
            self.log.info("Exiting the orchestrator context.")
            warnings.warn("Save the current world state before destroying it!!!")
            self.ctx_exit.close()
        return False
