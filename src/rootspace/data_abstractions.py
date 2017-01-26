# -*- coding: utf-8 -*-

"""
Define data abstractions for various concepts.
"""

import array
import ctypes
import enum
import math
import json

import attr
import glfw
from OpenGL.GL import GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, GL_LESS, GL_CCW, GL_BACK
from attr.validators import instance_of

from .utilities import iterable_of
from .exceptions import SerializationError


@attr.s
class DataModel(object):
    """
    The interface of a data abstraction class.
    """
    version = "1.0.0"

    @classmethod
    def from_dict(cls, **config):
        """
        Create an instance from a dictionary.

        :param config:
        :return:
        """
        return cls(**config)

    @classmethod
    def from_json(cls, file_path):
        """
        Create an instance from a JSON file.

        :param file_path:
        :return:
        """
        with file_path.open("r") as f:
            data = json.load(f)
            data_version = data.pop("version", None)
            if data_version is None or data_version != cls.version:
                raise SerializationError("Incompatible serialization format '{}' (expected '{}').".format(
                    data_version, cls.version
                ))
            return cls.from_dict(**data)

    def __iter__(self):
        """
        Iterate over the scene properties.

        :return:
        """
        for k in attr.asdict(self).keys():
            yield k

    def __getitem__(self, item):
        """
        Allow angle-bracket access.

        :param item:
        :return:
        """
        return attr.asdict(self)[item]


@attr.s
class ContextData(DataModel):
    """
    Contains simple Context data.
    """
    version = "1.0.0"

    default_config_dir = ".config"
    default_resources_dir = "resources"
    default_scenes_dir = "scenes"
    default_config_file = "config.json"
    default_keymap_file = "key_map.json"
    default_scene_file = "main.json"

    # Settings for the main loop
    delta_time = attr.ib(default=0.01, validator=instance_of(float), convert=float)
    max_frame_duration = attr.ib(default=0.25, validator=instance_of(float), convert=float)
    epsilon = attr.ib(default=1e-5, validator=instance_of(float), convert=float)
    swap_interval = attr.ib(default=1, validator=instance_of(int), convert=int)

    # Settings for the window
    window_title = attr.ib(default="Untitled", validator=instance_of(str))
    window_shape = attr.ib(default=(1024, 768), validator=iterable_of(tuple, int), convert=tuple)

    # Settings for the OpenGL context
    window_hint_context_version_major = attr.ib(default=3, validator=instance_of(int), convert=int)
    window_hint_context_version_minor = attr.ib(default=3, validator=instance_of(int), convert=int)
    window_hint_opengl_forward_compat = attr.ib(default=True, validator=instance_of(bool), convert=bool)
    window_hint_opengl_profile = attr.ib(default=glfw.OPENGL_CORE_PROFILE, validator=instance_of(int), convert=int)

    @property
    def window_hints(self):
        """
        Return the GLFW window hints as dictionary.

        :return:
        """
        window_hints = dict()
        for k, v in attr.asdict(self, filter=lambda a, v: a.name.startswith("window_hint")).items():
            name = getattr(glfw, k.replace("window_hint_", "").upper())
            window_hints[name] = v

        return window_hints


@attr.s
class KeyMap(DataModel):
    """
    KeyMap shall hold all known keys and corresponding actions.
    """
    version = "1.0.0"

    class Key(enum.Enum):
        A = glfw.KEY_A
        D = glfw.KEY_D
        S = glfw.KEY_S
        W = glfw.KEY_W
        X = glfw.KEY_X
        Z = glfw.KEY_Z

        @classmethod
        def coerce(cls, value):
            if isinstance(value, cls):
                return value
            elif isinstance(value, str):
                try:
                    return cls[value]
                except KeyError:
                    raise ValueError("Key {} is not known.".format(value))
            else:
                raise ValueError("Key {} is not known.".format(value))

    _left = attr.ib(validator=instance_of(Key), convert=Key.coerce)
    _right = attr.ib(validator=instance_of(Key), convert=Key.coerce)
    _up = attr.ib(validator=instance_of(Key), convert=Key.coerce)
    _down = attr.ib(validator=instance_of(Key), convert=Key.coerce)
    _forward = attr.ib(validator=instance_of(Key), convert=Key.coerce)
    _backward = attr.ib(validator=instance_of(Key), convert=Key.coerce)

    def __iter__(self):
        """
        Iterate over the GLFW constants in the KeyMap.

        :return:
        """
        for member in attr.astuple(self):
            yield member.value

    def __getattr__(self, item):
        """
        Return the appropriate GLFW symbol for the requested action.

        :param item:
        :return:
        """
        candidates = attr.astuple(self, filter=lambda a, v: item in a.name)
        if len(candidates) == 1:
            return candidates[0].value
        else:
            raise AttributeError("Attribute '{}' was not found.".format(item))


@attr.s
class Scene(DataModel):
    """
    Encapsulate the concept of a scene.
    """
    version = "1.0.0"

    # Settings for the render pipeline
    enable_depth_test = attr.ib(default=True, validator=instance_of(bool), convert=bool)
    depth_function = attr.ib(default=GL_LESS, validator=instance_of(int), convert=int)
    enable_face_culling = attr.ib(default=True, validator=instance_of(bool), convert=bool)
    front_face = attr.ib(default=GL_CCW, validator=instance_of(int), convert=int)
    cull_face = attr.ib(default=GL_BACK, validator=instance_of(int), convert=int)
    clear_color = attr.ib(default=(0, 0, 0, 1), validator=iterable_of(tuple, int), convert=tuple)
    clear_bits = attr.ib(default=(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT), validator=instance_of(int), convert=int)

    # Settings for the cursor
    cursor_mode = attr.ib(default=glfw.CURSOR_DISABLED, validator=instance_of(int), convert=int)
    cursor_origin = attr.ib(default=(512, 384), validator=iterable_of(tuple, int), convert=tuple)

    # Settings for the camera
    field_of_view = attr.ib(default=math.pi, validator=instance_of(float), convert=float)
    near_plane = attr.ib(default=0.1, validator=instance_of(float), convert=float)
    far_plane = attr.ib(default=100.0, validator=instance_of(float), convert=float)

    # Actual scene data
    systems = attr.ib(default=attr.Factory(dict), validator=instance_of(dict))
    entities = attr.ib(default=attr.Factory(dict), validator=instance_of(dict))
    components = attr.ib(default=attr.Factory(dict), validator=instance_of(dict))


@attr.s
class Attribute(object):
    """
    An Attribute defines the parameters necessary for the graphics library to read data from the vertex buffer.
    """

    class Type(enum.Enum):
        Other = 0
        Position = 1
        Color = 2
        Texture = 3

        @classmethod
        def coerce(cls, type_value):
            if isinstance(type_value, cls):
                return type_value
            elif isinstance(type_value, str):
                try:
                    return cls[type_value.capitalize()]
                except KeyError:
                    return cls.Other
            else:
                return cls.Other

    class DataType(enum.Enum):
        Int8 = ctypes.c_int8
        Uint8 = ctypes.c_uint8
        Int16 = ctypes.c_int16
        Uint16 = ctypes.c_uint16
        Int32 = ctypes.c_int32
        Uint32 = ctypes.c_uint32
        Float = ctypes.c_float
        Double = ctypes.c_double

        @classmethod
        def coerce(cls, value):
            equivalency = {
                "b": cls.Int8, "B": cls.Uint8, "h": cls.Int16, "H": cls.Uint16, "i": cls.Int32,
                "I": cls.Uint32, "f": cls.Float, "d": cls.Double
            }
            if isinstance(value, cls):
                return value
            elif isinstance(value, str):
                try:
                    return equivalency[value]
                except KeyError:
                    raise ValueError("Cannot convert value {} to a valid data type.".format(value))
            else:
                raise ValueError("Cannot convert value {} to a valid data type.".format(value))

    type = attr.ib(validator=instance_of(Type), convert=Type.coerce)
    data_type = attr.ib(validator=instance_of(DataType), convert=DataType.coerce)
    components = attr.ib(validator=instance_of(int))
    stride = attr.ib(validator=instance_of(int))
    start_idx = attr.ib(validator=instance_of(int))

    @property
    def stride_bytes(self):
        return self.stride * ctypes.sizeof(self.data_type.value)

    @property
    def start_ptr(self):
        return ctypes.c_void_p(self.start_idx * ctypes.sizeof(self.data_type.value))

    @property
    def location(self):
        return self.type.value


@attr.s
class Mesh(object):
    """
    The Mesh encapsulates all data necessary for the graphics library to render. It contains
    vertex data, vertex indices, vertex attribute descriptors and the draw mode enum.
    """

    class DrawMode(enum.Enum):
        Points = 0
        LineStrip = 3
        LineLoop = 2
        Lines = 1
        LineStripAdjacency = 11
        LinesAdjacency = 10
        TriangleStrip = 5
        TriangleFan = 6
        Triangles = 4
        TriangleStripAdjacency = 13
        TrianglesAdjacency = 12
        Patches = 14

    data = attr.ib(validator=instance_of(array.array))
    index = attr.ib(validator=instance_of(array.array))
    attributes = attr.ib(validator=instance_of(tuple), convert=tuple)
    draw_mode = attr.ib(validator=instance_of(DrawMode))

    @property
    def data_bytes(self):
        return self.data.tobytes()

    @property
    def data_type(self):
        return self.data.typecode

    @property
    def index_bytes(self):
        return self.index.tobytes()

    @property
    def index_type(self):
        return self.index.typecode
