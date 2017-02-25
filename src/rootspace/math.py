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

    def determinant(self):
        """
        Calculate the determinant.

        :return:
        """
        def det2(a):
            return a[0, 0] * a[1, 1] - a[0, 1] * a[1, 0]

        def det3(a):
            return a[0, 0] * det2(a[1:3, 1:3]) - \
                   a[0, 1] * det2(a[1:3, 0:3:2]) + \
                   a[0, 2] * det2(a[1:3, 0:2])

        def det4(a):
            return a[0, 0] * det3(a[1:4, 1:4]) - \
                   a[0, 1] * det3(a[1:4, (0, 2, 3)]) + \
                   a[0, 2] * det3(a[1:4, (0, 1, 3)]) - \
                   a[0, 3] * det3(a[1:4, 0:3])

        if self.is_square and not self.is_scalar:
            if self.shape[0] == 2:
                return det2(self)
            elif self.shape[0] == 3:
                return det3(self)
            elif self.shape[0] == 4:
                return det4(self)
            else:
                raise NotImplementedError("Cannot calculate the determinant for dimensions larger than 4x4.")
        else:
            raise ValueError("The determinant is not defined for non-square matrices or scalar matrices.")

    def norm(self):
        """
        Return the L2 norm for a vector.

        :return:
        """
        raise NotImplementedError()

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
        elif isinstance(key, tuple) and len(key) == 1:
            key = (key[0], slice(None))

        if isinstance(key, tuple):
            # Flip the keys if the matrix is transposed
            key = key if not self._transposed else key[::-1]

            # Calculate the shape of the resulting sub-matrix
            sub_shape = get_sub_shape(self._shape, *key)

            # Calculate the linear indices into the super-matrix.
            sub_idx = linearize_indices(self._shape, *key)

            if len(sub_idx) == 1:
                return self._data[sub_idx[0]]
            else:
                return Matrix(sub_shape, (self._data[i] for i in sub_idx))
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
        elif isinstance(key, tuple) and len(key) == 1:
            key = (key[0], slice(None))

        if isinstance(key, tuple):
            # Flip the keys if the matrix is transposed
            key = key if not self._transposed else key[::-1]

            # Calculate the shape of the resulting sub-matrix
            sub_shape = get_sub_shape(self._shape, *key)

            # Calculate the linear indices into the super-matrix.
            sub_idx = linearize_indices(self._shape, *key)

            if isinstance(value, Matrix) and value.shape == sub_shape:
                for j, i in enumerate(sub_idx):
                    self._data[i] = value.data[j]
            elif isinstance(value, collections.abc.Sequence) and len(value) == functools.reduce(operator.mul, sub_shape):
                for j, i in enumerate(sub_idx):
                    self._data[i] = value[j]
            elif isinstance(value, (int, float)):
                for i in sub_idx:
                    self._data[i] = value
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
    @property
    def t(self):
        """
        Return the conjugate of the Quaternion.

        :return:
        """
        return Quaternion(self.qr, -self.qi)

    @property
    def matrix(self):
        return Matrix((4, 4), (
            1 - 2 * (j**2 + k**2), 2 * (i*j - k*r), 2 * (i*k + j*r),
            2 * (i*j + k*r), 1 - 2 * (i**2 + k**2), 2 * (j*k - i*r),
            2 * (i*k - j*r), 2 * (j*k + i*r), 1 - 2 * (i**2 + j**2),
            0, 0, 0, 1
        ))

    def norm(self):
        """
        Return the L2 norm for a vector.

        :return:
        """
        return math.sqrt((self @ self.t).qr)

    def inverse(self):
        return 1 / (self @ self.t).qr * self.t

    def __init__(self, qr, qi):
        """
        Create a Vector instance from either a iterable, or positional arguments.

        :param qr:
        :param qi:
        """
        self.qr = qr
        self.qi = Matrix((3, 1), qi)

    def __repr__(self):
        """
        Return a representation of a Quaternion that can be evaluated as code.

        :return:
        """
        return "{}({!r}, {!r})".format(self.__class__.__name__, self.qr, self.qi)

    def __str__(self):
        """
        Return a printable representation of a Quaternion.

        :return:
        """
        return "{} + {}i + {}j + {}k".format(self.qr, *self.qi)

    def __eq__(self, other):
        """
        Return equal if all elements of the Quaternion are equal.

        :param other:
        :return:
        """
        if isinstance(other, Quaternion):
            return self.qr == other.qr and self.qi == other.qi
        else:
            return False

    def __neg__(self):
        """
        Perform a negation.

        :return:
        """
        return Quaternion(-self.qr, -self.qi)

    def __pos__(self):
        """
        Perform a unary positive operation.

        :return:
        """
        return Quaternion(+self.qr, +self.qi)

    def __add__(self, other):
        """
        Perform an addition.

        :param other:
        :return:
        """
        if isinstance(other, Quaternion):
            return Quaternion(self.qr + other.qr, self.qi + other.qi)
        elif isinstance(other, (int, float)):
            return Quaternion(self.qr + other, self.qi + other)
        else:
            return NotImplemented

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
        return self + -other

    def __rsub__(self, other):
        """
        Perform a right-sided subtraction.

        :param other:
        :return:
        """
        return other + -self

    def __mul__(self, other):
        """
        Perform an element-wise multiplication.

        :param other:
        :return:
        """
        if isinstance(other, Quaternion):
            return Quaternion(self.qr * other.qr, self.qi * other.qi)
        elif isinstance(other, (int, float)):
            return Quaternion(self.qr * other, self.qi * other)
        else:
            return NotImplemented

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
            return Quaternion(self.qr / other.qr, self.qi / other.qi)
        elif isinstance(other, (int, float)):
            return Quaternion(self.qr / other, self.qi / other)
        else:
            return NotImplemented

    def __rtruediv__(self, other):
        """
        Perform a right-sided element-wise division.

        :param other:
        :return:
        """
        if isinstance(other, Quaternion):
            return Quaternion(other.qr / self.qr, other.qi / self.qi)
        elif isinstance(other, (int, float)):
            return Quaternion(other / self.qr, other / self.qi)
        else:
            return NotImplemented

    def __matmul__(self, other):
        """
        Perform a quaternion multiplication.

        :param other:
        :return:
        """
        if isinstance(other, Quaternion):
            return Quaternion(
                self.qr * other.qr - self.qi.t @ other.qi,
                self.qi.cross(other.qi) + other.qr * self.qi + self.qr * other.qi
            )
        else:
            return NotImplemented

    @classmethod
    def from_axis(cls, axis, angle):
        if not isinstance(axis, Matrix):
            axis = Matrix((3, 1), axis)

        axis /= axis.norm()
        angle %= 2 * math.pi

        return cls(
            math.cos(angle / 2),
            math.sin(angle / 2) * axis
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
        if not isinstance(source, Matrix):
            source = Matrix((3, 1), source)

        if not isinstance(target, Matrix):
            target = Matrix((3, 1), target)

        if not isinstance(up_direction, Matrix):
            up_direction = Matrix((3, 1), up_direction)

        difference = source - target
        difference /= difference.norm()

        right_direction = up_direction.cross(difference)
        right_direction /= right_direction.norm()

        angle = math.acos(up_direction @ difference)

        return cls.from_axis(right_direction, angle)
