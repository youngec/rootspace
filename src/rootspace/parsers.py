#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Implements parsers for resource files."""

import array
import pyparsing as pp
import attr
from attr.validators import instance_of
import warnings
import ctypes


class FixmeWarning(Warning):
    """
    This warning is raised if something should be fixed.
    """
    pass


@attr.s
class Attribute(object):
    components = attr.ib(validator=instance_of(int))
    stride = attr.ib(validator=instance_of(int))
    start_idx = attr.ib(validator=instance_of(int))
    location = attr.ib(validator=instance_of(int))

    @property
    def stride_bytes(self):
        return self.stride * ctypes.sizeof(ctypes.c_float)

    @property
    def start_ptr(self):
        return ctypes.c_void_p(self.start_idx * ctypes.sizeof(ctypes.c_float))


@attr.s
class PositionAttribute(Attribute):
    pass


@attr.s
class TextureAttribute(Attribute):
    pass


@attr.s
class ColorAttribute(Attribute):
    pass


@attr.s
class Mesh(object):
    data = attr.ib(validator=instance_of(array.array))
    index = attr.ib(validator=instance_of(array.array))
    attributes = attr.ib(validator=instance_of(tuple))
    draw_mode = attr.ib(validator=instance_of(int))

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


@attr.s
class PlyParser(object):
    """
    Parse PLY Stanford Polygon Files
    --------------------------------

    Context free grammar:
    ply_grammar     ::= header body
    header          ::= "ply" declaration+ "end_header"
    declaration     ::= format | element | property
    format          ::= "format" format_type NUMBER
    element         ::= "element" element_type NUMBER
    property        ::= ("property" property_type IDENT) | ("property" "list" property_type property_type IDENT)
    format_type     ::= "ascii" | "binary_little_endian" | "binary_big_endian"
    element_type    ::= "vertex" | "face" | "edge" | IDENT
    property_type   ::= "char" | "uchar" | "short" | "ushort" | "int" | "uint" | "float" | "double"
    body            ::= statement+
    statement       ::= NUMBER+
    """
    grammar = attr.ib(validator=instance_of(pp.ParserElement))

    @classmethod
    def create(cls):
        """
        Create a Stanford polygon file parser (PLY).

        :return:
        """
        # Define the base patterns for parsing
        number = pp.pyparsing_common.number()
        identifier = pp.pyparsing_common.identifier()

        # Define the suppressed keywords
        start_keyword = pp.Suppress(pp.CaselessKeyword("ply"))
        stop_keyword = pp.Suppress(pp.CaselessKeyword("end_header"))
        comment_keyword = pp.Suppress(pp.CaselessKeyword("comment"))
        format_keyword = pp.Suppress(pp.CaselessKeyword("format"))
        element_keyword = pp.Suppress(pp.CaselessKeyword("element"))
        property_keyword = pp.Suppress(pp.CaselessKeyword("property"))
        list_keyword = pp.Suppress(pp.CaselessKeyword("list"))

        # Define the necessary keywords
        def keyword_or(*keywords):
            if isinstance(keywords[0], dict):
                return pp.Or(pp.CaselessKeyword(l).addParseAction(pp.replaceWith(d)) for l, d in keywords[0].items())
            else:
                return pp.Or(pp.CaselessKeyword(literal) for literal in keywords)

        warnings.warn("Currently does not parse binary PLY files!", FixmeWarning)
        # format_type = keyword_or("ascii", "binary_little_endian", "binary_big_endian")
        format_type = keyword_or("ascii")
        property_type = keyword_or({
            "char": "b",
            "uchar": "B",
            "short": "h",
            "ushort": "H",
            "int": "i",
            "uint": "I",
            "float": "f",
            "double": "d",
            "int8": "b",
            "uint8": "B",
            "int16": "h",
            "uint16": "H",
            "int32": "i",
            "uint32": "I",
            "float32": "f",
            "float64": "d"
        })

        # Define the grammar of statements
        comment_expr = pp.Group(
            comment_keyword +
            pp.restOfLine
        )("comment")

        format_expr = pp.Group(
            format_keyword +
            format_type("file_type") +
            number("version")
        )("format")

        property_simple_prefix = property_keyword + property_type("data_type")
        property_list_prefix = property_keyword + list_keyword + property_type("index_type") + property_type("data_type")

        property_simple_general = pp.Group(
            property_simple_prefix + identifier("name")
        )
        property_position = pp.Group(
            pp.Group(property_simple_prefix + keyword_or("x")("name")) +
            pp.Group(property_simple_prefix + keyword_or("y")("name")) +
            pp.Group(property_simple_prefix + keyword_or("z")("name"))
        )("position")
        property_color = pp.Group(
            pp.Group(property_simple_prefix + keyword_or("r", "red")("name")) +
            pp.Group(property_simple_prefix + keyword_or("g", "green")("name")) +
            pp.Group(property_simple_prefix + keyword_or("b", "blue")("name")) +
            pp.Group(property_simple_prefix + keyword_or("a", "alpha")("name"))
        )("color")
        property_ambient_color = pp.Group(
            pp.Group(property_simple_prefix + keyword_or("ambient_red")("name")) +
            pp.Group(property_simple_prefix + keyword_or("ambient_green")("name")) +
            pp.Group(property_simple_prefix + keyword_or("ambient_blue")("name")) +
            pp.Group(property_simple_prefix + keyword_or("ambient_alpha")("name"))
        )("ambient_color")
        property_diffuse_color = pp.Group(
            pp.Group(property_simple_prefix + keyword_or("diffuse_red")("name")) +
            pp.Group(property_simple_prefix + keyword_or("diffuse_green")("name")) +
            pp.Group(property_simple_prefix + keyword_or("diffuse_blue")("name"))+
            pp.Group(property_simple_prefix + keyword_or("diffuse_alpha")("name"))
        )("diffuse_color")
        property_specular_color = pp.Group(
            pp.Group(property_simple_prefix + keyword_or("specular_red")("name")) +
            pp.Group(property_simple_prefix + keyword_or("specular_green")("name")) +
            pp.Group(property_simple_prefix + keyword_or("specular_blue")("name")) +
            pp.Group(property_simple_prefix + keyword_or("specular_alpha")("name"))
        )("specular_color")
        property_texture = pp.Group(
            pp.Group(property_simple_prefix + keyword_or("s", "u", "tx")("name")) +
            pp.Group(property_simple_prefix + keyword_or("t", "v", "ty")("name"))
        )("texture")
        property_normal = pp.Group(
           pp.Group(property_simple_prefix + keyword_or("nx")("name")) +
           pp.Group(property_simple_prefix + keyword_or("ny")("name")) +
           pp.Group(property_simple_prefix + keyword_or("nz")("name"))
        )("normal")
        property_specular_power = pp.Group(
            property_simple_prefix + keyword_or("specular_power")("name")
        )("specular_power")
        property_opacity = pp.Group(
            property_simple_prefix + keyword_or("opacity")("name")
        )("opacity")

        property_list_general = pp.Group(
            property_list_prefix + identifier("name")
        )
        property_vertex_index = pp.Group(
            property_list_prefix + keyword_or("vertex_index", "vertex_indices")("name")
        )("vertex_index")
        property_material_index = pp.Group(
            property_list_prefix + keyword_or("material_index", "material_indices")("name")
        )("material_index")

        element_vertex = pp.Group(
            element_keyword + keyword_or("vertex")("name") + number("count") +
            pp.Group(
                pp.OneOrMore(
                    property_position | property_color | property_ambient_color | property_diffuse_color |
                    property_specular_color | property_texture | property_normal | property_specular_power |
                    property_opacity | property_simple_general
                )
            )("properties")
        )

        element_face = pp.Group(
            element_keyword + keyword_or("face")("name") + number("count") +
            pp.Group(property_vertex_index | property_list_general)("properties")
        )

        element_edge = pp.Group(
            element_keyword + keyword_or("edge")("name") + number("count") +
            pp.Group(
                pp.OneOrMore(property_color | property_simple_general)
            )("properties")
        )

        element_general = pp.Group(
            element_keyword + identifier("name") + number("count") +
            pp.Group(
                pp.OneOrMore(property_simple_general) | property_list_general
            )("properties")
        )

        element_group = element_vertex | element_face | element_edge | element_general

        declarations = pp.Group(
            format_expr +
            pp.Group(
                pp.OneOrMore(element_group)
            )("elements")
        )("declarations")

        header = start_keyword + declarations + stop_keyword

        body = pp.Forward()("data")

        ply_grammar = (header + body).ignore(comment_expr)

        # Define the grammar of the body based on the header data
        def construct_body_expr(source, location, tokens):
            body_expr = list()
            for el_decl in tokens.declarations.elements:
                props = el_decl.properties
                if len(props) == 1 and "index_type" in props[0]:
                    element = pp.countedArray(number)
                else:
                    sequences = list()
                    for prop in props:
                        if "name" in prop:
                            sequences.append(number(prop.name))
                        else:
                            for variable in prop:
                                sequences.append(number(variable.name))
                    element = pp.Group(pp.And(sequences))

                body_expr.append(pp.Group(element * el_decl.count)(el_decl.name))

            body << pp.And(body_expr)

        header.addParseAction(construct_body_expr)

        return cls(ply_grammar)

    def tokenize(self, data):
        """
        Parse the supplied data into a token tree.

        :param data:
        :return:
        """
        try:
            return self.grammar.parseString(data)
        except pp.ParseException as e:
            print(e.line)
            print(" " * (e.column - 1) + "^")
            print(e)

    def parse(self, data):
        """
        Parse the supplied data into a model.

        :param data:
        :return:
        """
        tokens = self.tokenize(data)

        # Determine the data types
        candidate_types = list()
        for element in tokens.declarations.elements:
            if element.name == "vertex":
                for property in element.properties:
                    if "name" in property:
                        candidate_types.append(property.data_type)
                    else:
                        for variable in property:
                            candidate_types.append(variable.data_type)

        data_type_ordering = ("b", "B", "h", "H", "i", "I", "f", "d")
        vertex_data_type = max(candidate_types, key=lambda e: data_type_ordering.index(e))

        index_data_type = "I"
        for element in tokens.declarations.elements:
            if element.name == "face":
                index_data_type = element.properties[0].data_type
        if index_data_type not in ("B", "H", "I"):
            index_data_type = "I"

        # Store the raw data
        vertex_data = array.array(vertex_data_type, (value for vertex in tokens.data.vertex for value in vertex))
        index_data = array.array(index_data_type, (value for face in tokens.data.face for value in face))

        # Determine the attributes
        warnings.warn("Vertex Attributes are not initialized correctly", FixmeWarning)
        vertex_attributes = list()
        for element in tokens.declarations.elements:
            if element.name == "vertex":
                for name, property in element.properties.items():
                    num_components = len(property)
                    if name == "position":
                        vertex_attributes.append(PositionAttribute(
                            num_components, 0, 0, 0
                        ))
                    elif name == "color":
                        vertex_attributes.append(ColorAttribute(
                            num_components, 0, 0, 0
                        ))
                    elif name == "texture":
                        vertex_attributes.append(TextureAttribute(
                            num_components, 0, 0, 0
                        ))

        return Mesh(
            data=vertex_data,
            index=index_data,
            attributes=tuple(vertex_attributes),
            draw_mode=4
        )


def main():
    data = """ply
format ascii 1.0
comment author: Greg Turk and Eleanore Young
comment object: a cube
element vertex 8
property float x
property float y
property float z
property uchar red
property uchar green
property uchar blue
property uchar alpha
property float s
property float t
element face 7
property list uchar int vertex_index
element edge 5
property int vertex1
property int vertex2
property uchar red
property uchar green
property uchar blue
property uchar alpha
end_header
0 0 0 255 0 0 255 0 0
0 0 1 255 0 0 255 0 1
0 1 1 255 0 0 255 0 0
0 1 0 255 0 0 255 0 1
1 0 0 0 0 255 255 1 0
1 0 1 0 0 255 255 1 1
1 1 1 0 0 255 255 0 0
1 1 0 0 0 255 255 0 0
3 0 1 2
3 0 2 3
4 7 6 5 4
4 0 4 5 1
4 1 5 6 2
4 2 6 7 3
4 3 7 4 0
0 1 255 255 255 255
1 2 255 255 255 255
2 3 255 255 255 255
3 0 255 255 255 255
2 0 0 0 0 255"""

    parser = PlyParser.create()
    tokens = parser.tokenize(data)
    print(parser.parse(data))
    # print(tokens.dump())


if __name__ == "__main__":
    main()
