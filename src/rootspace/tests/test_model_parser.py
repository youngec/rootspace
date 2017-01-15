# -*- coding: utf-8 -*-

import array
import pytest
import pyparsing
import ctypes

from rootspace.model_parser import PlyParser, Mesh, Attribute


class TestAttribute(object):
    def test_coersion_known(self):
        assert Attribute("position", "f", 0, 0, 0).type == Attribute.Type.Position

    def test_coersion_unknown(self):
        assert Attribute("somethingelse", "f", 0, 0, 0).type == Attribute.Type.Other

    def test_stride(self):
        a = Attribute("position", "f", 0, 1, 0)
        assert a.stride_bytes == a.stride * ctypes.sizeof(ctypes.c_float)

    def test_start_ptr(self):
        a = Attribute("position", "f", 0, 0, 1)
        assert a.start_ptr.value == ctypes.c_void_p(a.start_idx * ctypes.sizeof(ctypes.c_float)).value

    def test_location(self):
        for t in Attribute.Type:
            assert Attribute(t, "f", 0, 0, 0).location == t.value


class TestMesh(object):
    def test_data_bytes(self):
        mesh = Mesh(array.array("B", (0, 2)), array.array("B", (0, 1)), tuple(), Mesh.DrawMode.Triangles)
        assert mesh.data_bytes == b"\x00\x02"

    def test_data_type(self):
        mesh = Mesh(array.array("f", (0, 1)), array.array("B", (0, 1)), tuple(), Mesh.DrawMode.Triangles)
        assert mesh.data_type == "f"

    def test_index_bytes(self):
        mesh = Mesh(array.array("B", (0, 1)), array.array("B", (0, 2)), tuple(), Mesh.DrawMode.Triangles)
        assert mesh.index_bytes == b"\x00\x02"

    def test_index_type(self):
        mesh = Mesh(array.array("B", (0, 1)), array.array("I", (0, 1)), tuple(), Mesh.DrawMode.Triangles)
        assert mesh.index_type == "I"


class TestPlyParser(object):
    @pytest.fixture()
    def cube_complex(self):
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
