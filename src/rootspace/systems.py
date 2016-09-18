# -*- coding: utf-8 -*-

import abc
import collections
import ctypes

import attr
import sdl2.pixels
import sdl2.ext.sprite
import sdl2.ext.window
import sdl2.sdlttf
import sdl2.render
import sdl2.surface
from attr.validators import instance_of

from .components import Sprite, TerminalDisplayBuffer
from .exceptions import SDLError, SDLTTFError


@attr.s
class System(object, metaclass=abc.ABCMeta):
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
    sort_func = attr.ib()

    @abc.abstractmethod
    def render(self, world, components):
        """
        Render the current world to display.

        :param world:
        :param components:
        :return:
        """
        pass


@attr.s
class SpriteRenderSystem(RenderSystem):
    """
    Render sprites as components of entities.
    """
    # FIXME: Handle software sprites as well!
    _renderer = attr.ib(validator=instance_of(sdl2.ext.sprite.Renderer))

    @classmethod
    def create(cls, renderer):
        return cls(
            component_types=(Sprite,),
            is_applicator=False,
            sort_func=lambda e: e.depth,
            renderer=renderer
        )

    def render(self, world, components):
        """Draws the passed sprites (or sprite).

        x and y are optional arguments that can be used as relative
        drawing location for sprites. If set to None, the location
        information of the sprites are used. If set and sprites is an
        iterable, such as a list of TextureSprite objects, x and y are
        relative location values that will be added to each individual
        sprite's position. If sprites is a single TextureSprite, x and y
        denote the absolute position of the TextureSprite, if set.
        """
        sprites = sorted(components, key=self.sort_func)
        renderer = self._renderer.renderer
        r = sdl2.rect.SDL_Rect(0, 0, 0, 0)
        if isinstance(sprites, collections.Iterable):
            rcopy = sdl2.render.SDL_RenderCopy

            x = 0
            y = 0
            for sp in sprites:
                r.x = x + sp.x
                r.y = y + sp.y
                r.w, r.h = sp.shape
                if rcopy(renderer, sp.texture, None, r) == -1:
                    raise SDLError()
        else:
            r.x = sprites.x
            r.y = sprites.y
            r.w, r.h = sprites.shape
            sdl2.render.SDL_RenderCopy(renderer, sprites.texture, None, r)

        sdl2.render.SDL_RenderPresent(renderer)


@attr.s
class TerminalDisplaySystem(System):
    """
    Copy the data from the terminal display buffer to a texture.
    """
    _font = attr.ib(validator=instance_of(sdl2.sdlttf.TTF_Font))
    _font_color = attr.ib(validator=instance_of(sdl2.pixels.SDL_Color))
    _renderer = attr.ib(validator=instance_of(sdl2.render.SDL_Renderer))

    @classmethod
    def create(cls, renderer, resource_manager,
               font_name="Courier New.ttf", font_size=20, font_color=(0xff, 0xff, 0xff, 0xff)):
        """
        Create a terminal display system.

        :return:
        """
        color = sdl2.pixels.SDL_Color(*font_color)
        fname = ctypes.c_char_p(resource_manager.get_path(font_name).encode("utf-8"))
        font = sdl2.sdlttf.TTF_OpenFont(fname, font_size)
        if font is None:
            raise SDLTTFError()

        return cls(
            component_types=(Sprite, TerminalDisplayBuffer),
            is_applicator=True,
            font=font.contents,
            font_color=color,
            renderer=renderer.renderer.contents
        )

    def update(self, time, delta_time, world, components):
        """
        For each entity which has a Sprite and a TerminalDisplayBuffer,
        copy the contents of the TerminalDisplayBuffer to the Sprite for
        rendering.

        :param time:
        :param delta_time:
        :param world:
        :param components:
        :return:
        """
        for sprite, buffer in components:
            flat_buffer = ctypes.c_char_p("Help!".encode("latin1"))

            txt_surface = sdl2.sdlttf.TTF_RenderText_Solid(self._font, flat_buffer, self._font_color)
            if txt_surface is None:
                raise SDLTTFError()

            txt_texture = sdl2.render.SDL_CreateTextureFromSurface(self._renderer, txt_surface.contents)
            if txt_texture is None:
                raise SDLError()

            sdl2.surface.SDL_FreeSurface(txt_surface.contents)

            sprite.texture = txt_texture.contents

    def __del__(self):
        if self._font is not None:
            sdl2.sdlttf.TTF_CloseFont(self._font)
            self._font = None
