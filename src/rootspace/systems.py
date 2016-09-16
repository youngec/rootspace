# -*- coding: utf-8 -*-

import collections

import attr
import sdl2.ext
from attr.validators import instance_of


@attr.s
class System(object):
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

    def update(self, time, delta_time, world, components):
        """
        Processes component items.

        :param float time:
        :param float delta_time:
        :param World world:
        :param components:
        :return:
        """
        raise NotImplementedError()


@attr.s
class SpriteRenderSystem(object):
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

    def render(self, world, components):
        """
        Render the current world.

        :param world:
        :param components:
        :return:
        """
        raise NotImplementedError()


@attr.s
class TextureSpriteRenderSystem(SpriteRenderSystem):
    _renderer = attr.ib(validator=instance_of(sdl2.ext.Renderer))

    @classmethod
    def create(cls, target):
        if isinstance(target, sdl2.ext.Renderer):
            renderer = target
        else:
            raise TypeError("Unsupported target type.")

        return cls(
            component_types=(sdl2.ext.TextureSprite,),
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
                r.w, r.h = sp.size
                if rcopy(renderer, sp.texture, None, r) == -1:
                    raise sdl2.ext.SDLError()
        else:
            r.x = sprites.x
            r.y = sprites.y
            r.w, r.h = sprites.size
            sdl2.render.SDL_RenderCopy(renderer, sprites.texture, None, r)

        sdl2.render.SDL_RenderPresent(renderer)
