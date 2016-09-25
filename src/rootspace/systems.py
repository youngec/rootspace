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
import sdl2.events
from attr.validators import instance_of

from .components import Sprite, DisplayBuffer, IOStream, BuiltinCommands
from .exceptions import SDLError, SDLTTFError


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
class TerminalDisplaySystem(UpdateSystem):
    """
    Copy the data from the terminal display buffer to a texture.
    """
    _font = attr.ib(validator=instance_of(sdl2.sdlttf.TTF_Font))
    _font_color = attr.ib(validator=instance_of(sdl2.pixels.SDL_Color))
    _font_size = attr.ib(validator=instance_of(int))
    _renderer = attr.ib(validator=instance_of(sdl2.render.SDL_Renderer))

    @classmethod
    def create(cls, renderer, resource_manager,
               font_name="FantasqueSansMono-Regular.ttf", font_size=10, font_color=(0xff, 0xff, 0xff, 0xff)):
        """
        Create a terminal display system.

        :return:
        """
        color = sdl2.pixels.SDL_Color(*font_color)
        font_path = resource_manager.get_path(font_name)
        font = sdl2.sdlttf.TTF_OpenFont(font_path.encode("utf-8"), font_size)
        if font is None:
            raise SDLTTFError()

        return cls(
            component_types=(DisplayBuffer, Sprite),
            is_applicator=True,
            font=font.contents,
            font_color=color,
            font_size=font_size,
            renderer=renderer.renderer.contents
        )

    def update(self, time, delta_time, world, components):
        """
        For each entity which has a Sprite and a DisplayBuffer,
        copy the contents of the DisplayBuffer to the Sprite for
        rendering.

        :param time:
        :param delta_time:
        :param world:
        :param components:
        :return:
        """
        for buffer, sprite in components:
            if not buffer.empty and buffer.modified:
                wrap_width = min(self._get_text_shape(buffer.get_line(0).encode("utf-8"))[0], sprite.shape[0])

                surf = sdl2.sdlttf.TTF_RenderUTF8_Blended_Wrapped(
                    self._font, buffer.to_bytes("utf-8"), self._font_color, wrap_width
                )
                if surf is None:
                    raise SDLTTFError()

                try:
                    tx = sdl2.render.SDL_CreateTextureFromSurface(
                        self._renderer, surf.contents
                    )
                    if tx is None:
                        raise SDLTTFError()

                    try:
                        min_shape = [min(a, b) for a, b in zip(self._get_tx_shape(tx), sprite.shape)]
                        dest_rect = sdl2.render.SDL_Rect(0, 0, *min_shape)

                        old_target = sdl2.render.SDL_GetRenderTarget(self._renderer)
                        if old_target is None:
                            raise SDLError()

                        if sdl2.render.SDL_SetRenderTarget(self._renderer, sprite.texture) != 0:
                            raise SDLError()

                        if sdl2.render.SDL_RenderClear(self._renderer) != 0:
                            raise SDLError()

                        if sdl2.render.SDL_RenderCopy(self._renderer, tx.contents, None, dest_rect) != 0:
                            raise SDLError()

                        if sdl2.render.SDL_SetRenderTarget(self._renderer, old_target) != 0:
                            raise SDLError()
                    finally:
                        sdl2.render.SDL_DestroyTexture(tx)

                finally:
                    sdl2.surface.SDL_FreeSurface(surf)

    def _get_text_shape(self, text_bytes):
        text_width = ctypes.c_int()
        text_height = ctypes.c_int()
        if sdl2.sdlttf.TTF_SizeUTF8(self._font, text_bytes, ctypes.byref(text_width), ctypes.byref(text_height)) != 0:
            raise SDLTTFError()

        return text_width.value, text_height.value

    def _get_tx_shape(self, texture):
        """
        Determine the texture shape.

        :param texture:
        :return:
        """
        flags = ctypes.c_uint32()
        access = ctypes.c_int()
        width = ctypes.c_int()
        height = ctypes.c_int()
        if sdl2.render.SDL_QueryTexture(
                texture, ctypes.byref(flags), ctypes.byref(access), ctypes.byref(width), ctypes.byref(height)) != 0:
            raise SDLError()

        return width.value, height.value

    def __del__(self):
        if self._font is not None:
            sdl2.sdlttf.TTF_CloseFont(self._font)
            self._font = None


@attr.s
class TerminalInterpreterSystem(UpdateSystem):
    """
    Parse the default output stream and write the result to the display buffer.
    """
    @classmethod
    def create(cls):
        return cls(
            component_types=(DisplayBuffer, IOStream),
            is_applicator=True
        )

    def update(self, time, delta_time, world, components):
        """
        For each entity with a DisplayBuffer, interpret the default output stream
        registered with the entity and output the result to the DisplayBuffer.

        :param time:
        :param delta_time:
        :param world:
        :param components:
        :return:
        """
        pass


@attr.s
class HidSystem(EventSystem):
    """
    Handle input from Human Input Devices and send them to the default input stream.
    """
    @classmethod
    def create(cls):
        return cls(
            component_types=(IOStream,),
            is_applicator=True,
            event_types=tuple()
        )

    def dispatch(self, event, world, components):
        pass
