# -*- coding: utf-8 -*-

import array
import math

import pytest

from rootspace.math import Vector, Matrix, Quaternion


class TestVector(object):
    def test_initialization(self):
        with pytest.raises(ValueError):
            Vector()
        Vector(1)
        Vector(1, 2)
        Vector(1, 2, 3)
        Vector(1, 2, 3, 4)

    def test_default_data_type(self):
        assert Vector(1, 2, 3)._data.typecode == "f"

    def test_iterable_initialization(self):
        assert Vector([1, 2, 3])._data == array.array("f", (1, 2, 3))
        assert Vector((1, 2, 3))._data == array.array("f", (1, 2, 3))
        assert Vector(range(1, 4))._data == array.array("f", (1, 2, 3))

    def test_to_bytes(self):
        assert isinstance(Vector(1, 2, 3).to_bytes(), bytes)

    @pytest.mark.xfail
    def test_normalize(self):
        assert Vector(1, 2, 3).normalize(inplace=False) == Vector(1, 2, 3) / abs(Vector(1, 2, 3))
        a = Vector(1, 2, 3)
        a.normalize()
        assert a == Vector(1, 2, 3) / abs(Vector(1, 2, 3))

    def test_dot(self, mocker):
        mocker.patch.object(Vector, "__matmul__", autospec=True)
        a = Vector(1, 2, 3)
        b = Vector(2, 3, 4)
        a.dot(b)
        Vector.__matmul__.assert_called_once_with(a, b)

    def test_cross(self):
        with pytest.raises(TypeError):
            Vector(1, 2, 3).cross(1)

        with pytest.raises(ValueError):
            Vector(1, 2, 3).cross(Vector(1, 2))

        for d in (1, 2, 4, 5, 6, 8, 9, 10):
            with pytest.raises(ValueError):
                Vector(range(d)).cross(Vector(range(d)))

        with pytest.raises(NotImplementedError):
            Vector(range(7)).cross(Vector(range(7)))

        assert Vector(1, 0, 0).cross(Vector(0, 1, 0)) == Vector(0, 0, 1)
        assert Vector(0, 1, 0).cross(Vector(0, 0, 1)) == Vector(1, 0, 0)
        assert Vector(0, 0, 1).cross(Vector(1, 0, 0)) == Vector(0, 1, 0)
        assert Vector(0, 1, 0).cross(Vector(1, 0, 0)) == Vector(0, 0, -1)
        assert Vector(0, 0, 1).cross(Vector(0, 1, 0)) == Vector(-1, 0, 0)
        assert Vector(1, 0, 0).cross(Vector(0, 0, 1)) == Vector(0, -1, 0)

    def test_getitem(self):
        a = Vector(1, 2, 3)
        assert a[0] == 1
        assert a[:2] == Vector(1, 2)
        assert a[:] == a

    @pytest.mark.xfail
    def test_setitem(self):
        a = Vector(1, 2, 3)
        a[0] = 100
        assert a._data[0] == 100
        a[:2] = 200
        assert a._data[0] == 200 and a._data[1] == 200

    def test_repr(self):
        assert repr(Vector(1, 2, 3)) == "Vector(1.0, 2.0, 3.0)"

    def test_str(self):
        assert str(Vector(1, 2, 3)) == "(1.0, 2.0, 3.0)"

    def test_iter(self):
        assert 1 in Vector(1, 2, 3)

    def test_length(self):
        assert len(Vector(1, 2, 3)) == 3

    def test_equality(self):
        assert Vector(1, 2, 3) == Vector(1, 2, 3)
        assert Vector(1, 2, 3) != Vector(1, 2, 3, 4)
        assert Vector(1, 2, 3) != Vector(1, 2)
        assert Vector(1, 2, 3) != 1

    def test_absolute(self):
        assert abs(Vector(1, 2, 3)) == math.sqrt(14)

    def test_addition(self):
        assert Vector(1, 2, 3) + Vector(2, 3, 4) == Vector(3, 5, 7)
        assert Vector(1, 2, 3) + 1 == Vector(2, 3, 4)

        assert Vector(2, 3, 4) + Vector(1, 2, 3) == Vector(3, 5, 7)
        assert 1 + Vector(1, 2, 3) == Vector(2, 3, 4)

    def test_subtraction(self):
        assert Vector(1, 2, 3) - Vector(2, 3, 4) == Vector(-1, -1, -1)
        assert Vector(1, 2, 3) - 1 == Vector(0, 1, 2)

        assert Vector(2, 3, 4) - Vector(1, 2, 3) == Vector(1, 1, 1)
        assert 1 - Vector(1, 2, 3) == Vector(0, -1, -2)

    def test_multiplication(self):
        assert Vector(1, 2, 3) * Vector(2, 3, 4) == Vector(2, 6, 12)
        assert Vector(1, 2, 3) * 1 == Vector(1, 2, 3)

        assert Vector(2, 3, 4) * Vector(1, 2, 3) == Vector(2, 6, 12)
        assert 1 * Vector(1, 2, 3) == Vector(1, 2, 3)

    def test_truediv(self):
        assert Vector(1, 2, 2) / Vector(2, 6, 4) == Vector(0.5, 1/3, 0.5)
        assert Vector(1, 2, 3) / 1 == Vector(1, 2, 3)

        assert Vector(2, 6, 4) / Vector(1, 2, 2) == Vector(2, 3, 2)
        assert 1 / Vector(1, 2, 4) == Vector(1, 0.5, 0.25)

    def test_matmul(self):
        assert Vector(1, 2, 3) @ Vector(2, 3, 4) == 20
        assert Vector(2, 3, 4) @ Vector(1, 2, 3) == 20


class TestMatrix4(object):
    def test_creation(self):
        Matrix((4, 4))
        Matrix((4, 4), range(16))
        Matrix((4, 4), *list(range(16)))

    def test_data(self):
        assert Matrix((4, 4), range(16))._data == array.array("f", range(16))

    def test_equality(self):
        assert Matrix((4, 4)) == Matrix((4, 4))
        assert Matrix((4, 4), range(16)) == Matrix((4, 4), *list(range(16)))

    def test_length(self):
        assert len(Matrix((4, 4))) == 16

    def test_shape(self):
        assert Matrix((4, 4)).shape == (4, 4)

    def test_get_shape(self):
        m = Matrix((4, 4))
        assert m._get_shape(4) == (1, 1)
        assert m._get_shape(2, 2) == (1, 1)
        assert m._get_shape(2, slice(4)) == (1, 4)
        assert m._get_shape(slice(4), 2) == (4, 1)
        assert m._get_shape(slice(1, 5), slice(4)) == (4, 4)
        with pytest.raises(TypeError):
            m._get_shape(None)

    def test_getitem(self):
        m = Matrix((4, 4), range(16))
        assert m[0] == Matrix((1, 4), 0, 1, 2, 3)
        assert m[0, 1] == 1.0
        assert m[:4] == Matrix((4, 4), range(16))
        assert m[:] == Matrix((4, 4), range(16))
        assert m[1, :4] == Matrix((1, 4), 4, 5, 6, 7)
        assert m[1, :] == Matrix((1, 4), 4, 5, 6, 7)
        assert m[:4, 1] == Matrix((4, 1), 1, 5, 9, 13)
        assert m[:, 1] == Matrix((4, 1), 1, 5, 9, 13)

    def test_setitem(self):
        m = Matrix((4, 4))
        m[0] = (2, 2, 2, 2)
        assert m[0] == Matrix((1, 4), 2, 2, 2, 2)
        m[0, 0] = 3.0
        assert m[0, 0] == 3.0
        m[0, :3] = (4.0, 4.0, 4.0)
        assert m[0, :3] == Matrix((1, 3), 4, 4, 4)
        m[:3, 0] = (5.0, 5.0, 5.0)
        assert m[:3, 0] == Matrix((3, 1), 5, 5, 5)

    def test_translation(self):
        assert Matrix.translation(1, 1, 1) == Matrix(
            (4, 4),
            1, 0, 0, 1,
            0, 1, 0, 1,
            0, 0, 1, 1,
            0, 0, 0, 1
        )

    def test_rotation_x(self):
        c = math.cos(math.pi)
        s = math.sin(math.pi)
        assert Matrix.rotation_x(math.pi) == Matrix(
            (4, 4),
            1, 0, 0, 0,
            0, c, -s, 0,
            0, s, c, 0,
            0, 0, 0, 1
        )

    def test_rotation_y(self):
        c = math.cos(math.pi)
        s = math.sin(math.pi)
        assert Matrix.rotation_y(math.pi) == Matrix(
            (4, 4),
            c, 0, s, 0,
            0, 1, 0, 0,
            -s, 0, c, 0,
            0, 0, 0, 1
        )

    def test_rotation_z(self):
        c = math.cos(math.pi)
        s = math.sin(math.pi)
        assert Matrix.rotation_z(math.pi) == Matrix(
            (4, 4),
            c, -s, 0, 0,
            s, c, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1
        )

    def test_scaling(self):
        assert Matrix.scaling(2, 2, 2) == Matrix(
            (4, 4),
            2, 0, 0, 0,
            0, 2, 0, 0,
            0, 0, 2, 0,
            0, 0, 0, 1
        )

    def test_shearing(self):
        assert Matrix.shearing(2, 0, 2) == Matrix(
            (4, 4),
            1, 0, 2, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1
        )


class TestQuaternion(object):
    def test_initialization(self):
        for d in (1, 2, 3):
            with pytest.raises(ValueError):
                Quaternion(range(d))
        Quaternion()
        Quaternion([])
        Quaternion(1, 2, 3, 4)

    def test_direct_access_properties(self):
        epsilon = 7/3 - 4/3 - 1
        a = Quaternion(1, 2, 3, 4)

        assert a.r == 1.0
        assert a.i == 2.0
        assert a.j == 3.0
        assert a.k == 4.0

        a.r = epsilon * 0.1
        a.i = epsilon * 0.1
        a.j = epsilon * 0.1
        a.k = epsilon * 0.1

        assert a.r == 0.0
        assert a.i == 0.0
        assert a.j == 0.0
        assert a.k == 0.0

    def test_conjugate(self):
        assert Quaternion(1, 2, 3, 4).t == Quaternion(1, -2, -3, -4)

    @pytest.mark.xfail
    def test_matrix3(self):
        raise NotImplementedError()

    @pytest.mark.xfail
    def test_matrix4(self):
        raise NotImplementedError()

    def test_to_bytes(self):
        assert isinstance(Quaternion().to_bytes(), bytes)

    @pytest.mark.xfail
    def test_normalize(self):
        assert Quaternion(1, 2, 3).normalize(inplace=False) == Quaternion(1, 2, 3) / abs(Quaternion(1, 2, 3))
        a = Quaternion(1, 2, 3)
        a.normalize()
        assert a == Quaternion(1, 2, 3) / abs(Quaternion(1, 2, 3))

    def test_getitem(self):
        a = Quaternion(1, 2, 3, 4)
        assert a[0] == 1
        assert a[:2] == array.array("f", (1, 2))

    @pytest.mark.xfail
    def test_setitem(self):
        a = Quaternion(1, 2, 3, 4)
        a[0] = 100
        assert a._data[0] == 100
        a[:2] = 200
        assert a._data[0] == 200 and a._data[1] == 200

    def test_repr(self):
        assert repr(Quaternion(1, 2, 3, 4)) == "Quaternion(1.0, 2.0, 3.0, 4.0)"

    def test_str(self):
        assert str(Quaternion(1, 2, 3, 4)) == "1.0 + 2.0i + 3.0j + 4.0k"

    def test_iter(self):
        assert 1 in Quaternion(1, 2, 3, 4)

    def test_length(self):
        assert len(Quaternion(1, 2, 3, 4)) == 4

    def test_equality(self):
        assert Quaternion(1, 2, 3, 4) == Quaternion(1, 2, 3, 4)
        assert Quaternion(1, 2, 3, 4) != Quaternion()
        assert Quaternion(1, 2, 3, 4) != Quaternion(1, 1, 1, 1)
        assert Quaternion(1, 2, 3, 4) != 1

    def test_absolute(self):
        assert abs(Quaternion(1, 2, 3, 4)) == math.sqrt(30)

    def test_addition(self):
        assert Quaternion(1, 2, 3, 4) + Quaternion(2, 3, 4, 5) == Quaternion(3, 5, 7, 9)
        assert Quaternion(1, 2, 3, 4) + 1 == Quaternion(2, 3, 4, 5)

        assert Quaternion(2, 3, 4, 5) + Quaternion(1, 2, 3, 4) == Quaternion(3, 5, 7, 9)
        assert 1 + Quaternion(1, 2, 3, 4) == Quaternion(2, 3, 4, 5)

    def test_subtraction(self):
        assert Quaternion(1, 2, 3, 4) - Quaternion(2, 3, 4, 5) == Quaternion(-1, -1, -1, -1)
        assert Quaternion(1, 2, 3, 4) - 1 == Quaternion(0, 1, 2, 3)

        assert Quaternion(2, 3, 4, 5) - Quaternion(1, 2, 3, 4) == Quaternion(1, 1, 1, 1)
        assert 1 - Quaternion(1, 2, 3, 4) == Quaternion(0, -1, -2, -3)

    def test_multiplication(self):
        assert Quaternion(1, 2, 3, 4) * Quaternion(2, 3, 4, 5) == Quaternion(2, 6, 12, 20)
        assert Quaternion(1, 2, 3, 4) * 1 == Quaternion(1, 2, 3, 4)

        assert Quaternion(2, 3, 4, 5) * Quaternion(1, 2, 3, 4) == Quaternion(2, 6, 12, 20)
        assert 1 * Quaternion(1, 2, 3, 4) == Quaternion(1, 2, 3, 4)

    def test_truediv(self):
        assert Quaternion(1, 2, 2, 10) / Quaternion(2, 6, 4, 2) == Quaternion(0.5, 1/3, 0.5, 5.0)
        assert Quaternion(1, 2, 3, 4) / 1 == Quaternion(1, 2, 3, 4)

        assert Quaternion(2, 6, 4, 10) / Quaternion(1, 2, 2, 2) == Quaternion(2, 3, 2, 5)
        assert 1 / Quaternion(1, 2, 4, 5) == Quaternion(1, 0.5, 0.25, 0.2)

    def test_matmul(self):
        assert Quaternion(1, 2, 3, 4) @ Quaternion(2, 3, 4, 5) == Quaternion(-36, 6, 12, 12)
        assert Quaternion(2, 3, 4, 5) @ Quaternion(1, 2, 3, 4) == Quaternion(-36, 8, 8, 14)
        assert Quaternion(1, 2, 3, 4) @ Quaternion(1, -2, -3, -4) == Quaternion(30, 0, 0, 0)
