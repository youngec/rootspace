# -*- coding: utf-8 -*-

import collections.abc
import math
import array
import functools
import operator
import itertools

import numpy

from .utilities import get_sub_shape, linearize_indices


def identity():
    return numpy.eye(4)


def translation(vect):
    tra = numpy.eye(4)
    tra[:3, 3] = vect
    return tra


def orthographic(left, right, bottom, top, near, far):
    l = left
    r = right
    b = bottom
    t = top
    n = near
    f = far

    return numpy.array((
        (2 / (r - l),           0,            0, -(r + l) / (r - l)),
        (          0, 2 / (t - b),            0, -(t + b) / (t - b)),
        (          0,           0, -2 / (f - n), -(f + n) / (f - n)),
        (          0,           0,            0,                  1)
    ))


def perspective(field_of_view, viewport_ratio, near, far):
    a = viewport_ratio
    t = math.tanh(field_of_view / 2)
    n = near
    f = far
    y_scale = 1 / math.tan(field_of_view / 2)
    x_scale = y_scale / viewport_ratio
    z_sum = near + far
    z_diff = near - far
    z_prod = near * far

    return numpy.array((
        (x_scale, 0, 0, 0),
        (0, y_scale, 0, 0),
        (0, 0, z_sum / z_diff, 2 * z_prod / z_diff),
        (0, 0, -1, 0)
    ))


def all_close(a, b, rel_tol=1e-05, abs_tol=1e-08):
    if hasattr(a, "all_close"):
        return a.all_close(b, rel_tol, abs_tol)
    elif hasattr(b, "all_close"):
        return b.all_close(a, rel_tol, abs_tol)
    else:
        raise TypeError("unsupported operand type(s) for all_close() '{}' and '{}'".format(type(a), type(b)))


class Matrix(object):
    """
    The base class for Matrices of real numbers. The internal data structure uses row-major ordering.
    """
    @classmethod
    def identity(cls, d):
        """
        Return an identity matrix of shape d x d.

        :param d:
        :return:
        """
        return cls((d, d))

    @classmethod
    def translation(cls, t_x, t_y, t_z):
        """
        Return an affine translation Matrix.

        :param t_x:
        :param t_y:
        :param t_z:
        :return:
        """
        return cls((4, 4), (
            1, 0, 0, t_x,
            0, 1, 0, t_y,
            0, 0, 1, t_z,
            0, 0, 0, 1
        ))

    @classmethod
    def rotation_x(cls, angle):
        """
        Return an affine rotation matrix about the x-axis.

        :param angle:
        :return:
        """
        c = math.cos(angle)
        s = math.sin(angle)
        return cls((4, 4), (
            1, 0, 0, 0,
            0, c, -s, 0,
            0, s, c, 0,
            0, 0, 0, 1
        ))

    @classmethod
    def rotation_y(cls, angle):
        """
        Return an affine rotation matrix about the y-axis.

        :param angle:
        :return:
        """
        c = math.cos(angle)
        s = math.sin(angle)
        return cls((4, 4), (
            c, 0, s, 0,
            0, 1, 0, 0,
            -s, 0, c, 0,
            0, 0, 0, 1
        ))

    @classmethod
    def rotation_z(cls, angle):
        """
        Return an affine rotation matrix about the z-axis.

        :param angle:
        :return:
        """
        c = math.cos(angle)
        s = math.sin(angle)
        return cls((4, 4), (
            c, -s, 0, 0,
            s, c, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1
        ))

    @classmethod
    def scaling(cls, s_x, s_y, s_z):
        """
        Return an affine scaling matrix.

        :param s_x:
        :param s_y:
        :param s_z:
        :return:
        """
        return cls((4, 4), (
            s_x, 0, 0, 0,
            0, s_y, 0, 0,
            0, 0, s_z, 0,
            0, 0, 0, 1
        ))

    @classmethod
    def shearing(cls, s, i, j):
        """
        Return an affine shearing matrix.

        :param s:
        :param i:
        :param j:
        :return:
        """
        h = cls.identity(4)
        h[i, j] = s
        return h

    @classmethod
    def orthographic(cls, left, right, bottom, top, near, far):
        """
        Create an orthographic projection matrix.

        :param left:
        :param right:
        :param bottom:
        :param top:
        :param near:
        :param far:
        :return:
        """
        l = left
        r = right
        b = bottom
        t = top
        n = near
        f = far
        return cls((4, 4), (
            2 / (r - l), 0, 0, -(r + l) / (r - l),
            0, 2 / (t - b), 0, -(t + b) / (t - b),
            0, 0, -2 / (f - n), -(f + n) / (f - n),
            0, 0, 0, 1
        ))

    @classmethod
    def perspective(cls, field_of_view, viewport_ratio, near, far):
        """
        Create a perspective projection matrix.

        :param field_of_view:
        :param viewport_ratio:
        :param near:
        :param far:
        :return:
        """
        y_scale = 1 / math.tan(field_of_view / 2)
        x_scale = y_scale / viewport_ratio
        z_sum = near + far
        z_diff = near - far
        z_prod = near * far

        return cls((4, 4), (
            x_scale, 0, 0, 0,
            0, y_scale, 0, 0,
            0, 0, z_sum / z_diff, 2 * z_prod / z_diff,
            0, 0, -1, 0
        ))

    @property
    def shape(self):
        return self._shape if not self._transposed else self._shape[::-1]

    @property
    def data(self):
        return self._data

    @property
    def is_square(self):
        return functools.reduce(operator.eq, self.shape)

    @property
    def is_vector(self):
        return len([None for s in self.shape if s > 1]) == 1

    @property
    def is_column_vector(self):
        return self.is_vector and self.shape[0] > 1

    @property
    def is_row_vector(self):
        return self.is_vector and self.shape[0] == 1

    @property
    def is_scalar(self):
        return len(self) == 1

    @property
    def t(self):
        return Matrix(self._shape, self.data, transposed=(not self._transposed))

    def is_close(self, other, rel_tol=1e-05, abs_tol=1e-08):
        """
        Perform an element-wise approximate equality comparison.

        :param other:
        :param rel_tol:
        :param abs_tol:
        :return:
        """
        if isinstance(other, Matrix):
            if self.shape == other.shape:
                result = Matrix(self.shape, 0, data_type="B")
                for i, j in itertools.product(range(result.shape[0]), range(result.shape[1])):
                    result[i, j] = math.isclose(self[i, j], other[i, j], rel_tol=rel_tol, abs_tol=abs_tol)
                return result
            else:
                raise ValueError("Shape mismatch: '{}' must be equal to '{}'".format(self.shape, other.shape))
        elif isinstance(other, (int, float)):
            result = Matrix(self.shape, 0, data_type="B")
            for i, j in itertools.product(range(result.shape[0]), range(result.shape[1])):
                result[i, j] = math.isclose(self[i, j], other, rel_tol=rel_tol, abs_tol=abs_tol)
            return result
        else:
            raise TypeError("unsupported operand type(s) for is_close() '{}' and '{}'".format(type(self), type(other)))

    def all_close(self, other, rel_tol=1e-05, abs_tol=1e-08):
        """
        Return True if all elements compare approximately equal, False otherwise.

        :param other:
        :param rel_tol:
        :param abs_tol:
        :return:
        """
        return all(self.is_close(other, rel_tol, abs_tol))

    def norm(self):
        """
        Rwturn the L2 norm for a vector.

        :return:
        """
        return math.sqrt(self.t @ self)

    def cross(self, other):
        """
        Calculate the cross-product of two vectors.

        :param other:
        :return:
        """
        if isinstance(other, Matrix) and self.is_vector and other.is_vector and len(self) == 3 and len(other) == 3:
            s = self
            if self.is_row_vector:
                s = self.t

            o = other
            if self.is_row_vector:
                o = other.t

            return Matrix(self.shape, (
                s[1] * o[2] - s[2] * o[1],
                s[2] * o[0] - s[0] * o[2],
                s[0] * o[1] - s[1] * o[0]
            ))
        else:
            raise TypeError("unsupported operand type(s) for cross() '{}' and '{}'".format(type(self), type(other)))

    def __init__(self, shape, data=None, data_type="f", transposed=False):
        """
        Create a Matrix instance from a shape and either an iterable, a scalar number, or no arguments.
        Using only the shape creates an identity matrix if the shape is square.

        :param shape:
        :param data:
        :param data_type:
        :param transposed:
        """
        self._transposed = transposed

        # Set the shape of the matrix
        if isinstance(shape, tuple) and len(shape) == 2 and all(isinstance(s, int) and s > 0 for s in shape):
            self._shape = shape
        else:
            raise ValueError("The parameter 'shape' must be a 2-tuple of positive integers.")

        # Set the matrix data
        length = shape[0] * shape[1]
        if data is not None:
            if isinstance(data, array.ArrayType):
                self._data = data
                if len(self._data) != length:
                    raise ValueError("Expected an ArrayType of length '{}', got '{}'.".format(length, len(self._data)))
            elif isinstance(data, collections.abc.Iterable):
                self._data = array.array(data_type, data)
                if len(self._data) != length:
                    raise ValueError("Expected an iterable of length '{}', got '{}'.".format(length, len(self._data)))
            elif isinstance(data, (int, float)):
                self._data = array.array(data_type, length * [data])
            else:
                raise TypeError("Expected either an ArrayType, an iterable or a scalar number as positional argument.")
        elif data is None:
            if shape[0] == shape[1]:
                self._data = array.array(data_type, (1 if i in range(0, length, shape[0] + 1) else 0 for i in range(length)))
            else:
                self._data = array.array(data_type, (0 for _ in range(length)))
        else:
            raise ValueError("Expected an iterable of length '{0}' or a scalar number.".format(length))

    def __str__(self):
        """
        Return a human-readable representation.

        :return:
        """
        lines = list()
        for i in range(self.shape[0]):
            lines.append("[{}]".format(", ".join(str(e) for e in self[i, :])))
        return "[{}]".format("\n ".join(lines))

    def __repr__(self):
        """
        Return a eval-compatible representation.

        :return:
        """
        return "{}({}, ({}), data_type={}, transposed={})".format(
            self.__class__.__name__, self._shape, ", ".join(str(e) for e in self),
            self._data.typecode, self._transposed
        )

    def __bytes__(self):
        """
        Return a bytes representation of the matrix.

        :return:
        """
        return self._data.tobytes()

    def __len__(self):
        """
        Return the number of matrix elements.

        :return:
        """
        return functools.reduce(operator.mul, self._shape)

    def __iter__(self):
        """
        Provide an iterator interface.

        :return:
        """
        for d in self._data:
            yield d

    def __reversed__(self):
        """
        Provide a reverse iterator.

        :return:
        """
        for d in reversed(self._data):
            yield d

    def __contains__(self, item):
        """
        Provide the contains interface.

        :param item:
        :return:
        """
        return item in self._data

    def __getitem__(self, key):
        """
        Provide angle-bracket element access to the matrix.

        :param key:
        :return:
        """
        if isinstance(key, (int, slice)):
            key = (key, slice(None))

        if isinstance(key, tuple):
            key = key if not self._transposed else key[::-1]
            sub_shape = get_sub_shape(self._shape, *key)
            sub_idx = linearize_indices(self._shape, *key)
            d = Matrix(sub_shape, self._data[sub_idx])
            if d.is_scalar:
                return d.data[0]
            else:
                return d
        else:
            raise TypeError("Expected indices of type int, slice or tuple.")

    def __setitem__(self, key, value):
        """
        Provide angle-bracket element setting to the matrix.

        :param key:
        :param value:
        :return:
        """
        if isinstance(key, (int, slice)):
            key = (key, slice(None))

        if isinstance(key, tuple):
            key = key if not self._transposed else key[::-1]
            sub_shape = get_sub_shape(self._shape, *key)
            sub_idx = linearize_indices(self._shape, *key)
            if isinstance(value, Matrix) and value.shape == sub_shape:
                self._data[sub_idx] = value.data
            elif isinstance(value, collections.abc.Collection) and len(value) == functools.reduce(operator.mul, sub_shape):
                self._data[sub_idx] = array.array(self.data.typecode, value)
            elif isinstance(value, (int, float)) and sub_shape == (1, 1):
                self._data[sub_idx] = value
            else:
                raise ValueError("The shape/length of the value must equal the shape/length of the indexed range.")
        else:
            raise TypeError("Expected indices of type int, slice or tuple, not '{}'.".format(type(key)))

    def __eq__(self, other):
        """

        :param other:
        :return:
        """
        if isinstance(other, Matrix):
            return self.shape == other.shape and all(s == o for s, o in zip(self, other))
        else:
            return NotImplemented

    def __neg__(self):
        """
        Perform an element-wise negation.

        :return:
        """
        result = Matrix(self.shape, 0)
        for i, j in itertools.product(range(result.shape[0]), range(result.shape[1])):
            result[i, j] = -self[i, j]
        return result

    def __pos__(self):
        """
        Perform an element-wise positive unary operation.

        :return:
        """
        result = Matrix(self.shape, 0)
        for i, j in itertools.product(range(result.shape[0]), range(result.shape[1])):
            result[i, j] = +self[i, j]
        return result

    def __add__(self, other):
        """
        Perform a left-sided element-wise addition.

        :param other:
        :return:
        """
        if isinstance(other, Matrix):
            if self.shape == other.shape:
                result = Matrix(self.shape, 0)
                for i, j in itertools.product(range(result.shape[0]), range(result.shape[1])):
                    result[i, j] = self[i, j] + other[i, j]
                return result
            else:
                raise ValueError("Shape mismatch: '{}' must be equal to '{}'".format(self.shape, other.shape))
        elif isinstance(other, (int, float)):
            result = Matrix(self.shape, 0)
            for i, j in itertools.product(range(result.shape[0]), range(result.shape[1])):
                result[i, j] = self[i, j] + other
            return result
        else:
            return NotImplemented

    def __radd__(self, other):
        """
        Perform a right-sided element-wise addition. Equivalent to __add__.

        :param other:
        :return:
        """
        return self.__add__(other)

    def __sub__(self, other):
        """
        Perform a left-sided element-wise subtraction.

        :param other:
        :return:
        """
        return self + -other

    def __rsub__(self, other):
        """
        Perform a right-sided element-wise subtraction.

        :param other:
        :return:
        """
        return other + -self

    def __mul__(self, other):
        """
        Perform a left-sided element-wise multiplication.

        :param other:
        :return:
        """
        if isinstance(other, Matrix):
            if self.shape == other.shape:
                result = Matrix(self.shape, 0)
                for i, j in itertools.product(range(result.shape[0]), range(result.shape[1])):
                    result[i, j] = self[i, j] * other[i, j]
                return result
            else:
                raise ValueError("Shape mismatch: '{}' must be equal to '{}'".format(self.shape, other.shape))
        elif isinstance(other, (int, float)):
            result = Matrix(self.shape, 0)
            for i, j in itertools.product(range(result.shape[0]), range(result.shape[1])):
                result[i, j] = self[i, j] * other
            return result
        else:
            return NotImplemented

    def __rmul__(self, other):
        """
        Perform a right-sided element-wise multiplication. Equivalent to __mul__.

        :param other:
        :return:
        """
        return self.__mul__(other)

    def __truediv__(self, other):
        """
        Perform a left-sided element-wise division.

        :param other:
        :return:
        """
        if isinstance(other, Matrix):
            if self.shape == other.shape:
                result = Matrix(self.shape, 0)
                for i, j in itertools.product(range(result.shape[0]), range(result.shape[1])):
                    result[i, j] = self[i, j] / other[i, j]
                return result
            else:
                raise ValueError("Shape mismatch: '{}' must be equal to '{}'".format(self.shape, other.shape))
        elif isinstance(other, (int, float)):
            result = Matrix(self.shape, 0)
            for i, j in itertools.product(range(result.shape[0]), range(result.shape[1])):
                result[i, j] = self[i, j] / other
            return result
        else:
            return NotImplemented

    def __rtruediv__(self, other):
        """
        Perform a right-sided element wise division.

        :param other:
        :return:
        """
        if isinstance(other, Matrix):
            if self.shape == other.shape:
                result = Matrix(self.shape, 0)
                for i, j in itertools.product(range(result.shape[0]), range(result.shape[1])):
                    result[i, j] = other[i, j] / self[i, j]
                return result
            else:
                raise ValueError("Shape mismatch: '{}' must be equal to '{}'".format(self.shape, other.shape))
        elif isinstance(other, (int, float)):
            result = Matrix(self.shape, 0)
            for i, j in itertools.product(range(result.shape[0]), range(result.shape[1])):
                result[i, j] = other / self[i, j]
            return result
        else:
            return NotImplemented

    def __matmul__(self, other):
        """
        Perform a left-sided matrix multiplication.

        :param other:
        :return:
        """
        if isinstance(other, Matrix):
            if self.shape[-1] == other.shape[0] and self.shape[-1] > 1:
                result_shape = self.shape[:-1] + other.shape[1:]
                if result_shape == (1, 1):
                    return sum(a * b for a, b in zip(self, other))
                else:
                    result = Matrix(result_shape, 0)
                    for i, j in itertools.product(range(result.shape[0]), range(result.shape[1])):
                        result[i, j] = sum(a * b for a, b in zip(self[i, :], other[:, j]))

                    return result
            else:
                raise ValueError("Last dimension of '{}' and first dimension of '{}' do not match or are 1.".format(self.shape, other.shape))
        else:
            return NotImplemented


class Quaternion(object):
    """
    The Quaternion class provides a way to work with four-dimensional complex numbers.
    """
    def __init__(self, *args, data_type="f"):
        """
        Create a Vector instance from either a iterable, or positional arguments.

        :param args:
        :param data_type:
        """
        if len(args) == 1 and isinstance(args[0], collections.abc.Iterable):
            data = tuple(args[0])
        else:
            data = args

        if len(data) == 0:
            data = (1, 0, 0, 0)
        elif len(data) != 4:
            raise ValueError("Expected a four-element iterable as first argument, or four scalar values as positional arguments.")

        self._data = array.array(data_type, epsilon(*data, iterable=True))

    @property
    def r(self):
        return self._data[0]

    @r.setter
    def r(self, value):
        self._data[0] = epsilon(value)

    @property
    def i(self):
        return self._data[1]

    @i.setter
    def i(self, value):
        self._data[1] = epsilon(value)

    @property
    def j(self):
        return self._data[2]

    @j.setter
    def j(self, value):
        self._data[2] = epsilon(value)

    @property
    def k(self):
        return self._data[3]

    @k.setter
    def k(self, value):
        self._data[3] = epsilon(value)

    @property
    def t(self):
        """
        Return the conjugate of the Quaternion.

        :return:
        """
        return Quaternion(self.r, -self.i, -self.j, -self.k)

    @property
    def matrix3(self):
        r = self.r
        i = self.i
        j = self.j
        k = self.k

        return numpy.array((
            (1 - 2 * (j**2 + k**2), 2 * (i*j - k*r), 2 * (i*k + j*r)),
            (2 * (i*j + k*r), 1 - 2 * (i**2 + k**2), 2 * (j*k - i*r)),
            (2 * (i*k - j*r), 2 * (j*k + i*r), 1 - 2 * (i**2 + j**2))
        ))

    @property
    def matrix4(self):
        q = numpy.eye(4)
        q[:3, :3] = self.matrix3
        return q

    def to_bytes(self):
        """
        Return a bytes-based representation of the Quaternion.

        :return:
        """
        return self._data.tobytes()

    def normalize(self, inplace=True):
        """
        Normalize the Quaternion. If inplace is false, return a new, normalized Quaternion.

        :param inplace:
        :return:
        """
        n = self / abs(self)
        if inplace:
            self[:] = n[:]
        else:
            return n

    def __getitem__(self, item):
        """
        Access the Quaternion components by index.

        :param item:
        :return:
        """
        return self._data[item]

    def __setitem__(self, key, value):
        """
        Set the Quaternion components by index.

        :param key:
        :param value:
        :return:
        """
        self._data[key] = epsilon(value)

    def __repr__(self):
        """
        Return a representation of a Quaternion that can be evaluated as code.

        :return:
        """
        return "{}({})".format(self.__class__.__name__, ", ".join(str(e) for e in self._data))

    def __str__(self):
        """
        Return a printable representation of a Quaternion.

        :return:
        """
        return "{} + {}i + {}j + {}k".format(*self._data)

    def __iter__(self):
        """
        Iterate over the Vector.

        :return:
        """
        for e in self._data:
            yield e

    def __len__(self):
        """
        Return the dimensionality of the Vector.

        :return:
        """
        return len(self._data)

    def __eq__(self, other):
        """
        Return equal if all elements of the Quaternion are equal.

        :param other:
        :return:
        """
        if isinstance(other, Quaternion):
            return len(self) == len(other) and all(s == o for s, o in zip(self, other))
        else:
            return False

    def __abs__(self):
        """
        Return the L2 norm of the Quaternion.

        :return:
        """
        a = self @ self.t
        return math.sqrt(a.r)

    def __add__(self, other):
        """
        Perform an addition.

        :param other:
        :return:
        """
        if isinstance(other, Quaternion):
            return Quaternion(s + o for s, o in zip(self, other))
        elif isinstance(other, (int, float)):
            return Quaternion(s + other for s in self)
        else:
            raise TypeError("unsupported operand type(s) for +: '{}' and '{}'".format(Quaternion, type(other)))

    def __radd__(self, other):
        """
        Perform a right-sided addition. Equivalent to left-sided.

        :param other:
        :return:
        """
        return self.__add__(other)

    def __sub__(self, other):
        """
        Perform a subtraction.

        :param other:
        :return:
        """
        if isinstance(other, Quaternion):
            return Quaternion(s - o for s, o in zip(self, other))
        elif isinstance(other, (int, float)):
            return Quaternion(s - other for s in self)
        else:
            raise TypeError("unsupported operand type(s) for -: '{}' and '{}'".format(Quaternion, type(other)))

    def __rsub__(self, other):
        """
        Perform a right-sided subtraction.

        :param other:
        :return:
        """
        if isinstance(other, Quaternion):
            return Quaternion(o - s for s, o in zip(self, other))
        elif isinstance(other, (int, float)):
            return Quaternion(other - s for s in self)
        else:
            raise TypeError("unsupported operand type(s) for -: '{}' and '{}'".format(type(other), Quaternion))

    def __mul__(self, other):
        """
        Perform an element-wise multiplication.

        :param other:
        :return:
        """
        if isinstance(other, Quaternion):
            return Quaternion(s * o for s, o in zip(self, other))
        elif isinstance(other, (int, float)):
            return Quaternion(s * other for s in self)
        else:
            raise TypeError("unsupported operand type(s) for *: '{}' and '{}'".format(Quaternion, type(other)))

    def __rmul__(self, other):
        """
        Perform a right-sided element-wise multiplication. Equivalent to left-sided.

        :param other:
        :return:
        """
        return self.__mul__(other)

    def __truediv__(self, other):
        """
        Perform an element-wise division.

        :param other:
        :return:
        """
        if isinstance(other, Quaternion):
            return Quaternion(s / o for s, o in zip(self, other))
        elif isinstance(other, (int, float)):
            return Quaternion(s / other for s in self)
        else:
            raise TypeError("unsupported operand type(s) for /: '{}' and '{}'".format(Quaternion, type(other)))

    def __rtruediv__(self, other):
        """
        Perform a right-sided element-wise division.

        :param other:
        :return:
        """
        if isinstance(other, Quaternion):
            return Quaternion(o / s for s, o in zip(self, other))
        elif isinstance(other, (int, float)):
            return Quaternion(other / s for s in self)
        else:
            raise TypeError("unsupported operand type(s) for /: '{}' and '{}'".format(type(other), Quaternion))

    def __matmul__(self, other):
        """
        Perform a quaternion multiplication.

        :param other:
        :return:
        """
        if isinstance(other, Quaternion):
            return Quaternion(
                self.r * other.r - self.i * other.i - self.j * other.j - self.k * other.k,
                self.r * other.i + self.i * other.r + self.j * other.k - self.k * other.j,
                self.r * other.j - self.i * other.k + self.j * other.r + self.k * other.i,
                self.r * other.k + self.i * other.j - self.j * other.i + self.k * other.r
            )
        else:
            raise TypeError("unsupported operand type(s) for @: '{}' and '{}'".format(type(self), type(other)))

    @classmethod
    def from_axis(cls, axis, angle):
        axis = numpy.array(axis)
        axis /= numpy.linalg.norm(axis)
        angle %= 2 * math.pi

        sin = math.sin(angle / 2)
        return cls(
            math.cos(angle / 2),
            axis[0] * sin, 
            axis[1] * sin, 
            axis[2] * sin
        )

    @classmethod
    def look_at(cls, source, target, up_direction):
        """
        Construct a Quaternion from a source position, a target position, and a locked up position.

        :param source:
        :param target:
        :param up_direction:
        :return:
        """
        difference = source - target
        difference /= numpy.linalg.norm(difference)

        right_direction = numpy.cross(up_direction, difference)
        right_direction /= numpy.linalg.norm(right_direction)

        angle = math.acos(up_direction @ difference)

        return cls.from_axis(right_direction, angle)
