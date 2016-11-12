# -*- coding: utf-8 -*-

import attr
import sdl2.render
from attr.validators import instance_of

from .components import MachineState, NetworkState, DisplayBuffer, Sprite, InputOutputStream, \
    ShellState
from .core import Entity
from .filesystem import FileSystem


@attr.s
class LocalComputer(Entity):
    """
    Define an entity that models the local computer.
    """
    machine_state = attr.ib(validator=instance_of(MachineState), hash=False)
    network_state = attr.ib(validator=instance_of(NetworkState), hash=False)
    file_system = attr.ib(validator=instance_of(FileSystem), hash=False)
    sprite = attr.ib(validator=instance_of(Sprite), hash=False)
    terminal_display_buffer = attr.ib(validator=instance_of(DisplayBuffer), hash=False)
    input_output_stream = attr.ib(validator=instance_of(InputOutputStream), hash=False)
    shell_state = attr.ib(validator=instance_of(ShellState), hash=False)

    @classmethod
    def create(cls, world, **kwargs):
        """
        Create a local computer.

        :param world:
        :param kwargs:
        :return:
        """
        position = (50, 50)
        display_shape = (700, 500)
        text_matrix_shape = (24, 80)
        resource_manager = kwargs.pop("resource_manager")
        db_path = resource_manager.get_path("local_computer.db")
        args = {k: kwargs.pop(k) for k in ("depth", "renderer", "pixel_format", "bpp", "masks") if
                k in kwargs}

        inst = super(LocalComputer, cls).create(
            world=world,
            machine_state=MachineState(),
            network_state=NetworkState(),
            file_system=FileSystem(db_path),
            sprite=Sprite.create(position, display_shape, access=sdl2.render.SDL_TEXTUREACCESS_TARGET, **args),
            terminal_display_buffer=DisplayBuffer.create(text_matrix_shape),
            input_output_stream=InputOutputStream(),
            shell_state=ShellState(),
            **kwargs
        )

        # Register the components
        world.add_component(inst.machine_state)
        world.add_component(inst.network_state)
        world.add_component(inst.file_system)
        world.add_component(inst.sprite)
        world.add_component(inst.terminal_display_buffer)
        world.add_component(inst.input_output_stream)
        world.add_component(inst.shell_state)

        return inst
