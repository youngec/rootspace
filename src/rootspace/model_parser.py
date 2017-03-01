#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Implements parsers for resource files."""

import array
import pathlib
import mmap
import struct
import enum

import attr
from attr.validators import instance_of
from pyparsing import pyparsing_common, ParserElement, Group, And, MatchFirst, CaselessKeyword, Optional, \
    OneOrMore, replaceWith, Suppress, countedArray, ParseResults, Word, printables, ZeroOrMore, alphanums, NotAny

from .data_abstractions import Attribute, Mesh


@attr.s
class PlyParser(object):
    """
    Parse PLY Stanford Polygon Files
    --------------------------------
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
    header_grammar = attr.ib(validator=instance_of(ParserElement))

    class FormatType(enum.Enum):
        ASCII = 0
        BINARY_LE = 1
        BINARY_BE = 2

    begin_header_keyword = "ply"
    end_header_keyword = "end_header"
    comment_keyword = "comment"
    format_keyword = "format"
    element_keyword = "element"
    property_keyword = "property"
    list_keyword = "list"

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
        real = pyparsing_common.real()
        integer = pyparsing_common.integer()

        # Define how the header portion begins and ends
        start_keyword = cls._or(cls.begin_header_keyword, suppress=True)
        stop_keyword = cls._or(cls.end_header_keyword, suppress=True)

        # Define the grammar of a comment statement
        comment_keyword = cls._or(cls.comment_keyword, suppress=True)
        vertex_shader_comment = Group(comment_keyword + Suppress(CaselessKeyword("VertexShaderFile")) + Word(alphanums + ".-_"))("vertex_shader_file")
        fragment_shader_comment = Group(comment_keyword + Suppress(CaselessKeyword("FragmentShaderFile")) + Word(alphanums + ".-_"))("fragment_shader_file")
        texture_comment = Group(comment_keyword + Suppress(CaselessKeyword("TextureFile")) + Word(alphanums + ".-_"))("texture_file")
        other_comment = comment_keyword + NotAny("TextureFile") + Word(printables + " ")

        # Define the grammar of a format statement
        format_keyword = cls._or(cls.format_keyword, suppress=True)
        format_type = cls._or(cls.format_type_map)
        format_expr = Group(
            format_keyword +
            format_type("file_type") +
            real("version")
        )("format")

        # Define the grammar of properties
        property_keyword = cls._or(cls.property_keyword, suppress=True)
        list_keyword = cls._or(cls.list_keyword, suppress=True)
        property_type = cls._or(cls.data_type_map)
        psp = property_keyword + property_type("data_type")

        position_keywords = [cls._or(k) for k in ("x", "y", "z")]
        property_position = cls._aggregate_property("position", psp, *position_keywords)

        property_color = Group(And([
            Group(psp + MatchFirst((CaselessKeyword("r"), CaselessKeyword("red")))("name")),
            Group(psp + MatchFirst((CaselessKeyword("g"), CaselessKeyword("green")))("name")),
            Group(psp + MatchFirst((CaselessKeyword("b"), CaselessKeyword("blue")))("name")),
            Optional(Group(psp + MatchFirst((CaselessKeyword("a"), CaselessKeyword("alpha")))("name")),)
        ]))("color")

        ambient_keywords = [cls._or(k) for k in ("ambient_red", "ambient_green", "ambient_blue", "ambient_alpha")]
        property_ambient_color = cls._aggregate_property("ambient_color", psp, *ambient_keywords)

        diffuse_keywords = [cls._or(k) for k in ("diffuse_red", "diffuse_green", "diffuse_blue", "diffuse_alpha")]
        property_diffuse_color = cls._aggregate_property("diffuse_color", psp, *diffuse_keywords)

        specular_keywords = [cls._or(k) for k in ("specular_red", "specular_green", "specular_blue", "specular_alpha")]
        property_specular_color = cls._aggregate_property("specular_color", psp, *specular_keywords)

        texture_keywords = [cls._or(*k) for k in (("s", "u", "tx"), ("t", "v", "ty"))]
        property_texture = cls._aggregate_property("texture", psp, *texture_keywords)

        normal_keywords = [cls._or(k) for k in ("nx", "ny", "nz")]
        property_normal = cls._aggregate_property("normal", psp, *normal_keywords)

        power_keywords = [CaselessKeyword("specular_power")]
        property_specular_power = cls._aggregate_property("specular_power", psp, *power_keywords)

        opacity_keywords = [CaselessKeyword("opacity")]
        property_opacity = cls._aggregate_property("opacity", psp, *opacity_keywords)

        plp = property_keyword + list_keyword + property_type("index_type") + property_type("data_type")

        vertex_index_keywords = [cls._or("vertex_index", "vertex_indices")]
        property_vertex_index = cls._aggregate_property("vertex_index", plp, *vertex_index_keywords)

        material_index_keywords = [cls._or("material_index", "material_indices")]
        property_material_index = cls._aggregate_property("material_index", plp, *material_index_keywords)

        # Define the grammar of elements
        element_keyword = cls._or(cls.element_keyword, suppress=True)

        element_vertex = Group(
            element_keyword + CaselessKeyword("vertex")("name") + integer("count") +
            Group(
                OneOrMore(
                    property_position | property_color | property_ambient_color | property_diffuse_color |
                    property_specular_color | property_texture | property_normal | property_specular_power |
                    property_opacity
                )
            )("properties")
        )

        element_face = Group(
            element_keyword + CaselessKeyword("face")("name") + integer("count") +
            Group(property_vertex_index | property_material_index)("properties")
        )

        element_group = element_vertex | element_face

        declarations = format_expr + \
                       Group(ZeroOrMore(vertex_shader_comment | fragment_shader_comment | texture_comment | other_comment))("comments") + \
                       Group(OneOrMore(element_group))("elements")

        header_grammar = start_keyword + declarations + stop_keyword

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
        Parse the supplied file object as PLY file and return a Mesh data abstraction object.

        :param file_object:
        :return:
        """
        # Separate the header and the body portion
        with mmap.mmap(file_object.fileno(), 0, access=mmap.ACCESS_READ) as file_mmap:
            # Read and tokenize the header portion
            header_data, data_start_idx = self._extract_header(file_mmap)
            tokens = self.tokenize_header(header_data)

            # Extract the comments
            if "comments" in tokens:
                comments = list()
                vertex_shader_file = None
                fragment_shader_file = None
                texture_file = None
                for comment in tokens.comments:
                    if isinstance(comment, str):
                        comments.append(comment)
                    else:
                        if comment.getName() == "vertex_shader_file":
                            vertex_shader_file = comment[0]
                        elif comment.getName() == "fragment_shader_file":
                            fragment_shader_file = comment[0]
                        elif comment.getName() == "texture_file":
                            texture_file = comment[0]
                        else:
                            raise ValueError("Unkown ParseResult: '{}'.".format(comment))
                comments = tuple(comments)
            else:
                comments = ()
                vertex_shader_file = None
                fragment_shader_file = None
                texture_file = None

            # Determine the data types
            aggregate_data_types = {
                "vertex": self._get_array_type(tokens, "vertex", "f"),
                "face": self._get_array_type(tokens, "face", self.default_index_type, self.allowed_index_types)
            }

            # Determine the attributes
            vertex_attributes = self._get_vertex_attributes(tokens, aggregate_data_types["vertex"])

            # Parse the data of the PLY file
            if tokens.format.file_type == self.FormatType.ASCII:
                element_data = self._parse_ascii_data(tokens, file_mmap, data_start_idx, aggregate_data_types)
            else:
                element_data = self._parse_binary_data(tokens, file_mmap, data_start_idx, aggregate_data_types)

            # Store the raw data as array
            return Mesh(
                data=element_data["vertex"],
                index=element_data["face"],
                attributes=vertex_attributes,
                draw_mode=Mesh.DrawMode.Triangles,
                vertex_shader_file=vertex_shader_file,
                fragment_shader_file=fragment_shader_file,
                texture_file=texture_file,
                comments=tuple(comments)
            )

    def load(self, file):
        """
        Load the supplied file as PLY file into a Mesh data abstraction object.

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

    @classmethod
    def _or(cls, *literals, suppress=False):
        """
        Return a MatchFirst aggregation of CaselessKeyword literals based on the supplied iterable of strings.
        If the supplied iterable is a dictionary, replace the keys with the values as a pyparsing parse action.
        If suppress is True, wrap the output in a Suppress object.

        :param literals:
        :param suppress:
        :return:
        """
        if isinstance(literals[0], dict):
            keywords = (CaselessKeyword(l).addParseAction(replaceWith(d)) for l, d in literals[0].items())
        else:
            keywords = (CaselessKeyword(literal) for literal in literals)

        match_first = MatchFirst(keywords)

        if suppress:
            return Suppress(match_first)
        else:
            return match_first

    @classmethod
    def _aggregate_property(cls, name, prefix, *keywords):
        """
        Create a property group from the specified name,
        the pattern prefix (a ParseElement instance), and an iterable of keywords.

        Example:
        aggregate_property('position', CaselessKeyword('property'), *[CaselessKeyword('x'), ...])

        :param name:
        :param prefix:
        :param keywords:
        :return:
        """
        aggregates = list()
        for keyword in keywords:
            aggregates.append(Group(prefix + keyword("name")))

        return Group(And(aggregates))(name)

    def _extract_header(self, file_mmap):
        """
        Given a memory map of a file object, search for a valid PLY header and return the header as a string.

        :param file_mmap:
        :return:
        """
        # Find the indices of the header beginning and end
        begin_idx = file_mmap.find(self.begin_header_keyword.encode("ascii"))
        end_idx = file_mmap.find(self.end_header_keyword.encode("ascii"))
        if begin_idx != 0 or end_idx == -1:
            raise ValueError("Could not find a valid PLY header portion in the submitted file.")

        # Adjust the header end index to after the keyword
        end_idx += len(self.end_header_keyword)

        # Also correct for any stray newline characters
        for idx in range(end_idx, len(file_mmap)):
            if file_mmap[idx] in (0x0a, 0x0d):
                end_idx += 1
            else:
                break

        # Extract the header data
        header_data = file_mmap[begin_idx:end_idx].decode("ascii")

        return header_data, end_idx

    def _get_array_type(self, token_tree, element_name, default_data_type, allowed_data_types=None):
        """
        Return the data type for the aggregate array that contains the data of the specified element.

        :param token_tree:
        :param element_name:
        :param default_data_type:
        :param allowed_data_types:
        :return:
        """
        # Get a list of the data types of all element properties
        candidate_types = list()
        for el in token_tree.elements:
            if el.name == element_name:
                for prop in el.properties:
                    for variable in prop:
                        candidate_types.append(variable.data_type)

        # Sort the list according to the type preference and return the appropriate result
        if len(candidate_types) > 0:
            priority_type = max(candidate_types, key=lambda e: self.data_type_precedence.index(e))

            if allowed_data_types is not None:
                if priority_type in allowed_data_types:
                    return priority_type
                else:
                    return default_data_type
            else:
                return priority_type
        else:
            return default_data_type

    def _get_vertex_attributes(self, header_tokens, vertex_data_type, element_name="vertex"):
        """
        From the header tokens, extract a tuple of Attribute instances that describe the vertex data.

        :param header_tokens:
        :param vertex_data_type:
        :param element_name:
        :return:
        """
        vertex_attributes = list()
        start_index = 0
        for element in header_tokens.elements:
            if element.name == element_name:
                stride = sum(len(prop) for name, prop in element.properties.items())
                for name, prop in element.properties.items():
                    vertex_attributes.append(Attribute(
                        name, vertex_data_type, len(prop), stride, start_index
                    ))
                    start_index += len(prop)

        return tuple(vertex_attributes)

    def _parse_ascii_data(self, header_tokens, file_mmap, buffer_offset, aggregate_data_types):
        """
        Parse the data portion of a PLY file assuming it uses ASCII format.

        :param header_tokens:
        :param file_mmap:
        :param buffer_offset:
        :param aggregate_data_types:
        :return:
        """
        # Define the grammar of the body
        number = pyparsing_common.number()
        body_expr = list()
        for element in header_tokens.elements:
            sequences = list()
            for prop in element.properties:
                for variable in prop:
                    if "index_type" in variable:
                        sequences.append(countedArray(number))
                    else:
                        sequences.append(number(variable.name))

            element_data = Group(And(sequences))
            body_expr.append(Group(element_data * element.count)(element.name))

        ascii_grammar = And(body_expr)

        # Tokenize the body data
        body_tokens = ascii_grammar.parseString(file_mmap[buffer_offset:].decode("ascii"), parseAll=True)

        # Convert the data to arrays.
        element_data = dict()
        for name, dtype in aggregate_data_types.items():
            element_data[name] = array.array(dtype, self._flatten(body_tokens[name]))

        return element_data

    def _parse_binary_data(self, header_tokens, file_mmap, buffer_offset, aggregate_data_types):
        """
        Parse the data portion of a PLY file assuming it uses one of the two binary formats.

        :param header_tokens:
        :param file_mmap:
        :param buffer_offset:
        :param aggregate_data_types:
        :return:
        """
        # Determine the byte order of the data
        byte_order = self.byte_order_map[header_tokens.format.file_type]

        # Get the data
        element_data = dict()
        buffer_idx = buffer_offset
        for element in header_tokens.elements:
            data_types = list()
            for prop in element.properties:
                for variable in prop:
                    if "index_type" in variable:
                        data_types.append((variable.index_type, variable.data_type))
                    else:
                        data_types.append(variable.data_type)

            aggregate_data_type = aggregate_data_types.get(element.name, "f")

            if all(isinstance(dt, str) for dt in data_types):
                data_format_spec = "{}{}".format(byte_order, "".join(data_types))
                data = self._flatten(self._unpack_property_simple(data_format_spec, element.count, file_mmap, buffer_idx))
                element_data[element.name] = array.array(aggregate_data_type, data)
                buffer_idx += struct.calcsize(data_format_spec) * element.count
            elif all(isinstance(dt, tuple) for dt in data_types) and len(data_types) == 1:
                index_format_spec = "{}{}".format(byte_order, data_types[0][0])
                raw_data_format_spec = "{}{}{}".format(byte_order, "{}", data_types[0][1])
                data = self._flatten(self._unpack_property_list(index_format_spec, raw_data_format_spec, element.count, file_mmap, buffer_idx))
                element_data[element.name] = array.array(aggregate_data_type, data)
                buffer_idx += self._calculate_property_list_size(index_format_spec, raw_data_format_spec, element.count, file_mmap, buffer_idx)
            else:
                raise NotImplementedError("Currently cannot parse mixed simple and list properties per element. "
                                          "If a list property is present, it must be the only one for that element.")

        return element_data

    def _unpack_property_simple(self, format_string, count, file_mmap, buffer_offset):
        """
        Unpack binary data from a simple property. Works as generator.

        :param format_string:
        :param count:
        :param file_mmap:
        :param buffer_offset:
        :return:
        """
        pattern_size = struct.calcsize(format_string)
        for i in range(count):
            yield struct.unpack_from(format_string, file_mmap, buffer_offset + i * pattern_size)

    def _calculate_property_list_size(self, index_format_string, raw_data_format_string, count, file_mmap, buffer_offset):
        """

        :param index_format_string:
        :param raw_data_format_string:
        :param count:
        :param file_mmap:
        :param buffer_offset:
        :return:
        """
        index_size = struct.calcsize(index_format_string)
        data_block_size = 0
        for i in range(count):
            num_values = struct.unpack_from(index_format_string, file_mmap, buffer_offset + data_block_size)[0]
            data_format_string = raw_data_format_string.format(num_values)
            data_size = struct.calcsize(data_format_string)
            data_block_size += index_size + data_size

        return data_block_size

    def _unpack_property_list(self, index_format_string, raw_data_format_string, count, file_mmap, buffer_offset):
        """
        Unpack binary data from a list property. Works as generator.

        :param index_format_string:
        :param raw_data_format_string:
        :param count:
        :param file_mmap:
        :param buffer_offset:
        :return:
        """
        index_size = struct.calcsize(index_format_string)
        secondary_offset = 0
        for i in range(count):
            num_values = struct.unpack_from(index_format_string, file_mmap, buffer_offset + secondary_offset)[0]
            data_format_string = raw_data_format_string.format(num_values)
            data_size = struct.calcsize(data_format_string)
            data = struct.unpack_from(data_format_string, file_mmap, buffer_offset + secondary_offset + index_size)
            secondary_offset += index_size + data_size
            yield data

    def _flatten(self, nested_iterable):
        """
        Flatten a nested iterable. Is capable of flattening up to three levels, and works as generator.

        :param nested_iterable:
        :return:
        """
        for d in nested_iterable:
            if isinstance(d, (tuple, ParseResults)):
                for e in d:
                    if isinstance(e, ParseResults):
                        for f in e:
                            yield f
                    else:
                        yield e
            else:
                yield d
