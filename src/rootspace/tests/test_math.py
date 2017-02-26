# -*- coding: utf-8 -*-

import math
import itertools
import functools
import operator
import collections.abc

import pytest

from rootspace.math import all_close, Matrix, Quaternion


class TestMatrix(object):
    @pytest.fixture("class", params=(
            (4, 4),
            (3, 4),
            (4, 3),
            (4, 1),
            (1, 4),
            (3, 3),
            (3, 1),
            (1, 3),
            (2, 2),
            (1, 1)
    ))
    def shape(self, request):
        return request.param

    def test_instantiation(self, shape):
        Matrix(shape)
        Matrix(shape, data_type="f", transposed=False)
        Matrix(shape, 2)
        Matrix(shape, range(shape[0] * shape[1]))
        Matrix(shape, list(range(shape[0] * shape[1])))

        a = Matrix(shape)
        assert Matrix(shape, a._data)._data is a._data

    def test_traits(self):
        assert issubclass(Matrix, collections.abc.Reversible)
        assert issubclass(Matrix, collections.abc.Collection)

    def test_shape(self, shape):
        assert Matrix(shape).shape == shape
        assert Matrix(shape, transposed=True).shape == shape[::-1]

    def test_length(self, shape):
        assert len(Matrix(shape)) == functools.reduce(operator.mul, shape)

    def test_is_square(self):
        assert Matrix((4, 4)).is_square is True
        assert Matrix((4, 1)).is_square is False
        assert Matrix((1, 4)).is_square is False
        assert Matrix((1, 1)).is_square is True

    def test_is_vector(self):
        assert Matrix((4, 4)).is_vector is False
        assert Matrix((4, 1)).is_vector is True
        assert Matrix((1, 4)).is_vector is True
        assert Matrix((1, 1)).is_vector is False

    def test_is_column_vector(self):
        assert Matrix((4, 4)).is_column_vector is False
        assert Matrix((4, 1)).is_column_vector is True
        assert Matrix((1, 4)).is_column_vector is False
        assert Matrix((1, 1)).is_column_vector is False

    def test_is_row_vector(self):
        assert Matrix((4, 4)).is_row_vector is False
        assert Matrix((4, 1)).is_row_vector is False
        assert Matrix((1, 4)).is_row_vector is True
        assert Matrix((1, 1)).is_row_vector is False

    def test_is_scalar(self):
        assert Matrix((4, 4)).is_scalar is False
        assert Matrix((4, 1)).is_scalar is False
        assert Matrix((1, 4)).is_scalar is False
        assert Matrix((1, 1)).is_scalar is True

    def test_equality(self, shape):
        length = functools.reduce(operator.mul, shape)
        assert Matrix(shape) == Matrix(shape)
        assert Matrix(shape, range(length)) == Matrix(shape, list(range(length)))

    def test_is_close(self, shape):
        epsilon = 7/3 - 4/3 - 1
        a = Matrix(shape, epsilon)
        b = Matrix(shape, 0)
        c = 0
        d = 0.0
        assert a.is_close(b) == Matrix(shape, 1, data_type="B")
        assert a.is_close(c) == Matrix(shape, 1, data_type="B")
        assert a.is_close(d) == Matrix(shape, 1, data_type="B")

    def test_all_close(self, shape):
        epsilon = 7/3 - 4/3 - 1
        a = Matrix(shape, epsilon)
        b = Matrix(shape, 0)
        c = 0
        d = 0.0
        assert a.all_close(b) is True
        assert a.all_close(c) is True
        assert a.all_close(d) is True

    def test_getitem(self):
        m = Matrix((4, 4), range(16))

        assert m[0, 1] == 1.0

        assert m[1, :3] == Matrix((1, 3), (4, 5, 6))
        assert m[1, :] == Matrix((1, 4), (4, 5, 6, 7))
        assert m[:3, 1] == Matrix((3, 1), (1, 5, 9))
        assert m[:, 1] == Matrix((4, 1), (1, 5, 9, 13))
        assert m[:3, :3] == Matrix((3, 3), (0, 1, 2, 4, 5, 6, 8, 9, 10))

        assert m[1, (0, 1)] == Matrix((1, 2), (4, 5))
        assert m[(0, 1), 1] == Matrix((2, 1), (1, 5))
        assert m[(0, 1), (0, 1)] == Matrix((2, 2), (0, 1, 4, 5))

        assert m[:, (0, 1)] == Matrix((4, 2), (0, 1, 4, 5, 8, 9, 12, 13))
        assert m[(0, 1), :] == Matrix((2, 4), (0, 1, 2, 3, 4, 5, 6, 7))

        assert m[0] == Matrix((1, 4), (0, 1, 2, 3))
        assert m[(0, 1), ] == Matrix((2, 4), (0, 1, 2, 3, 4, 5, 6, 7))
        assert m[:] == m

    def test_setitem(self):
        m = Matrix((4, 4), range(16))
        m[0, 1] = 100
        assert m[0, 1] == 100

        m = Matrix((4, 4), range(16))
        m[1, :3] = Matrix((1, 3), 100)
        assert m[1, :3] == Matrix((1, 3), 100)

        m = Matrix((4, 4), range(16))
        m[:2, :2] = (100, 100, 100, 100)
        assert m[:2, :2] == Matrix((2, 2), 100)

        m = Matrix((4, 4), range(16))
        m[0, (0, 1, 3)] = 100
        assert m[0, (0, 1, 3)] == Matrix((1, 3), 100)

    def test_determinant(self, shape):
        a = Matrix(shape)
        if a.is_square and not a.is_scalar:
            if a.shape[0] <= 4:
                assert a.determinant() == 1
            else:
                with pytest.raises(NotImplementedError):
                    a.determinant()
        else:
            with pytest.raises(ValueError):
                a.determinant()

    def test_norm(self, shape):
        assert Matrix(shape, 1).norm() == math.pow(sum(functools.reduce(operator.mul, shape) * [math.pow(abs(1), 2)]), 0.5)

    def test_cross(self, shape):
        if shape == (3, 1) or shape == (1, 3):
            a = Matrix(shape, (1, 0, 0))
            b = Matrix(shape, (0, 1, 0))
            c = Matrix(shape, (0, 0, 1))

            assert a.cross(b) == c
            assert b.cross(c) == a
            assert c.cross(a) == b
            assert b.cross(a) == -c
            assert c.cross(b) == -a
            assert a.cross(c) == -b
        else:
            with pytest.raises(ValueError):
                Matrix(shape).cross(Matrix(shape))

    def test_transpose(self, shape):
        length = functools.reduce(operator.mul, shape)
        a = Matrix(shape, range(length))
        assert a == a.t.t
        assert a.shape == a.t.shape[::-1]
        for i, j in itertools.product(range(a.shape[0]), range(a.shape[1])):
            assert a[i, j] == a.t[j, i]

    def test_identity(self):
        assert Matrix.identity(4) == Matrix((4, 4))
        assert Matrix.identity(4) == Matrix((4, 4), (
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1
        ))

    def test_translation(self):
        assert Matrix.translation(2, 2, 2) == Matrix((4, 4), (
            1, 0, 0, 2,
            0, 1, 0, 2,
            0, 0, 1, 2,
            0, 0, 0, 1
        ))

    def test_rotation_x(self):
        c = math.cos(math.pi)
        s = math.sin(math.pi)
        assert Matrix.rotation_x(math.pi) == Matrix((4, 4), (
            1, 0, 0, 0,
            0, c, -s, 0,
            0, s, c, 0,
            0, 0, 0, 1
        ))

    def test_rotation_y(self):
        c = math.cos(math.pi)
        s = math.sin(math.pi)
        assert Matrix.rotation_y(math.pi) == Matrix((4, 4), (
            c, 0, s, 0,
            0, 1, 0, 0,
            -s, 0, c, 0,
            0, 0, 0, 1
        ))

    def test_rotation_z(self):
        c = math.cos(math.pi)
        s = math.sin(math.pi)
        assert Matrix.rotation_z(math.pi) == Matrix((4, 4), (
            c, -s, 0, 0,
            s, c, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1
        ))

    def test_scaling(self):
        assert Matrix.scaling(2, 2, 2) == Matrix((4, 4), (
            2, 0, 0, 0,
            0, 2, 0, 0,
            0, 0, 2, 0,
            0, 0, 0, 1
        ))

    def test_shearing(self):
        assert Matrix.shearing(2, 0, 2) == Matrix((4, 4), (
            1, 0, 2, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1
        ))

    def test_orthograohic(self):
        assert Matrix.orthographic(-1 , 1, -1, 1, 0.1, 100) == Matrix((4, 4), (
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, -2 / 99.9, -100.1 / 99.9,
            0, 0, 0, 1
        ))

    def test_perspective(self):
        assert Matrix.perspective(math.pi/4, 1, 0.1, 100) == Matrix((4, 4), (
            1/math.tan(math.pi/8), 0, 0, 0,
            0, 1/math.tan(math.pi/8), 0, 0,
            0, 0, -100.1/99.9, -20/99.9,
            0, 0, -1, 0
        ))

    def test_addition_neutral_element(self, shape):
        a = Matrix(shape, range(functools.reduce(operator.mul, shape)))

        assert a + Matrix(a.shape, 0) == a
        assert a + 0 == a
        assert a + 0.0 == a

    def test_addition_inverse(self, shape):
        length = functools.reduce(operator.mul, shape)
        a = Matrix(shape, range(length))
        b = Matrix(shape, range(1, length + 1))

        assert -a == Matrix(a.shape, (-s for s in a))
        assert a + -b == a - b
        assert a + +b == a + b

    def test_addition_commutativity(self, shape):
        length = functools.reduce(operator.mul, shape)
        a = Matrix(shape, range(length))
        b = Matrix(shape, range(1, length + 1))
        c = 5
        d = 5.0

        assert a + b == b + a
        assert a + c == c + a
        assert a + d == d + a

    def test_addition_associativity(self, shape):
        length = functools.reduce(operator.mul, shape)
        a = Matrix(shape, range(length))
        b = Matrix(shape, range(1, length + 1))
        c = Matrix(shape, range(2, length + 2))
        d = 5
        e = 6
        f = 5.0
        g = 6.0

        assert b + (a + c) == (b + a) + c
        assert d + (a + e) == (d + a) + e
        assert f + (a + g) == (f + a) + g

    def test_addition_shapes(self):
        with pytest.raises(ValueError):
            Matrix((2, 2)) + Matrix((3, 3))
        with pytest.raises(ValueError):
            Matrix((2, 2)) - Matrix((3, 3))

    def test_multiplication_neutral_element(self, shape):
        length = functools.reduce(operator.mul, shape)
        a = Matrix(shape, range(length))

        assert a * Matrix(shape, 1) == a
        assert a * 1 == a
        assert a * 1.0 == a

    def test_multiplication_inverse(self, shape):
        length = functools.reduce(operator.mul, shape)
        a = Matrix(shape, range(1, length + 1))
        b = Matrix(shape, range(4, length + 4))

        assert all_close(Matrix(shape, 1) / a, Matrix(a.shape, (1 / s for s in a)))
        assert all_close(1 / a, Matrix(a.shape, (1 / s for s in a)))
        assert all_close(1.0 / a, Matrix(a.shape, (1 / s for s in a)))
        assert all_close(a * (Matrix(shape, 1) / b), a / b)
        assert all_close(a * (1 / b), a / b)
        assert all_close(a * (1.0 / b), a / b)

    def test_multiplication_commutativity(self, shape):
        length = functools.reduce(operator.mul, shape)
        a = Matrix(shape, range(1, length + 1))
        b = Matrix(shape, range(4, length + 4))
        c = 5
        d = 5.0

        assert a * b == b * a
        assert a * c == c * a
        assert a * d == d * a

    def test_multiplication_associativity(self, shape):
        length = functools.reduce(operator.mul, shape)
        a = Matrix(shape, range(length))
        b = Matrix(shape, range(1, length + 1))
        c = Matrix(shape, range(2, length + 2))
        d = 5
        e = 6
        f = 5.0
        g = 6.0

        assert b * (a * c) == (b * a) * c
        assert d * (a * e) == (d * a) * e
        assert f * (a * g) == (f * a) * g

    def test_distributivity(self, shape):
        length = functools.reduce(operator.mul, shape)
        a = Matrix(shape, range(length))
        b = Matrix(shape, range(1, length + 1))
        c = Matrix(shape, range(2, length + 2))

        assert a * (b + c) == a * b + a * c

    def test_multiplication_shapes(self):
        with pytest.raises(ValueError):
            Matrix((2, 2)) * Matrix((3, 3))
        with pytest.raises(ValueError):
            Matrix((2, 2)) / Matrix((3, 3))

    def test_dot_product_neutral_element(self):
        a = Matrix((2, 2), range(4))
        b = Matrix.identity(2)

        assert a @ b == a
        assert a @ b == b @ a

    def test_dot_product_inverse(self):
        a = Matrix((2, 2), (4, 3, 2, 1))
        b = Matrix((2, 2), (-0.5, 1.5, 1, -2))

        assert a @ b == Matrix.identity(2)
        assert b @ a == Matrix.identity(2)

    def test_dot_product_associativity(self):
        a = Matrix((2, 2), range(4))
        b = Matrix((2, 2), range(1, 5))
        c = Matrix((2, 2), range(2, 6))

        assert b @ (a @ c) == (b @ a) @ c

    def test_dot_distributivity(self):
        a = Matrix((2, 2), range(4))
        b = Matrix((2, 2), range(1, 5))
        c = Matrix((2, 2), range(2, 6))

        assert a @ (b + c) == a @ b + a @ c

    def test_dot_product_shapes(self):
        with pytest.raises(ValueError):
            Matrix((4, 3)) @ Matrix((2, 2))

    def test_dot_product_vectors(self):
        assert Matrix((1, 3), 1) @ Matrix((3, 1), 1) == 3


class TestQuaternion(object):
    def test_instantiation(self):
        Quaternion()
        Quaternion(qi=0, qj=0, qk=0, qr=1, data_type="f")

    def test_properties(self):
        a = Quaternion(1, 2, 3, 4)
        assert a.qi == 1
        assert a.qj == 2
        assert a.qk == 3
        assert a.qr == 4

    def test_conjugate(self):
        assert Quaternion(1, 2, 3, 4).t == Quaternion(-1, -2, -3, 4)

    def test_matrix(self):
        assert Quaternion().matrix == Matrix.identity(4)

    def test_equality(self):
        assert Quaternion() == Quaternion()
        assert Quaternion(1, 2, 3, 4) == Quaternion(1, 2, 3, 4)

    def test_norm(self):
        assert Quaternion().norm() == 1
        assert Quaternion(1, 1, 1, 1).norm() == 2

    def test_transform(self):
        a = Quaternion(0, 0, 0, 1)
        b = Matrix((4, 1), (1, 2, 3, 4))

        assert a.transform(b) == b

    @pytest.mark.xfail
    def test_from_axis(self):
        raise NotImplementedError()

    def test_slerp(self):
        a = Quaternion(1, 0, 0, 1)
        b = Quaternion(0, 1, 0, 1)

        assert Quaternion.slerp(a, b, 0.0) == a / a.norm()
        assert Quaternion.slerp(a, b, 1.0) == b / b.norm()

    def test_addition_neutral_element(self):
        a = Quaternion(1, 2, 3, 4)

        assert a + Quaternion(0, 0, 0, 0) == a
        assert a + 0 == a
        assert a + 0.0 == a

    def test_addition_inverse(self):
        a = Quaternion(1, 2, 3, 4)
        b = Quaternion(2, 3, 4, 5)

        assert -a == Quaternion(-1, -2, -3, -4)
        assert a + -b == a - b
        assert a + +b == a + b

    def test_addition_commutativity(self):
        a = Quaternion(1, 2, 3, 4)
        b = Quaternion(2, 3, 4, 5)
        c = 5
        d = 5.0

        assert a + b == b + a
        assert a + c == c + a
        assert a + d == d + a

    def test_addition_associativity(self):
        a = Quaternion(1, 2, 3, 4)
        b = Quaternion(2, 3, 4, 5)
        c = Quaternion(3, 4, 5, 6)
        d = 5
        e = 6
        f = 5.0
        g = 6.0

        assert b + (a + c) == (b + a) + c
        assert d + (a + e) == (d + a) + e
        assert f + (a + g) == (f + a) + g

    def test_multiplication_neutral_element(self):
        a = Quaternion(1, 2, 3, 4)

        assert a * Quaternion(1, 1, 1, 1) == a
        assert a * 1 == a
        assert a * 1.0 == a

    def test_multiplication_inverse(self):
        a = Quaternion(1, 2, 3, 4)
        b = Quaternion(2, 3, 4, 5)

        assert all_close(Quaternion(1, 1, 1, 1) / a, Quaternion(1/a.qi, 1/a.qj, 1/a.qk, 1/a.qr))
        assert all_close(1 / a, Quaternion(1/a.qi, 1/a.qj, 1/a.qk, 1/a.qr))
        assert all_close(1.0 / a, Quaternion(1/a.qi, 1/a.qj, 1/a.qk, 1/a.qr))
        assert all_close(a * (Quaternion(1, 1, 1, 1) / b), a / b)
        assert all_close(a * (1 / b), a / b)
        assert all_close(a * (1.0 / b), a / b)

    def test_multiplication_commutativity(self):
        a = Quaternion(1, 2, 3, 4)
        b = Quaternion(2, 3, 4, 5)
        c = 5
        d = 5.0

        assert a * b == b * a
        assert a * c == c * a
        assert a * d == d * a

    def test_multiplication_associativity(self):
        a = Quaternion(1, 2, 3, 4)
        b = Quaternion(2, 3, 4, 5)
        c = Quaternion(3, 4, 5, 6)
        d = 5
        e = 6
        f = 5.0
        g = 6.0

        assert b * (a * c) == (b * a) * c
        assert d * (a * e) == (d * a) * e
        assert f * (a * g) == (f * a) * g

    def test_distributivity(self):
        a = Quaternion(1, 2, 3, 4)
        b = Quaternion(2, 3, 4, 5)
        c = Quaternion(3, 4, 5, 6)

        assert a * (b + c) == a * b + a * c

    def test_quaternion_product_neutral_element(self):
        a = Quaternion(1, 2, 3, 4)
        b = Quaternion()

        assert a @ b == a
        assert a @ b == b @ a

    def test_quaternion_product_inverse(self):
        a = Quaternion(2, 2, 2, 2)
        b = a.inverse()

        assert a @ b == Quaternion()
        assert b @ a == Quaternion()

    def test_quaternion_product_associativity(self):
        a = Quaternion(1, 2, 3, 4)
        b = Quaternion(2, 3, 4, 5)
        c = Quaternion(3, 4, 5, 6)

        assert b @ (a @ c) == (b @ a) @ c

    def test_quaternion_distributivity(self):
        a = Quaternion(1, 2, 3, 4)
        b = Quaternion(2, 3, 4, 5)
        c = Quaternion(3, 4, 5, 6)

        assert a @ (b + c) == a @ b + a @ c

    def test_quaternion_vectors(self):
        a = Quaternion(0, 0, 0, 1)
        b = Matrix((4, 1), (1, 2, 3, 4))

        assert a @ b @ a.inverse() == Quaternion(1, 2, 3, 4)
