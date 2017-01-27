# -*- coding: utf-8 -*-

import collections
import ctypes
import sys
import warnings

import attr
import sdl2.pixels
import sdl2.render
import sdl2.sdlttf
import sdl2.surface
from attr.validators import instance_of
from sdl2.events import SDL_TEXTINPUT, SDL_TEXTEDITING, SDL_KEYDOWN, SDL_KEYUP
from sdl2.keycode import SDLK_RETURN, SDLK_RETURN2, SDLK_TAB, SDLK_BACKSPACE, SDLK_DELETE, SDLK_ESCAPE

from .components import Sprite, DisplayBuffer, InputOutputStream, ShellState, MachineState
from .core import UpdateSystem, RenderSystem, EventSystem
from .exceptions import SDLError, SDLTTFError, FixmeWarning
from .filesystem import FileSystem


@attr.s
class SpriteRenderSystem(RenderSystem):
    """
    Render sprites as components of entities.
    """
    # FIXME: Handle software sprites as well!
    _renderer = attr.ib(validator=instance_of(sdl2.render.SDL_Renderer))

    @classmethod
    def create(cls, renderer):
        return cls(
            component_types=(Sprite,),
            is_applicator=False,
            sort_func=lambda e: e.depth,
            renderer=renderer.contents,
            log=cls.get_logger()
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
        r = sdl2.rect.SDL_Rect(0, 0, 0, 0)
        if isinstance(sprites, collections.Iterable):
            for sp in sprites:
                r.x, r.y = sp.position
                r.w, r.h = sp.shape
                if sdl2.render.SDL_RenderCopy(self._renderer, sp.texture, None, r) != 0:
                    raise SDLError()
        else:
            r.x, r.y = sprites.position
            r.w, r.h = sprites.shape
            if sdl2.render.SDL_RenderCopy(self._renderer, sprites.texture, None, r) != 0:
                raise SDLError()

        sdl2.render.SDL_RenderPresent(self._renderer)


@attr.s
class DisplaySystem(UpdateSystem):
    """
    Copy the data from the terminal display buffer to a texture.
    """
    _font = attr.ib(validator=instance_of(sdl2.sdlttf.TTF_Font))
    _font_color = attr.ib(validator=instance_of(sdl2.pixels.SDL_Color))
    _font_size = attr.ib(validator=instance_of(int))
    _renderer = attr.ib(validator=instance_of(sdl2.render.SDL_Renderer))

    @classmethod
    def create(cls, renderer, resource_manager,
               font_name="CourierCode-Roman.ttf", font_size=14, font_color=(0xff, 0xff, 0xff, 0xff)):
        """
        Create a terminal display system.

        :return:
        """
        color = sdl2.pixels.SDL_Color(*font_color)
        font_path = resource_manager.get_path(font_name)
        font = sdl2.sdlttf.TTF_OpenFont(font_path.encode("utf-8"), font_size)
        if not font:
            raise SDLTTFError()

        return cls(
            component_types=(DisplayBuffer, MachineState, Sprite),
            is_applicator=True,
            font=font.contents,
            font_color=color,
            font_size=font_size,
            renderer=renderer.contents,
            log=cls.get_logger()
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
        for buffer, machine, sprite in components:
            if any((machine.power_up, machine.ready, machine.power_down)) and (not buffer.empty and buffer.modified):
                surf = sdl2.sdlttf.TTF_RenderUTF8_Blended_Wrapped(
                    self._font, buffer.to_bytes(), self._font_color, sprite.shape[0]
                )
                if not surf:
                    raise SDLTTFError()

                try:
                    tx = sdl2.render.SDL_CreateTextureFromSurface(
                        self._renderer, surf.contents
                    )
                    if not tx:
                        raise SDLTTFError()

                    try:
                        min_shape = [min(a, b) for a, b in zip(self._get_tx_shape(tx), sprite.shape)]
                        dest_rect = sdl2.render.SDL_Rect(0, 0, *min_shape)

                        if sdl2.render.SDL_SetRenderTarget(self._renderer, sprite.texture) != 0:
                            raise SDLError()

                        if sdl2.render.SDL_RenderClear(self._renderer) != 0:
                            raise SDLError()

                        if sdl2.render.SDL_RenderCopy(self._renderer, tx.contents, None, dest_rect) != 0:
                            raise SDLError()

                        if sdl2.render.SDL_SetRenderTarget(self._renderer, None) != 0:
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
class DisplayInterpreterSystem(UpdateSystem):
    """
    Parse the default output stream and write the result to the display buffer.
    """
    _tab_width = attr.ib(validator=instance_of(int))
    _encoding = attr.ib(validator=instance_of(str))

    @classmethod
    def create(cls, encoding="utf-8"):
        return cls(
            component_types=(DisplayBuffer, InputOutputStream, MachineState),
            is_applicator=True,
            tab_width=4,
            encoding=encoding,
            log=cls.get_logger()
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
        for buffer, stream, machine in components:
            if any((machine.power_up, machine.ready, machine.power_down)) and len(stream.output) > 0:
                try:
                    self._interpret(buffer, stream.output)
                finally:
                    stream.output.clear()

    def _interpret(self, buffer, byte_stream):
        for b in byte_stream:
            row, column = buffer.cursor

            # Parse the individual characters
            if b.to_bytes(1, sys.byteorder).decode(self._encoding).isprintable():
                buffer.buffer[row, column] = b.to_bytes(1, sys.byteorder)
                column += 1
            elif b == 0x00:
                warnings.warn("Null character not implemented.", FixmeWarning)
            elif b == 0x07:
                warnings.warn("Bell not implemented.", FixmeWarning)
            elif b == 0x08:
                warnings.warn("Backspace not implemented.", FixmeWarning)
            elif b == 0x09:
                column += self._tab_width - (column % self._tab_width)
            elif b == 0x0a:
                column = 0
                row += 1
            elif b == 0x0b:
                warnings.warn("Vertical tab not implemented.", FixmeWarning)
            elif b == 0x0c:
                warnings.warn("Form feed not implemented.", FixmeWarning)
            elif b == 0x0d:
                warnings.warn("Carriage return not implemented.", FixmeWarning)
            elif b == 0x1a:
                warnings.warn("End of file not implemented.", FixmeWarning)
            elif b == 0x1b:
                warnings.warn("Escape character not implemented.", FixmeWarning)
            elif b == 0x7f:
                warnings.warn("Delete character not implemented.", FixmeWarning)
            else:
                self._log.debug("Got an unhandled character: {!r}".format(b))

            # Wrap around the beginning and end of a row.
            if column >= buffer.shape[1]:
                column = 0
                row += 1
            elif column < 0:
                column = buffer.shape[1] - 1
                row -= 1

            buffer.cursor = (row, column)


@attr.s
class TextInputSystem(EventSystem):
    """
    Handle input from Human Input Devices and send them to the default input stream.
    """
    _encoding = attr.ib(validator=instance_of(str))

    @classmethod
    def create(cls, encoding="utf-8"):
        return cls(
            component_types=(InputOutputStream, MachineState),
            is_applicator=True,
            event_types=(SDL_TEXTINPUT, SDL_TEXTEDITING, SDL_KEYDOWN, SDL_KEYUP),
            encoding=encoding,
            log=cls.get_logger()
        )

    def process(self, event, world, components):
        """
        React to text input or text edit events.

        :param event:
        :param world:
        :param components:
        :return:
        """
        for stream, machine in components:
            if machine.power_off:
                if event.type == SDL_KEYDOWN:
                    if event.key.keysym.sym == SDLK_ESCAPE:
                        machine.power_up = True
            elif machine.ready:
                if event.type == SDL_TEXTINPUT:
                    stream.input.extend(event.text.text)
                elif event.type == SDL_KEYDOWN:
                    if event.key.keysym.sym in (SDLK_RETURN, SDLK_RETURN2):
                        stream.input.extend(b"\n")
                    elif event.key.keysym.sym == SDLK_TAB:
                        stream.input.extend(b"\t")
                    elif event.key.keysym.sym == SDLK_BACKSPACE:
                        stream.input.extend(b"\b")
                    elif event.key.keysym.sym == SDLK_DELETE:
                        stream.input.extend(b"\x7f")
                    else:
                        self._log.debug("Got an unhandled key: {!r}".format(event.key.keysym.sym))


@attr.s
class ShellSystem(UpdateSystem):
    """
    Manage the relationship between the input and output stream. In other words, provide a shell.
    """
    _echo = attr.ib(validator=instance_of(bool))
    _keyword_separator = attr.ib(validator=instance_of(bytes))
    _line_separator = attr.ib(validator=instance_of(bytes))
    _encoding = attr.ib(validator=instance_of(str))

    @classmethod
    def create(cls, encoding="utf-8"):

        return cls(
            component_types=(InputOutputStream, FileSystem, MachineState, ShellState),
            is_applicator=True,
            echo=True,
            keyword_separator=b" ",
            line_separator=b"\n",
            encoding=encoding,
            log=cls.get_logger()
        )

    def update(self, time, delta_time, world, components):
        for stream, fs, machine, env in components:
            if machine.power_up:
                machine.ready = True
            elif machine.ready and len(stream.input) > 0:
                if self._echo:
                    stream.output.extend(stream.input)
                    self._log.debug("Input: {!r}, Output: {!r}".format(stream.input, stream.output))

                if self._line_separator in stream.input:
                    env.line_buffer = bytearray(b" ".join(env.line_buffer.strip().split()))
                    self._interpret(env.line_buffer, {"env": env, "stream": stream, "fs": fs, "machine": machine})
                    self._log.debug("Shell line buffer: {!r}".format(env.line_buffer))
                else:
                    env.line_buffer.extend(stream.input)

                stream.input.clear()
            elif machine.power_down:
                machine.power_off = True

    def _interpret(self, line_buffer, context):
        """
        Interpret a command line given a particular context.

        :param line_buffer:
        :param context:
        :return:
        """
        raise NotImplementedError("Cannot interpret commands yet.")
