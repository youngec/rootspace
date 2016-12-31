#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Implements parsers for resource files."""

import pyparsing as pp
import attr


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
    grammar = attr.ib()

    @classmethod
    def create(cls):
        number = pp.pyparsing_common.number()
        identifier = pp.pyparsing_common.identifier()
        lit = {l: pp.CaselessKeyword(l) for l in (
            "ascii", "binary_little_endian", "binary_big_endian", "vertex", "face", "edge", "char",
            "uchar", "short", "ushort", "int", "uint", "float", "double", "format", "comment",
            "element", "property", "list", "ply", "end_header"
        )}

        format_type = lit["ascii"] | lit["binary_little_endian"] | lit["binary_big_endian"]
        element_type = lit["vertex"] | lit["face"] | lit["edge"] | identifier
        data_type = lit["char"] | lit["uchar"] | lit["short"] | lit["ushort"] | lit["int"] | lit["uint"] | \
            lit["float"] | lit["double"]

        comment_decl = lit["comment"] + pp.restOfLine

        format_decl = pp.Group(
            pp.Suppress(lit["format"]) +
            format_type("file_type") +
            number("version")
        )("format")

        property_simple = pp.Group(
            pp.Suppress(lit["property"]) +
            data_type("data_type") +
            identifier("name")
        )("simple")

        property_list = pp.Group(
            pp.Suppress(lit["property"]) + pp.Suppress(lit["list"]) +
            data_type("index_type") +
            data_type("data_type") +
            identifier("name")
        )("list")

        element_decl = pp.Group(
            pp.Suppress(lit["element"]) +
            element_type("name") +
            number("count") +
            pp.Group(
                pp.OneOrMore(property_simple) | property_list
            )("properties")
        )

        declarations = pp.Group(
            format_decl +
            pp.Group(
                pp.OneOrMore(element_decl)
            )("elements")
        )("declarations")

        header_start = pp.Suppress(lit["ply"])

        header_stop = pp.Suppress(lit["end_header"])

        header = header_start + declarations + header_stop

        body = pp.Forward()("data")

        ply_grammar = (header + body).ignore(comment_decl)

        def construct_body_expr(source, location, tokens):
            body_expr = list()
            for el_decl in tokens.declarations.elements:
                if el_decl.properties[0].getName() == "list":
                    element = pp.countedArray(number)
                else:
                    element = pp.Group(
                        pp.And(number(p.name) for p in el_decl.properties)
                    )

                body_expr.append(pp.Group(element * el_decl.count)(el_decl.name))

            body << pp.And(body_expr)

        header.addParseAction(construct_body_expr)

        return cls(ply_grammar)

    def tokenize(self, data):
        """
        Parse the supplied data into an abstract syntax tree.

        :param data:
        :return:
        """
        return self.grammar.parseString(data)


def main():
    data = """ply
format ascii 1.0
comment author: Greg Turk
comment object: another cube
element vertex 8
property float x
property float y
property float z
property uchar red
property uchar green
property uchar blue
element face 7
property list uchar int vertex_index
element edge 5
property int vertex1
property int vertex2
property uchar red
property uchar green
property uchar blue
end_header
0 0 0 255 0 0
0 0 1 255 0 0
0 1 1 255 0 0
0 1 0 255 0 0
1 0 0 0 0 255
1 0 1 0 0 255
1 1 1 0 0 255
1 1 0 0 0 255
3 0 1 2
3 0 2 3
4 7 6 5 4
4 0 4 5 1
4 1 5 6 2
4 2 6 7 3
4 3 7 4 0
0 1 255 255 255
1 2 255 255 255
2 3 255 255 255
3 0 255 255 255
2 0 0 0 0"""

    try:
        parser = PlyParser.create()
        tokens = parser.tokenize(data)
        #tokens.pprint()
        print(tokens.dump())
        #print(len(tokens.body))
    except pp.ParseException as e:
        print(e.line)
        print(" " * (e.column - 1) + "^")
        print(e)


if __name__ == "__main__":
    main()