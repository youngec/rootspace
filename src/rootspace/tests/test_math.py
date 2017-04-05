# -*- coding: utf-8 -*-

import math
import itertools
import functools
import operator

import pytest

from rootspace.math import Quaternion
from rootspace._math import Matrix, get_sub_shape, linearize_indices, \
    complete_indices, select_all


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

    def test_total_ordering(self, shape):
        assert Matrix(shape, -1) < Matrix(shape, 0)
        assert Matrix(shape, -1) <= Matrix(shape, 0)
        assert Matrix(shape, 0) == Matrix(shape, 0)
        assert Matrix(shape, 1) >= Matrix(shape, 0)
        assert Matrix(shape, 1) > Matrix(shape, 0)

        assert Matrix(shape, -1) < 0
        assert Matrix(shape, -1) <= 0
        assert Matrix(shape, 0) == 0
        assert Matrix(shape, 1) >= 0
        assert Matrix(shape, 1) > 0

        assert Matrix(shape, -1) < 0.0
        assert Matrix(shape, -1) <= 0.0
        assert Matrix(shape, 0) == 0.0
        assert Matrix(shape, 1) >= 0.0
        assert Matrix(shape, 1) > 0.0

        assert Matrix(shape, 0) != Matrix(shape, 1)
        assert not Matrix(shape, 0) == Matrix(shape, 1)
        assert Matrix(shape, 0) != "Something entirely different"

    def test_str(self):
        assert str(Matrix((2, 3), range(6))) == "[[0.0, 1.0, 2.0], [3.0, 4.0, 5.0]]"

    def test_repr(self):
        assert repr(Matrix((2, 3), range(6))) == "Matrix((2, 3), (0.0, 1.0, 2.0, 3.0, 4.0, 5.0), transposed=0)"
        assert eval(repr(Matrix((2, 3), range(6)))) == Matrix((2, 3), range(6))

    def test_length(self, shape):
        assert len(Matrix(shape)) == functools.reduce(operator.mul, shape)

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

        m = Matrix((2, 3), 0)
        m[:] = Matrix((3, 2), range(6), transposed=True)
        assert m[:] == Matrix((2, 3), (0, 2, 4, 1, 3, 5))

    def test_iter(self):
        a = Matrix((2, 3), range(6))
        assert [e for r in a for e in r] == [0, 1, 2, 3, 4, 5]
        b = Matrix((2, 3), range(6), transposed=True)
        assert [e for r in b for e in r] == [0, 3, 1, 4, 2, 5]

    def test_all_close(self, shape):
        epsilon = 7/3 - 4/3 - 1
        a = Matrix(shape, epsilon)
        b = Matrix(shape, 0)
        c = 0
        d = 0.0
        assert a.all_close(b) is True
        assert a.all_close(c) is True
        assert a.all_close(d) is True

    def test_unary_negative(self, shape):
        assert -Matrix(shape, 1) == Matrix(shape, -1)
        assert -Matrix(shape, 0) == Matrix(shape, 0)
        assert -Matrix(shape, -1) == Matrix(shape, 1)

    def test_unary_positive(self, shape):
        assert +Matrix(shape, 1) == Matrix(shape, 1)
        assert +Matrix(shape, 0) == Matrix(shape, 0)
        assert +Matrix(shape, -1) == Matrix(shape, -1)

    def test_unary_absolute(self, shape):
        assert abs(Matrix(shape, 1)) == Matrix(shape, 1)
        assert abs(Matrix(shape, 0)) == Matrix(shape, 0)
        assert abs(Matrix(shape, -1)) == Matrix(shape, 1)

    def test_addition_neutral_element(self, shape):
        a = Matrix(shape, range(functools.reduce(operator.mul, shape)))

        assert a + Matrix(shape, 0) == a
        assert a + 0 == a
        assert a + 0.0 == a

    def test_addition_inverse(self, shape):
        length = functools.reduce(operator.mul, shape)
        a = Matrix(shape, range(length))
        b = Matrix(shape, range(1, length + 1))

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
        a_inv = Matrix(shape, [1 / i for i in range(1, length + 1)])

        assert (Matrix(shape, 1) / a).all_close(a_inv)
        assert (1 / a).all_close(a_inv)
        assert (1.0 / a).all_close(a_inv)
        assert (a * (Matrix(shape, 1) / b)).all_close(a / b)
        assert (a * (1 / b)).all_close(a / b)
        assert (a * (1.0 / b)).all_close(a / b)

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
        b = Matrix((2, 2), (1, 0, 0, 1))

        assert a @ b == a
        assert a @ b == b @ a

    def test_dot_product_inverse(self):
        a = Matrix((2, 2), (4, 3, 2, 1))
        b = Matrix((2, 2), (-0.5, 1.5, 1, -2))

        assert a @ b == Matrix((2, 2), (1, 0, 0, 1))
        assert b @ a == Matrix((2, 2), (1, 0, 0, 1))

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

    def test_shape(self, shape):
        assert Matrix(shape).shape == shape
        assert Matrix(shape, transposed=True).shape == shape[::-1]
        with pytest.raises(AttributeError):
            Matrix(shape).shape = 1

    def test_transpose(self, shape):
        length = functools.reduce(operator.mul, shape)
        a = Matrix(shape, range(length))
        assert a == a.t.t
        assert a.shape == a.t.shape[::-1]
        for i, j in itertools.product(range(a.shape[0]), range(a.shape[1])):
            assert a[i, j] == a.t[j, i]

    def test_norm(self, shape):
        for p in range(1, 3):
            assert Matrix(shape, 1).norm(p) == math.pow(sum(functools.reduce(operator.mul, shape) * [math.pow(abs(1), p)]), 1/p)

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

    def test_to_bytes(self, ):
        assert Matrix((2, 3), (0, 1, 2, 3, 4, 5)).to_bytes() == b'\x00\x00\x00\x00\x00\x00\x80?\x00\x00\x00@\x00\x00@@\x00\x00\x80@\x00\x00\xa0@'

    def test_identity(self):
        for d in range(1, 5):
            assert Matrix.identity(d) == Matrix((d, d), [1 if i in range(0, d * d, d + 1) else 0 for i in range(d * d)])

    def test_translation(self):
        assert Matrix.translation(2, 2, 2) == Matrix((4, 4), (
            1, 0, 0, 2,
            0, 1, 0, 2,
            0, 0, 1, 2,
            0, 0, 0, 1
        ))

    def test_scaling(self):
        assert Matrix.scaling(2, 2, 2) == Matrix((4, 4), (
            2, 0, 0, 0,
            0, 2, 0, 0,
            0, 0, 2, 0,
            0, 0, 0, 1
        ))

    def test_orthographic(self):
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

    def test_ex(self):
        assert Matrix.ex() == Matrix((3, 1), (1, 0, 0))

    def test_ey(self):
        assert Matrix.ey() == Matrix((3, 1), (0, 1, 0))

    def test_ez(self):
        assert Matrix.ez() == Matrix((3, 1), (0, 0, 1))

    @pytest.mark.skip
    def test_from_iterable(self):
        data = (
            (0, 1),
            (2, 3)
        )

        assert Matrix.from_iterable(data) == Matrix((2, 2), range(4))

        data = (
            0, 1, 2, 3
        )

        assert Matrix.from_iterable(data) == Matrix((4, 1), range(4))

        data = (
            (0, 1),
            (0, 1, 2)
        )

        with pytest.raises(ValueError):
            Matrix.from_iterable(data)


@pytest.mark.skip
class TestQuaternion(object):
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


@pytest.mark.xfail
def test_euler_step():
    raise NotImplementedError()


@pytest.mark.xfail
def test_runge_kutta_4():
    raise NotImplementedError()


@pytest.mark.xfail
def test_velocity_verlet():
    raise NotImplementedError()


@pytest.mark.xfail
def test_equations_of_motion():
    raise NotImplementedError()


@pytest.mark.parametrize("N,M,t,idx,e", (
    (2, 3, False, (0, 0), (1, 1)),
    (2, 3, False, (0, (0, 1, 2)), (1, 3)),
    (2, 3, False, (0, slice(None, None, None)), (1, 3)),
    (2, 3, False, (0, 0), (1, 1)),
    (2, 3, False, ((0, 1), (0, 1, 2)), (2, 3)),
    (2, 3, False, ((0, 1), slice(None, None, None)), (2, 3)),
))
def test_get_sub_shape(N, M, t, idx, e):
    assert get_sub_shape(N, M, t, idx) == e


def test_benchmark_get_sub_shape(benchmark):
    assert benchmark(get_sub_shape, 2, 3, False, ((0, 1), slice(None, None, None))) == (2, 3)


@pytest.mark.parametrize("N,M,t,idx,e", (
    (2, 3, False, (0, 0), (0,)),
    (2, 3, False, (0, 1), (1,)),
    (2, 3, False, (0, 2), (2,)),
    (2, 3, False, (1, 0), (3,)),
    (2, 3, False, (1, 1), (4,)),
    (2, 3, False, (1, 2), (5,)),
    (2, 3, True, (0, 0), (0,)),
    (2, 3, True, (1, 0), (1,)),
    (2, 3, True, (2, 0), (2,)),
    (2, 3, True, (0, 1), (3,)),
    (2, 3, True, (1, 1), (4,)),
    (2, 3, True, (2, 1), (5,)),
    (2, 3, False, (0, (0,)), (0,)),
    (2, 3, False, (0, (0, 1)), (0, 1)),
    (2, 3, False, (0, (0, 1, 2)), (0, 1, 2)),
    (2, 3, False, (1, (0,)), (3,)),
    (2, 3, False, (1, (0, 1)), (3, 4)),
    (2, 3, False, (1, (0, 1, 2)), (3, 4, 5)),
    (2, 3, True, (0, (0,)), (0,)),
    (2, 3, True, (1, (0,)), (1,)),
    (2, 3, True, (2, (0,)), (2,)),
    (2, 3, True, (0, (0, 1)), (0, 3)),
    (2, 3, True, (1, (0, 1)), (1, 4)),
    (2, 3, True, (2, (0, 1)), (2, 5)),
    (2, 3, False, (0, slice(0, 1, 1)), (0,)),
    (2, 3, False, (0, slice(0, 2, 1)), (0, 1)),
    (2, 3, False, (0, slice(0, 3, 1)), (0, 1, 2)),
    (2, 3, False, (1, slice(0, 1, 1)), (3,)),
    (2, 3, False, (1, slice(0, 2, 1)), (3, 4)),
    (2, 3, False, (1, slice(0, 3, 1)), (3, 4, 5)),
    (2, 3, True, (0, slice(0, 1, 1)), (0,)),
    (2, 3, True, (1, slice(0, 1, 1)), (1,)),
    (2, 3, True, (2, slice(0, 1, 1)), (2,)),
    (2, 3, True, (0, slice(0, 2, 1)), (0, 3)),
    (2, 3, True, (1, slice(0, 2, 1)), (1, 4)),
    (2, 3, True, (2, slice(0, 2, 1)), (2, 5)),
    (2, 3, False, (0, slice(0, 1, 2)), (0,)),
    (2, 3, False, (0, slice(0, 2, 2)), (0,)),
    (2, 3, False, (0, slice(0, 3, 2)), (0, 2)),
    (2, 3, False, (1, slice(0, 1, 2)), (3,)),
    (2, 3, False, (1, slice(0, 2, 2)), (3,)),
    (2, 3, False, (1, slice(0, 3, 2)), (3, 5)),
    (2, 3, True, (0, slice(0, 1, 2)), (0,)),
    (2, 3, True, (1, slice(0, 1, 2)), (1,)),
    (2, 3, True, (2, slice(0, 1, 2)), (2,)),
    (2, 3, True, (0, slice(0, 2, 2)), (0,)),
    (2, 3, True, (1, slice(0, 2, 2)), (1,)),
    (2, 3, True, (2, slice(0, 2, 2)), (2,)),
    (2, 3, False, ((0,), 0), (0,)),
    (2, 3, False, ((0,), 1), (1,)),
    (2, 3, False, ((0,), 2), (2,)),
    (2, 3, False, ((0, 1), 0), (0, 3)),
    (2, 3, False, ((0, 1), 1), (1, 4)),
    (2, 3, False, ((0, 1), 2), (2, 5)),
    (2, 3, True, ((0,), 0), (0,)),
    (2, 3, True, ((0, 1), 0), (0, 1)),
    (2, 3, True, ((0, 1, 2), 0), (0, 1, 2)),
    (2, 3, True, ((0,), 1), (3,)),
    (2, 3, True, ((0, 1), 1), (3, 4)),
    (2, 3, True, ((0, 1, 2), 1), (3, 4, 5)),
    (2, 3, False, ((0,), (0,)), (0,)),
    (2, 3, False, ((0,), (0, 1)), (0, 1)),
    (2, 3, False, ((0,), (0, 1, 2)), (0, 1, 2)),
    (2, 3, False, ((0, 1), (0,)), (0, 3)),
    (2, 3, False, ((0, 1), (0, 1)), (0, 1, 3, 4)),
    (2, 3, False, ((0, 1), (0, 1, 2)), (0, 1, 2, 3, 4, 5)),
    (2, 3, True, ((0,), (0,)), (0,)),
    (2, 3, True, ((0, 1), (0,)), (0, 1)),
    (2, 3, True, ((0, 1, 2), (0,)), (0, 1, 2)),
    (2, 3, True, ((0,), (0, 1)), (0, 3)),
    (2, 3, True, ((0, 1), (0, 1)), (0, 3, 1, 4)),
    (2, 3, True, ((0, 1, 2), (0, 1)), (0, 3, 1, 4, 2, 5)),
    (2, 3, False, ((0,), slice(0, 1, 1)), (0,)),
    (2, 3, False, ((0,), slice(0, 2, 1)), (0, 1)),
    (2, 3, False, ((0,), slice(0, 3, 1)), (0, 1, 2)),
    (2, 3, False, ((0, 1), slice(0, 1, 1)), (0, 3)),
    (2, 3, False, ((0, 1), slice(0, 2, 1)), (0, 1, 3, 4)),
    (2, 3, False, ((0, 1), slice(0, 3, 1)), (0, 1, 2, 3, 4, 5)),
    (2, 3, True, ((0,), slice(0, 1, 1)), (0,)),
    (2, 3, True, ((0, 1), slice(0, 1, 1)), (0, 1)),
    (2, 3, True, ((0, 1, 2), slice(0, 1, 1)), (0, 1, 2)),
    (2, 3, True, ((0,), slice(0, 2, 1)), (0, 3)),
    (2, 3, True, ((0, 1), slice(0, 2, 1)), (0, 3, 1, 4)),
    (2, 3, True, ((0, 1, 2), slice(0, 2, 1)), (0, 3, 1, 4, 2, 5)),
    (2, 3, False, ((0,), slice(0, 1, 2)), (0,)),
    (2, 3, False, ((0,), slice(0, 2, 2)), (0,)),
    (2, 3, False, ((0,), slice(0, 3, 2)), (0, 2)),
    (2, 3, False, ((0, 1), slice(0, 1, 2)), (0, 3)),
    (2, 3, False, ((0, 1), slice(0, 2, 2)), (0, 3)),
    (2, 3, False, ((0, 1), slice(0, 3, 2)), (0, 2, 3, 5)),
    (2, 3, True, ((0,), slice(0, 1, 2)), (0,)),
    (2, 3, True, ((0, 1), slice(0, 1, 2)), (0, 1)),
    (2, 3, True, ((0, 1, 2), slice(0, 1, 2)), (0, 1, 2)),
    (2, 3, True, ((0,), slice(0, 2, 2)), (0,)),
    (2, 3, True, ((0, 1), slice(0, 2, 2)), (0, 1)),
    (2, 3, True, ((0, 1, 2), slice(0, 2, 2)), (0, 1, 2)),
    (2, 3, False, (slice(0, 1, 1), 0), (0,)),
    (2, 3, False, (slice(0, 1, 1), 1), (1,)),
    (2, 3, False, (slice(0, 1, 1), 2), (2,)),
    (2, 3, False, (slice(0, 2, 1), 0), (0, 3)),
    (2, 3, False, (slice(0, 2, 1), 1), (1, 4)),
    (2, 3, False, (slice(0, 2, 1), 2), (2, 5)),
    (2, 3, True, (slice(0, 1, 1), 0), (0,)),
    (2, 3, True, (slice(0, 2, 1), 0), (0, 1)),
    (2, 3, True, (slice(0, 3, 1), 0), (0, 1, 2)),
    (2, 3, True, (slice(0, 1, 1), 1), (3,)),
    (2, 3, True, (slice(0, 2, 1), 1), (3, 4)),
    (2, 3, True, (slice(0, 3, 1), 1), (3, 4, 5)),
    (2, 3, False, (slice(0, 1, 2), 0), (0,)),
    (2, 3, False, (slice(0, 1, 2), 1), (1,)),
    (2, 3, False, (slice(0, 1, 2), 2), (2,)),
    (2, 3, False, (slice(0, 2, 2), 0), (0,)),
    (2, 3, False, (slice(0, 2, 2), 1), (1,)),
    (2, 3, False, (slice(0, 2, 2), 2), (2,)),
    (2, 3, True, (slice(0, 1, 2), 0), (0,)),
    (2, 3, True, (slice(0, 2, 2), 0), (0,)),
    (2, 3, True, (slice(0, 3, 2), 0), (0, 2)),
    (2, 3, True, (slice(0, 1, 2), 1), (3,)),
    (2, 3, True, (slice(0, 2, 2), 1), (3,)),
    (2, 3, True, (slice(0, 3, 2), 1), (3, 5)),
    (2, 3, False, (slice(0, 1, 1), (0,)), (0,)),
    (2, 3, False, (slice(0, 1, 1), (0, 1)), (0, 1)),
    (2, 3, False, (slice(0, 1, 1), (0, 1, 2)), (0, 1, 2)),
    (2, 3, False, (slice(0, 2, 1), (0,)), (0, 3)),
    (2, 3, False, (slice(0, 2, 1), (0, 1)), (0, 1, 3, 4)),
    (2, 3, False, (slice(0, 2, 1), (0, 1, 2)), (0, 1, 2, 3, 4, 5)),
    (2, 3, True, (slice(0, 1, 1), (0,)), (0,)),
    (2, 3, True, (slice(0, 2, 1), (0,)), (0, 1)),
    (2, 3, True, (slice(0, 3, 1), (0,)), (0, 1, 2)),
    (2, 3, True, (slice(0, 1, 1), (0, 1)), (0, 3)),
    (2, 3, True, (slice(0, 2, 1), (0, 1)), (0, 3, 1, 4)),
    (2, 3, True, (slice(0, 3, 1), (0, 1)), (0, 3, 1, 4, 2, 5)),
    (2, 3, False, (slice(0, 1, 2), (0,)), (0,)),
    (2, 3, False, (slice(0, 1, 2), (0, 1)), (0, 1)),
    (2, 3, False, (slice(0, 1, 2), (0, 1, 2)), (0, 1, 2)),
    (2, 3, False, (slice(0, 2, 2), (0,)), (0,)),
    (2, 3, False, (slice(0, 2, 2), (0, 1)), (0, 1)),
    (2, 3, False, (slice(0, 2, 2), (0, 1, 2)), (0, 1, 2)),
    (2, 3, True, (slice(0, 1, 2), (0,)), (0,)),
    (2, 3, True, (slice(0, 2, 2), (0,)), (0,)),
    (2, 3, True, (slice(0, 3, 2), (0,)), (0, 2)),
    (2, 3, True, (slice(0, 1, 2), (0, 1)), (0, 3)),
    (2, 3, True, (slice(0, 2, 2), (0, 1)), (0, 3)),
    (2, 3, True, (slice(0, 3, 2), (0, 1)), (0, 3, 2, 5)),
    (2, 3, False, (slice(0, 1, 1), slice(0, 1, 1)), (0,)),
    (2, 3, False, (slice(0, 1, 1), slice(0, 2, 1)), (0, 1)),
    (2, 3, False, (slice(0, 1, 1), slice(0, 3, 1)), (0, 1, 2)),
    (2, 3, False, (slice(0, 2, 1), slice(0, 1, 1)), (0, 3)),
    (2, 3, False, (slice(0, 2, 1), slice(0, 2, 1)), (0, 1, 3, 4)),
    (2, 3, False, (slice(0, 2, 1), slice(0, 3, 1)), (0, 1, 2, 3, 4, 5)),
    (2, 3, True, (slice(0, 1, 1), slice(0, 1, 1)), (0,)),
    (2, 3, True, (slice(0, 2, 1), slice(0, 1, 1)), (0, 1)),
    (2, 3, True, (slice(0, 3, 1), slice(0, 1, 1)), (0, 1, 2)),
    (2, 3, True, (slice(0, 1, 1), slice(0, 2, 1)), (0, 3)),
    (2, 3, True, (slice(0, 2, 1), slice(0, 2, 1)), (0, 3, 1, 4)),
    (2, 3, True, (slice(0, 3, 1), slice(0, 2, 1)), (0, 3, 1, 4, 2, 5)),
    (2, 3, False, (slice(0, 1, 2), slice(0, 1, 2)), (0,)),
    (2, 3, False, (slice(0, 1, 2), slice(0, 2, 2)), (0,)),
    (2, 3, False, (slice(0, 1, 2), slice(0, 3, 2)), (0, 2)),
    (2, 3, False, (slice(0, 2, 2), slice(0, 1, 2)), (0,)),
    (2, 3, False, (slice(0, 2, 2), slice(0, 2, 2)), (0,)),
    (2, 3, False, (slice(0, 2, 2), slice(0, 3, 2)), (0, 2)),
    (2, 3, True, (slice(0, 1, 2), slice(0, 1, 2)), (0,)),
    (2, 3, True, (slice(0, 2, 2), slice(0, 1, 2)), (0,)),
    (2, 3, True, (slice(0, 3, 2), slice(0, 1, 2)), (0, 2)),
    (2, 3, True, (slice(0, 1, 2), slice(0, 2, 2)), (0,)),
    (2, 3, True, (slice(0, 2, 2), slice(0, 2, 2)), (0,)),
    (2, 3, True, (slice(0, 3, 2), slice(0, 2, 2)), (0, 2)),
    (2, 3, False, (slice(None, None, None), slice(None, None, None)), (0, 1, 2, 3, 4, 5)),
    (2, 3, True, (slice(None, None, None), slice(None, None, None)), (0, 3, 1, 4, 2, 5)),
))
def test_linearize_indices(N, M, t, idx, e):
    assert linearize_indices(N, M, t, idx) == e


def test_benchmark_linearize_indices(benchmark):
    assert benchmark(linearize_indices, 2, 3, True, (slice(None, None, None), slice(None, None, None))) == (0, 3, 1, 4, 2, 5)


@pytest.mark.parametrize("idx,e", (
    (0, (0, slice(None, None, None))),
    (((0, 1),), ((0, 1), slice(None, None, None))),
    (slice(None, None, None), (slice(None, None, None), slice(None, None, None))),
))
def test_complete_indices(idx, e):
    assert complete_indices(idx) == e


def test_benchmark_complete_indices(benchmark):
    assert benchmark(complete_indices, slice(None, None, None)) == (slice(None, None, None), slice(None, None, None))


@pytest.mark.parametrize("N,M,t,e", (
    (2, 3, False, (0, 1, 2, 3, 4, 5)),
    (2, 3, True, (0, 3, 1, 4, 2, 5)),
))
def test_select_all(N, M, t, e):
    assert select_all(N, M, t) == e


def test_benchmark_select_all(benchmark):
    assert benchmark(select_all, 2, 3, True) == (0, 3, 1, 4, 2, 5)