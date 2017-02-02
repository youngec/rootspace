#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Implements parsers for resource files."""

import array
import pathlib
import mmap
import struct
import enum

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
    Ignore all "comment" statements.
    ply_grammar      ::= header body
    header           ::= "ply" format element_group+ "end_header"
    num_el_grp       ::= [number of element_group occurrences]
    element_group    ::= element property+
    num_el_prop      ::= [number of property occurrences for the parent element]
    format           ::= "format" format_type format_version
    element          ::= "element" element_type element_count
    property         ::= property_simple | property_list
    property_simple  ::= "property" property_type prop_simple_name
    property_list    ::= "property" "list" property_type property_type prop_list_name
    format_type      ::= "ascii" | "binary_little_endian" | "binary_big_endian"
    element_type     ::= "vertex" | "face" | "edge" | IDENT
    property_type    ::= "char" | "uchar" | "short" | "ushort" | "int" | "uint" | "float" | "double"
    prop_simple_name ::= "x" | "y" | "z" | [many more] | IDENT
    prop_list_name   ::= "vertex_index" | "material_index" | IDENT
    format_version   ::= FLOAT_NUMBER
    element_count    ::= INT_NUMBER

    body             ::= el_data_group * num_el_grp
    el_data_group    ::= prp_data_group * element_count
    prp_data_group   ::= (prop_simple_data | prop_list_data) * num_el_prop
    prop_simple_data ::= NUMBER
    prop_list_data   ::= list_length (NUMBER * list_length)
    list_length      ::= NUMBER
    """
    header_grammar = attr.ib(validator=instance_of(pp.ParserElement))

    class FormatType(enum.Enum):
        ASCII = 0
        BINARY_LE = 1
        BINARY_BE = 2

    begin_header = "ply"
    end_header = "end_header"
    format_type_map = {
        "ascii": FormatType.ASCII,
        "binary_little_endian": FormatType.BINARY_LE,
        "binary_big_endian": FormatType.BINARY_BE
    }
    byte_order_map = {
        FormatType.ASCII: "=",
        FormatType.BINARY_LE: "<",
        FormatType.BINARY_BE: ">"
    }
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
    data_type_sizes = {
        "b": 1,
        "B": 1,
        "h": 2,
        "H": 2,
        "i": 4,
        "I": 4,
        "f": 4,
        "d": 8
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
        real = pp.pyparsing_common.real()
        integer = pp.pyparsing_common.integer()
        identifier = pp.pyparsing_common.identifier()

        # Define the suppressed keywords
        start_keyword = pp.Suppress(pp.CaselessKeyword(cls.begin_header))
        stop_keyword = pp.Suppress(pp.CaselessKeyword(cls.end_header))
        comment_keyword = pp.Suppress(pp.CaselessKeyword("comment"))
        format_keyword = pp.Suppress(pp.CaselessKeyword("format"))
        element_keyword = pp.Suppress(pp.CaselessKeyword("element"))
        property_keyword = pp.Suppress(pp.CaselessKeyword("property"))
        list_keyword = pp.Suppress(pp.CaselessKeyword("list"))

        # Define the necessary keywords
        def keyword_or(*keywords):
            if isinstance(keywords[0], dict):
                return pp.MatchFirst(
                    pp.CaselessKeyword(l).addParseAction(pp.replaceWith(d)) for l, d in keywords[0].items()
                )
            else:
                return pp.MatchFirst(pp.CaselessKeyword(literal) for literal in keywords)

        format_type = keyword_or(cls.format_type_map)
        property_type = keyword_or(cls.data_type_map)

        # Define the grammar of statements
        comment_expr = comment_keyword + pp.restOfLine

        format_expr = pp.Group(
            format_keyword +
            format_type("file_type") +
            real("version")
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
            element_keyword + keyword_or("vertex")("name") + integer("count") +
            pp.Group(
                pp.OneOrMore(
                    property_position | property_color | property_ambient_color | property_diffuse_color |
                    property_specular_color | property_texture | property_normal | property_specular_power |
                    property_opacity | property_simple_general
                )
            )("properties")
        )

        element_face = pp.Group(
            element_keyword + keyword_or("face")("name") + integer("count") +
            pp.Group(property_vertex_index | property_list_general)("properties")
        )

        element_edge = pp.Group(
            element_keyword + keyword_or("edge")("name") + integer("count") +
            pp.Group(
                pp.OneOrMore(property_color | property_simple_general)
            )("properties")
        )

        element_general = pp.Group(
            element_keyword + identifier("name") + integer("count") +
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

        header_grammar = header.ignore(comment_expr)

        return cls(header_grammar)

    def tokenize_header(self, header_data):
        """
        Tokenize the header portion of the PLY file.

        :param header_data:
        :return:
        """
        return self.header_grammar.parseString(header_data, parseAll=True)

    def parse(self, file_object):
        """
        Parse the supplied data into a model.

        :param data:
        :return:
        """
        # Separate the header and the body portion
        with mmap.mmap(file_object.fileno(), 0, access=mmap.ACCESS_READ) as file_mmap:
            # Read and tokenize the header portion
            header_data = self._extract_header(file_mmap, advance_idx=True)
            tokens = self.tokenize_header(header_data)

            # Determine the data types
            vertex_data_type = self._get_vertex_data_type(tokens)
            index_data_type = self._get_index_data_type(tokens)

            # Determine the attributes
            vertex_attributes = self._get_vertex_attributes(tokens, vertex_data_type)

            # Parse the data of the PLY file
            if tokens.declarations.format.file_type == self.FormatType.ASCII:
                vertex_data, index_data = self._parse_ascii_data(tokens, file_mmap, vertex_data_type, index_data_type)
            else:
                vertex_data, index_data = self._parse_binary_data(tokens, file_mmap, vertex_data_type, index_data_type)

            # Store the raw data as array
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
            with open(file, "rb")as f:
                return self.parse(f)
        elif isinstance(file, pathlib.Path):
            with file.open("rb") as f:
                return self.parse(f)
        elif hasattr(file, "mode") and "b" in file.mode:
            return self.parse(file)
        else:
            raise TypeError("The 'file' parameter must be either a path to a file, a pathlib.Path object, "
                            "or a binary file object.")

    def _extract_header(self, file_mmap, advance_idx=True):
        """
        Given a memory map of a file object, search for a valid PLY header and return the data as a string.
        Optionally advance the memory mapped file index to just after the header.

        :param file_mmap:
        :param advance_idx:
        :return:
        """
        # Find the indices of the header beginning and end
        begin_idx = file_mmap.find(self.begin_header.encode("ascii"))
        end_idx = file_mmap.find(self.end_header.encode("ascii"))
        if begin_idx != 0 or end_idx == -1:
            raise ValueError("Could not find a valid PLY header portion in the submitted file.")

        # Extract the header data
        header_data = file_mmap[begin_idx:end_idx + len(self.end_header)].decode("ascii")

        # Advance the memory map pointer to just after the header
        if advance_idx:
            file_mmap.seek(end_idx + len(self.end_header))

        return header_data

    def _get_vertex_data_type(self, token_tree, element_name="vertex"):
        """
        Return the aggregate data type for the vertex data.

        :param token_tree:
        :param element_name:
        :return:
        """
        candidate_types = list()
        for el in token_tree.declarations.elements:
            if el.name == element_name:
                for prop in el.properties:
                    if "name" in prop:
                        candidate_types.append(prop.data_type)
                    else:
                        for variable in prop:
                            candidate_types.append(variable.data_type)

        return max(candidate_types, key=lambda e: self.data_type_precedence.index(e))

    def _get_index_data_type(self, token_tree, element_name="face"):
        """
        Return the aggregate data type for the vertex index data.

        :param token_tree:
        :param element_name:
        :return:
        """
        for el in token_tree.declarations.elements:
            if el.name == element_name:
                candidate_type = el.properties[0].data_type
                if candidate_type in self.allowed_index_types:
                    return candidate_type
                else:
                    return self.default_index_type

        return self.default_index_type

    def _get_vertex_attributes(self, header_tokens, vertex_data_type):
        """
        From the header tokens, extract a tuple of Attribute instances that describe the vertex data.

        :param header_tokens:
        :param vertex_data_type:
        :return:
        """
        vertex_attributes = list()
        start_index = 0
        for element in header_tokens.declarations.elements:
            if element.name == "vertex":
                stride = sum(len(prop) for name, prop in element.properties.items())
                for name, prop in element.properties.items():
                    vertex_attributes.append(Attribute(
                        name, vertex_data_type, len(prop), stride, start_index
                    ))
                    start_index += len(prop)

        return tuple(vertex_attributes)

    def _parse_ascii_data(self, header_tokens, file_mmap, vertex_data_type, index_data_type):
        """
        Parse the data portion of a PLY file assuming it uses ASCII format.

        :param header_tokens:
        :param file_mmap:
        :param vertex_data_type:
        :param index_data_type:
        :return:
        """
        # Define the grammar of the body
        number = pp.pyparsing_common.number()
        body_expr = list()
        for el_decl in header_tokens.declarations.elements:
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

        ascii_grammar = pp.And(body_expr)

        # Load the body data into a string
        body_data = file_mmap[file_mmap.tell():].decode("ascii")

        # Tokenize the body data
        body_tokens = ascii_grammar.parseString(body_data, parseAll=True)

        # Convert the data to arrays.
        vertex_data = array.array(vertex_data_type, (value for vertex in body_tokens.vertex for value in vertex))
        index_data = array.array(index_data_type, (value for face in body_tokens.face for value in face))

        return vertex_data, index_data

    def _parse_binary_data(self, header_tokens, file_mmap, vertex_data_type, index_data_type):
        """
        Parse the data portion of a PLY file assuming it uses one of the two binary formats.

        :param header_tokens:
        :param file_mmap:
        :param vertex_data_type:
        :param index_data_type:
        :return:
        """
        # Determine the byte order of the data
        byte_order = self.byte_order_map[header_tokens.declarations.format.file_type]

        # Get the vertex element, the data types, and the total size in bytes
        vertex_element = next(e for e in header_tokens.declarations.elements if e.name == "vertex")
        vertex_data_types = vertex_element.count * [p.data_type for g in vertex_element.properties for p in g]
        vertex_bytes = sum(self.data_type_sizes[t] for t in vertex_data_types)

        # Parse the data into an array
        vertex_data_iter = struct.iter_unpack(byte_order + "".join(vertex_data_types), file_mmap.read(vertex_bytes))
        vertex_data = array.array(vertex_data_type, vertex_data_iter)

        # Get the index element
        index_data = array.array(index_data_type, (0,))

        return vertex_data, index_data
