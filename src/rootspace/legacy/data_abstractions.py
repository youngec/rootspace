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
import PIL.Image
from OpenGL.GL import GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, GL_LESS, GL_CCW, GL_BACK
from attr.validators import instance_of, optional

from .utilities import iterable_of, underscore_to_camelcase
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
class Attribute(object):
    """
    An Attribute defines the parameters necessary for the graphics library to read data from the vertex buffer.
    """

    class Type(enum.Enum):
        Position = 0
        Color = 1
        Texture = 2
        Normal = 3
        AmbientColor = 4
        DiffuseColor = 5
        SpecularColor = 6
        Power = 7
        Opacity = 8

        @classmethod
        def coerce(cls, type_value):
            if isinstance(type_value, cls):
                return type_value
            elif isinstance(type_value, str):
                try:
                    return cls[underscore_to_camelcase(type_value)]
                except KeyError:
                    raise KeyError("No equivalent enum for '{}'.".format(type_value))
            else:
                raise KeyError("No equivalent enum for '{}'.".format(type_value))

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

    data = attr.ib(validator=instance_of(array.array), repr=False)
    index = attr.ib(validator=instance_of(array.array), repr=False)
    attributes = attr.ib(validator=instance_of(tuple), convert=tuple)
    draw_mode = attr.ib(validator=instance_of(DrawMode))
    vertex_shader = attr.ib(default=None, validator=optional(instance_of(str)))
    fragment_shader = attr.ib(default=None, validator=optional(instance_of(str)))
    texture = attr.ib(default=None, validator=optional(instance_of(PIL.Image.Image)))
    comments = attr.ib(default=None, validator=optional(instance_of(tuple)))

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

    @property
    def requires_texture(self):
        return any(a.type == Attribute.Type.Texture for a in self.attributes)
