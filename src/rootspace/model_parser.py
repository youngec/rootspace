#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Implements parsers for resource files."""

import array
import pathlib

import attr
import pyparsing as pp
from attr.validators import instance_of

from .data_abstractions import Attribute, Mesh


@attr.s
class PlyParser(object):
    """
    Parse PLY Stanford Polygon Files
    --------------------------------
    As of yet, the parser does not handle the binary file formats!

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

    data_type_map = {
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
    }
    data_type_precedence = ("b", "B", "h", "H", "i", "I", "f", "d")
    allowed_index_types = ("B", "H", "I")
    default_index_type = "I"

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

        # format_type = keyword_or("ascii", "binary_little_endian", "binary_big_endian")
        format_type = keyword_or("ascii")
        property_type = keyword_or(cls.data_type_map)

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

        # Properties and Elements are sadly much more complex.
        property_simple_prefix = property_keyword + property_type("data_type")
        property_list_prefix = property_keyword + list_keyword + property_type("index_type") + \
                               property_type("data_type")

        def aggregate_property(name, *keyword_group):
            aggregates = list()
            for keywords in keyword_group:
                aggregates.append(pp.Group(property_simple_prefix + keyword_or(*keywords)("name")))

            return pp.Group(pp.And(aggregates))(name)

        property_simple_general = pp.Group(
            property_simple_prefix + identifier("name")
        )
        property_position = aggregate_property("position", "x", "y", "z")
        property_color = aggregate_property("color", ("r", "red"), ("g", "green"), ("b", "blue"), ("a", "alpha"))
        property_ambient_color = aggregate_property(
            "ambient_color", "ambient_red", "ambient_green", "ambient_blue", "ambient_alpha"
        )
        property_diffuse_color = aggregate_property(
            "diffuse_color", "diffuse_red", "diffuse_green", "diffuse_blue", "diffuse_alpha"
        )
        property_specular_color = aggregate_property(
            "specular_color", "specular_red", "specular_green", "specular_blue", "specular_alpha"
        )
        property_texture = aggregate_property("texture", ("s", "u", "tx"), ("t", "v", "ty"))
        property_normal = aggregate_property("normal", "nx", "ny", "nz")

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
        # property_material_index = pp.Group(
        #     property_list_prefix + keyword_or("material_index", "material_indices")("name")
        # )("material_index")

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
            file_type = tokens.declarations.format.file_type
            if file_type == "ascii":
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
            elif file_type == "binary_little_endian":
                raise NotImplementedError("Cannot properly parse binary little endian files yet.")
            elif file_type == "binary_big_endian":
                raise NotImplementedError("Cannot properly parse binary big endian files yet.")
            else:
                raise ValueError("Unknown file type '{}'. This should have been caught earlier!".format(file_type))

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

        def get_vertex_data_type(token_tree):
            candidate_types = list()
            for el in token_tree.declarations.elements:
                if el.name == "vertex":
                    for prop in el.properties:
                        if "name" in prop:
                            candidate_types.append(prop.data_type)
                        else:
                            for variable in prop:
                                candidate_types.append(variable.data_type)

            return max(candidate_types, key=lambda e: self.data_type_precedence.index(e))

        def get_index_data_type(token_tree):
            for el in token_tree.declarations.elements:
                if el.name == "face":
                    candidate_type = el.properties[0].data_type
                    if candidate_type in self.allowed_index_types:
                        return candidate_type
                    else:
                        return self.default_index_type

            return self.default_index_type

        # Tokenize the input data
        tokens = self.tokenize(data)

        # Determine the data types
        vertex_data_type = get_vertex_data_type(tokens)
        index_data_type = get_index_data_type(tokens)

        # Store the raw data as array
        vertex_data = array.array(vertex_data_type, (value for vertex in tokens.data.vertex for value in vertex))
        index_data = array.array(index_data_type, (value for face in tokens.data.face for value in face))

        # Determine the attributes
        vertex_attributes = list()
        start_index = 0
        for element in tokens.declarations.elements:
            if element.name == "vertex":
                stride = sum(len(prop) for name, prop in element.properties.items())
                for name, prop in element.properties.items():
                    vertex_attributes.append(Attribute(
                        name, vertex_data_type, len(prop), stride, start_index
                    ))
                    start_index += len(prop)

        return Mesh(
            data=vertex_data,
            index=index_data,
            attributes=vertex_attributes,
            draw_mode=Mesh.DrawMode.Triangles
        )

    def load(self, file):
        """
        Load the supplied ply file as Model.

        :param file:
        :return:
        """
        if isinstance(file, (str, bytes)):
            with open(file, "r")as f:
                return self.parse(f.read())
        elif isinstance(file, pathlib.Path):
            with file.open("r") as f:
                return self.parse(f.read())
        elif hasattr(file, "mode") and "t" in file.mode:
            return self.parse(file.read())
        else:
            raise TypeError("The 'file' parameter must be either a path to a file, a pathlib.Path object, "
                            "or a text file object.")
