#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Implements parsers for resource files."""

import typing
import array
import pyparsing as pp
import attr
from attr.validators import instance_of
import warnings

from .exceptions import FixmeWarning


@attr.s
class Mesh(object):
    vertices = attr.ib()
    faces = attr.ib()
    edges = attr.ib()
    other = attr.ib(default=attr.Factory(dict), validator=instance_of(dict))

    def __getattr__(self, item):
        if item in self.other:
            return self.other[item]
        else:
            raise AttributeError("No attribute named '{}'.".format(item))


@attr.s
class Material(object):
    pass


@attr.s
class Texture(object):
    pass


@attr.s
class Model(object):
    meshes = attr.ib(validator=instance_of(typing.List[Mesh]))
    materials = attr.ib(validator=instance_of(typing.List[Material]))
    textures = attr.ib(validator=instance_of(typing.List[Texture]))


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
        # format_types = ("ascii", "binary_little_endian", "binary_big_endian")
        format_type = keyword_or("ascii")
        element_type = keyword_or("vertex", "face", "edge") | identifier
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
        property_position = keyword_or("x", "y", "z")
        property_color = keyword_or("r", "g", "b", "a", "red", "green", "blue", "alpha")
        property_ambient_color = keyword_or("ambient_red", "ambient_green", "ambient_blue", "ambient_alpha")
        property_diffuse_color = keyword_or("diffuse_red", "diffuse_green", "diffuse_blue", "diffuse_alpha")
        property_specular_color = keyword_or("specular_red", "specular_green", "specular_blue", "specular_alpha")
        property_texture = keyword_or("s", "t", "u", "v", "tx", "ty")
        property_normal = keyword_or("nx", "ny", "nz")
        property_vertex_index = keyword_or("vertex_index", "vertex_indices")
        property_material_index = keyword_or("material_index", "material_indices")
        property_specular_power = keyword_or("specular_power")
        property_opacity = keyword_or("opacity")

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

        property_simple_expr = pp.Group(
            property_keyword +
            property_type("data_type") +
            identifier("name")
        )

        property_list_expr = pp.Group(
            property_keyword + list_keyword +
            property_type("index_type") +
            property_type("data_type") +
            identifier("name")
        )

        element_expr = element_keyword + element_type("type") + number("count")

        # Define the grammar of statement groups
        element_group = pp.Group(
            element_expr +
            pp.Group(
                pp.OneOrMore(property_simple_expr) | property_list_expr
            )("properties")
        )

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
                    element = pp.Group(
                        pp.And(number(p.name) for p in props)
                    )

                body_expr.append(pp.Group(element * el_decl.count)(el_decl.type))

            body << pp.And(body_expr)

        header.addParseAction(construct_body_expr)

        return cls(ply_grammar)

    def tokenize(self, data):
        """
        Parse the supplied data into a token tree.

        :param data:
        :return:
        """
        return self.grammar.parseString(data)

    def parse(self, data):
        """
        Parse the supplied data into a model.

        :param data:
        :return:
        """
        tokens = self.tokenize(data)


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

    try:
        parser = PlyParser.create()
        model = parser.tokenize(data)
        print(model)
    except pp.ParseException as e:
        print(e.line)
        print(" " * (e.column - 1) + "^")
        print(e)


if __name__ == "__main__":
    main()
