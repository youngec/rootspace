# -*- coding: utf-8 -*-

import array
import pytest
import pyparsing

from rootspace.legacy.model_parser import PlyParser
from rootspace.legacy.data_abstractions import Attribute, Mesh


@pytest.fixture()
def cube_complex():
    return """ply
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
property uchar alpha
element face 7
property list uchar int vertex_index
element edge 5
property int vertex1
property int vertex2
property uchar red
property uchar green
property uchar blue
end_header
0 0 0 255 0 0 1
0 0 1 255 0 0 1
0 1 1 255 0 0 1
0 1 0 255 0 0 1
1 0 0 0 0 255 1
1 0 1 0 0 255 1
1 1 1 0 0 255 1
1 1 0 0 0 255 1
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


class TestPlyParser(object):
    def test_tokenize(self, cube_complex):
        parser = PlyParser.create()
        assert isinstance(parser.tokenize(cube_complex), pyparsing.ParseResults)

    def test_parse(self, cube_complex):
        parser = PlyParser.create()
        assert isinstance(parser.parse(cube_complex), Mesh)

    def test_load(self, tmpdir, cube_complex):
        parser = PlyParser.create()
        temp_cube = tmpdir.join("cube.ply")
        temp_cube.write(cube_complex)
        assert isinstance(parser.load(str(temp_cube)), Mesh)

    def test_result(self, cube_complex):
        parser = PlyParser.create()
        mesh = parser.parse(cube_complex)

        target_data = array.array("f", (
            0, 0, 0, 255, 0, 0, 1,
            0, 0, 1, 255, 0, 0, 1,
            0, 1, 1, 255, 0, 0, 1,
            0, 1, 0, 255, 0, 0, 1,
            1, 0, 0, 0, 0, 255, 1,
            1, 0, 1, 0, 0, 255, 1,
            1, 1, 1, 0, 0, 255, 1,
            1, 1, 0, 0, 0, 255, 1
        ))
        target_index = array.array("I", (
            0, 1, 2,
            0, 2, 3,
            7, 6, 5, 4,
            0, 4, 5, 1,
            1, 5, 6, 2,
            2, 6, 7, 3,
            3, 7, 4, 0
        ))
        target_attributes = (
            Attribute("position", "f", 3, 7, 0),
            Attribute("color", "f", 4, 7, 3)
        )
        assert mesh.data == target_data
        assert mesh.index == target_index
        assert mesh.attributes == target_attributes
