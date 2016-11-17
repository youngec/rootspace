# -*- coding: utf-8 -*-

import collections


KeyEvent = collections.namedtuple("KeyEvent", ("window", "key", "scancode", "action", "mods"))
CharEvent = collections.namedtuple("CharEvent", ("window", "codepoint"))
CursorEvent = collections.namedtuple("CursorEvent", ("window", "xpos", "ypos"))
CursorEnterEvent = collections.namedtuple("CursorEnterEvent", ("window", "entered"))
MouseButtonEvent = collections.namedtuple("MouseButtonEvent", ("window", "button", "action", "mods"))
ScrollEvent = collections.namedtuple("ScrollEvent", ("window", "xoffset", "yoffset"))
