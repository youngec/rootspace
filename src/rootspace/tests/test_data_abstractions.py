# -*- coding: utf-8 -*-

import array
import ctypes


from rootspace.data_abstractions import Attribute, Mesh


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
