# -*- coding: utf-8 -*-

import collections.abc
import math
import array
import functools
import operator
import itertools
from typing import Any, Union, Tuple, NewType, Iterable, Sequence, Optional

from .utilities import get_sub_shape, linearize_indices

Number = NewType("Number", Union[int, float])
MatrixType = NewType("Matrix", object)
GenericMatrix = NewType("GenericMatrix", Union[Iterable[Number], MatrixType])
QuaternionType = NewType("Quaternion", object)


class Matrix(object):
    """
    The base class for Matrices of real numbers. The internal data structure uses row-major ordering.
    """

    @classmethod
    def from_iterable(cls, data: Sequence[Union[Number, Sequence[Number]]]) -> MatrixType:
        """
        Return a matrix from a collection with shape information.

        :param data:
        :return:
        """
        if isinstance(data, collections.abc.Sequence):
            if all(isinstance(row, (int, float)) for row in data):
                return Matrix((len(data), 1), data)
            elif all(isinstance(row, collections.abc.Sequence) for row in data):
                if functools.reduce(operator.eq, (len(row) for row in data)):
                    shape = (len(data), len(data[0]))
                    return Matrix(shape, (column for row in data for column in row))
                else:
                    raise ValueError("Elements of data do not have the same length.")
            else:
                raise TypeError("Expected integers, floats or collections as elements of data.")
        else:
            raise TypeError("Expected a collection, got '{}'.".format(data))

    @classmethod
    def identity(cls, d: int) -> MatrixType:
        """
        Return an identity matrix of shape d x d.

        :param d:
        :return:
        """
        return cls((d, d))

    @classmethod
    def zeros(cls, shape: Union[int, Tuple[int, ...]]) -> MatrixType:
        """
        Create a matrix with zeros.

        :param shape:
        :return:
        """
        if isinstance(shape, int):
            return Matrix((shape, 1), 0)
        elif isinstance(shape, tuple):
            return Matrix(shape, 0)
        else:
            raise TypeError("Expected an integer or a tuple of integers.")

    @classmethod
    def ones(cls, shape: Union[int, Tuple[int, ...]]) -> MatrixType:
        """
        Create a matrix with ones.

        :param shape:
        :return:
        """
        if isinstance(shape, int):
            return Matrix((shape, 1), 1)
        elif isinstance(shape, tuple):
            return Matrix(shape, 1)
        else:
            raise TypeError("Expected an integer or a tuple of integers.")

    @classmethod
    def translation(cls, t_x: Number, t_y: Number, t_z: Number) -> MatrixType:
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
    def rotation_x(cls, angle: Number) -> MatrixType:
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
    def rotation_y(cls, angle: Number) -> MatrixType:
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
    def rotation_z(cls, angle: Number) -> MatrixType:
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
    def scaling(cls, s_x: Number, s_y: Number, s_z: Number) -> MatrixType:
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
    def shearing(cls, s: Number, i: int, j: int) -> MatrixType:
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
    def orthographic(cls, left: Number, right: Number,
                     bottom: Number, top: Number,
                     near: Number, far: Number) -> MatrixType:
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
    def perspective(cls, field_of_view: Number, viewport_ratio: Number,
                    near: Number, far: Number) -> MatrixType:
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
    def is_scalar(self) -> bool:
        return len(self) == 1

    @classmethod
    def ex(cls):
        return cls((3, 1), (1, 0, 0))

    @classmethod
    def ey(cls):
        return cls((3, 1), (0, 1, 0))

    @classmethod
    def ez(cls):
        return cls((3, 1), (0, 0, 1))

    @property
    def shape(self) -> Tuple[int, ...]:
        return self._shape if not self._transposed else self._shape[::-1]

    @property
    def data(self) -> array.ArrayType:
        return self._data

    @property
    def is_square(self) -> bool:
        return functools.reduce(operator.eq, self.shape)

    @property
    def is_vector(self) -> bool:
        return len([None for s in self.shape if s > 1]) == 1

    @property
    def is_column_vector(self) -> bool:
        return self.is_vector and self.shape[0] > 1

    @property
    def is_row_vector(self) -> bool:
        return self.is_vector and self.shape[0] == 1

    @property
    def is_4d_vector(self) -> bool:
        return self.is_vector and self.shape == (4, 1) or self.shape == (1, 4)

    @property
    def is_3d_vector(self) -> bool:
        return self.is_vector and self.shape == (3, 1) or self.shape == (1, 3)

    @property
    def t(self) -> MatrixType:
        return Matrix(self._shape, self.data, transposed=(not self._transposed))

    def is_close(self, other: Union[MatrixType, int, float],
                 rel_tol: float = 1e-05, abs_tol: float = 1e-08) -> MatrixType:
        """
        Perform an element-wise approximate equality comparison.

        :param other:
        :param rel_tol:
        :param abs_tol:
        :raise TypeError:
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
            return NotImplemented

    def all_close(self, other: Any, rel_tol: float = 1e-05, abs_tol: float = 1e-08) -> bool:
        """
        Return True if all elements compare approximately equal, False otherwise.

        :param other:
        :param rel_tol:
        :param abs_tol:
        :return:
        """
        return all(self.is_close(other, rel_tol, abs_tol))

    def determinant(self) -> float:
        """
        Calculate the determinant.

        :raise NotImplementedError:
        :raise ValueError:
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

    def norm(self, p: int = 2) -> float:
        """
        Calculate the norm of the Matrix.

        :param p:
        :return:
        """
        return math.pow(sum(math.pow(abs(d), p) for d in self), 1 / p)

    def cross(self, other: MatrixType) -> MatrixType:
        """
        Calculate the cross-product of two vectors.

        :param other:
        :raise ValueError:
        :raise TypeError:
        :return:
        """
        if isinstance(other, Matrix):
            if self.is_3d_vector and other.is_3d_vector:
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
                raise ValueError("Expected a vector with three dimensions, got '{}'.".format(other))
        else:
            raise TypeError("unsupported operand type(s) for cross() '{}' and '{}'".format(type(self), type(other)))

    def __init__(self,
                 shape: Tuple[int, ...],
                 data: Optional[Union[Iterable[Number], int, float]] = None,
                 data_type: str = "f",
                 transposed: bool = False
                 ):
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
        else:
            if shape[0] == shape[1]:
                self._data = array.array(data_type,
                                         (1 if i in range(0, length, shape[0] + 1) else 0 for i in range(length)))
            else:
                self._data = array.array(data_type, (0 for _ in range(length)))

    def __str__(self) -> str:
        """
        Return a human-readable representation.

        :return:
        """
        lines = list()
        for i in range(self.shape[0]):
            d = self[i, :]
            if isinstance(d, Matrix):
                lines.append("[{}]".format(", ".join("{:.2e}".format(e) for e in d)))
            else:
                lines.append("[{}]".format(d))

        return "[{}]".format("; ".join(lines))

    def __repr__(self) -> str:
        """
        Return a eval-compatible representation.

        :return:
        """
        return "{}({}, ({}), data_type={}, transposed={})".format(
            self.__class__.__name__, self._shape, ", ".join("{:e}".format(e) for e in self),
            self._data.typecode, self._transposed
        )

    def __bytes__(self) -> bytes:
        """
        Return a bytes representation of the matrix.

        :return:
        """
        return self._data.tobytes()

    def __len__(self) -> int:
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

    def __contains__(self, item) -> bool:
        """
        Provide the contains interface.

        :param item:
        :return:
        """
        return item in self._data

    def __getitem__(self, key: Union[int, slice, Tuple[int, slice, Tuple[int, ...]]]) -> Union[int, float, MatrixType]:
        """
        Provide angle-bracket element access to the matrix.

        :param key:
        :raise TypeError:
        :return:
        """
        if isinstance(key, (int, slice)):
            # noinspection PyTypeChecker
            key = (key, slice(None))
        elif isinstance(key, tuple):
            if len(key) == 1:
                # noinspection PyTypeChecker
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

    def __setitem__(self, key: Union[int, slice, Tuple[int, slice, Tuple[int, ...]]],
                    value: Union[int, float, MatrixType, Sequence[Number]]):
        """
        Provide angle-bracket element setting to the matrix.

        :param key:
        :param value:
        :raise ValueError:
        :raise TypeError:
        :return:
        """
        if isinstance(key, (int, slice)):
            # noinspection PyTypeChecker
            key = (key, slice(None))
        elif isinstance(key, tuple) and len(key) == 1:
            # noinspection PyTypeChecker
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
            elif isinstance(value, collections.abc.Sequence) and len(value) == functools.reduce(operator.mul,
                                                                                                sub_shape):
                for j, i in enumerate(sub_idx):
                    self._data[i] = value[j]
            elif isinstance(value, (int, float)):
                for i in sub_idx:
                    self._data[i] = value
            else:
                raise ValueError("The shape/length of the value must equal the shape/length of the indexed range.")
        else:
            raise TypeError("Expected indices of type int, slice or tuple, not '{}'.".format(type(key)))

    def __eq__(self, other: MatrixType) -> bool:
        """
        Return True if all elements of two matrices are equal.

        :param other:
        :return:
        """
        if isinstance(other, Matrix):
            return self.shape == other.shape and all(s == o for s, o in zip(self, other))
        else:
            return NotImplemented

    def __neg__(self) -> MatrixType:
        """
        Perform an element-wise negation.

        :return:
        """
        result = Matrix(self.shape, 0)
        for i, j in itertools.product(range(result.shape[0]), range(result.shape[1])):
            result[i, j] = -self[i, j]
        return result

    def __pos__(self) -> MatrixType:
        """
        Perform an element-wise positive unary operation.

        :return:
        """
        result = Matrix(self.shape, 0)
        for i, j in itertools.product(range(result.shape[0]), range(result.shape[1])):
            result[i, j] = +self[i, j]
        return result

    def __add__(self, other: Union[int, float, MatrixType]) -> MatrixType:
        """
        Perform a left-sided element-wise addition.

        :param other:
        :raise ValueError:
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

    def __radd__(self, other: Union[int, float, MatrixType]) -> MatrixType:
        """
        Perform a right-sided element-wise addition. Equivalent to __add__.

        :param other:
        :return:
        """
        return self.__add__(other)

    def __sub__(self, other: Union[int, float, MatrixType]) -> MatrixType:
        """
        Perform a left-sided element-wise subtraction.

        :param other:
        :return:
        """
        return self + -other

    def __rsub__(self, other: Union[int, float, MatrixType]) -> MatrixType:
        """
        Perform a right-sided element-wise subtraction.

        :param other:
        :return:
        """
        return other + -self

    def __mul__(self, other: Union[int, float, MatrixType]) -> MatrixType:
        """
        Perform a left-sided element-wise multiplication.

        :param other:
        :raise ValueError:
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

    def __rmul__(self, other: Union[int, float, MatrixType]) -> MatrixType:
        """
        Perform a right-sided element-wise multiplication. Equivalent to __mul__.

        :param other:
        :return:
        """
        return self.__mul__(other)

    def __truediv__(self, other: Union[int, float, MatrixType]) -> MatrixType:
        """
        Perform a left-sided element-wise division.

        :param other:
        :raise ValueError:
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

    def __rtruediv__(self, other: Union[int, float, MatrixType]) -> MatrixType:
        """
        Perform a right-sided element wise division.

        :param other:
        :raise ValueError:
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

    def __matmul__(self, other: MatrixType) -> MatrixType:
        """
        Perform a left-sided matrix multiplication.

        :param other:
        :raise ValueError:
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
                raise ValueError(
                    "Last dimension of '{}' and first dimension of '{}' do not match or are 1.".format(self.shape,
                                                                                                       other.shape))
        else:
            return NotImplemented


class Quaternion(object):
    """
    The Quaternion class provides a way to work with four-dimensional complex numbers.
    """

    @classmethod
    def from_axis(cls, axis: MatrixType, angle: Number) -> QuaternionType:
        """
        Create a Quaternion from an axis and an angle.

        :param axis:
        :param angle:
        :raise ValueError:
        :return:
        """
        if axis.is_3d_vector:
            axis /= axis.norm()
            angle %= 2 * math.pi

            c = math.cos(angle / 2)
            s = math.sin(angle / 2)

            q = cls(s * axis[0], s * axis[1], s * axis[2], c)

            return q / q.norm()
        else:
            raise ValueError("Expected a three-dimensional vector as axis, got '{}'.".format(axis))

    @classmethod
    def from_vectors(cls, s: MatrixType, t: MatrixType) -> QuaternionType:
        """
        Create a Quaternion from two 3D vectors. The Quaternion describes the rotation from source to target.

        :param s:
        :param t:
        :raise ValueError:
        :return:
        """
        if s.is_3d_vector and t.is_3d_vector:
            s /= s.norm()
            t /= t.norm()

            a = s.cross(t)
            b = math.sqrt(2 * (1 + math.e))

            q = cls(
                1 / b * a[0],
                1 / b * a[1],
                1 / b * a[2],
                b / 2
            )

            return q / q.norm()
        else:
            raise ValueError("Expected three-dimensional vectors, got '{}' and '{}'.".format(s, t))

    @classmethod
    def slerp(cls, s: QuaternionType, t: QuaternionType, x: float) -> QuaternionType:
        """

        :param s:
        :param t:
        :param x:
        :return:
        """
        s /= s.norm()
        t /= t.norm()

        phi = math.acos(sum(s * t))
        a = math.sin(phi * (1 - x)) / math.sin(phi)
        b = math.sin(phi * x) / math.sin(phi)

        return a * s + b * t

    @property
    def qi(self) -> Number:
        return self._data[0]

    @property
    def qj(self) -> Number:
        return self._data[1]

    @property
    def qk(self) -> Number:
        return self._data[2]

    @property
    def qr(self) -> Number:
        return self._data[3]

    @property
    def data(self) -> array.ArrayType:
        return self._data

    @property
    def t(self) -> QuaternionType:
        """
        Return the conjugate of the Quaternion.

        :return:
        """
        return Quaternion(-self.qi, -self.qj, -self.qk, self.qr)

    @property
    def vector(self) -> MatrixType:
        return Matrix((4, 1), (
            self.qi,
            self.qj,
            self.qk,
            self.qr
        ))

    @property
    def matrix(self) -> MatrixType:
        i = self.qi
        j = self.qj
        k = self.qk
        r = self.qr
        s = 2 / self.norm()

        return Matrix((4, 4), (
            1 - s * (j ** 2 + k ** 2), s * (i * j - k * r), s * (i * k + j * r), 0,
            s * (i * j + k * r), 1 - s * (i ** 2 + k ** 2), s * (j * k - i * r), 0,
            s * (i * k - j * r), s * (j * k + i * r), 1 - s * (i ** 2 + j ** 2), 0,
            0, 0, 0, 1
        ))

    def all_close(self, other: QuaternionType, rel_tol: float = 1e-05, abs_tol: float = 1e-08) -> bool:
        """
        Return True if all elements compare approximately equal, False otherwise.

        :param other:
        :param rel_tol:
        :param abs_tol:
        :raise TypeError:
        :return:
        """
        if isinstance(other, Quaternion):
            return all(math.isclose(a, b, rel_tol=rel_tol, abs_tol=abs_tol) for a, b in zip(self, other))
        else:
            return NotImplemented

    def norm(self) -> float:
        """
        Calculate the L2 norm of the Matrix.

        :return:
        """
        return math.sqrt(sum(abs(d) ** 2 for d in self))

    def inverse(self) -> QuaternionType:
        """
        Calculate the inverse of the Quaternion.

        :return:
        """
        return 1 / (self @ self.t).qr * self.t

    def transform(self, other: MatrixType) -> MatrixType:
        """
        Transform the 4D vector by the current quaternion.

        :param other:
        :return:
        """
        return (self @ other @ self.inverse()).vector

    def __init__(self, qi: Number = 0.0, qj: Number = 0.0, qk: Number = 0.0, qr: Number = 1.0, data_type: str = "f"):
        """
        Create a Quaternion from the four components:

        Q = qr + qi * i + qj * j + qk * k

        :param qi:
        :param qj:
        :param qk:
        :param qr:
        :param data_type:
        """
        self._data = array.array(data_type, (qi, qj, qk, qr))

    def __str__(self) -> str:
        """
        Return a printable representation of a Quaternion.

        :return:
        """
        return "{:.2e}i + {:.2e}j + {:.2e}k + {:.2e}".format(self.qi, self.qj, self.qk, self.qr)

    def __repr__(self) -> str:
        """
        Return a representation of a Quaternion that can be evaluated as code.

        :return:
        """
        return "{}(qi={:e}, qj={:e}, qk={:e}, qr={:e})".format(self.__class__.__name__, self.qi, self.qj, self.qk, self.qr)

    def __iter__(self):
        """
        Provide an iterator interface.

        :return:
        """
        for d in self._data:
            yield d

    def __reversed__(self):
        """
        Provide a reverse iterator interface.

        :return:
        """
        for d in reversed(self._data):
            yield d

    def __eq__(self, other: QuaternionType) -> bool:
        """
        Return True if the Quaternions are equal.

        :param other:
        :return:
        """
        if isinstance(other, Quaternion):
            return self.qi == other.qi and self.qj == other.qj and self.qk == other.qk and self.qr == other.qr
        else:
            return NotImplemented

    def __neg__(self) -> QuaternionType:
        """
        Perform a negation.

        :return:
        """
        return Quaternion(-self.qi, -self.qj, -self.qk, -self.qr)

    def __pos__(self) -> QuaternionType:
        """
        Perform a unary positive operation.

        :return:
        """
        return Quaternion(+self.qi, +self.qj, +self.qk, +self.qr)

    def __add__(self, other: Union[int, float, QuaternionType]) -> QuaternionType:
        """
        Perform an addition.

        :param other:
        :return:
        """
        if isinstance(other, Quaternion):
            return Quaternion(self.qi + other.qi, self.qj + other.qj, self.qk + other.qk, self.qr + other.qr)
        elif isinstance(other, (int, float)):
            return Quaternion(self.qi + other, self.qj + other, self.qk + other, self.qr + other)
        else:
            return NotImplemented

    def __radd__(self, other: Union[int, float, QuaternionType]) -> QuaternionType:
        """
        Perform a right-sided addition. Equivalent to left-sided.

        :param other:
        :return:
        """
        return self.__add__(other)

    def __sub__(self, other: Union[int, float, QuaternionType]) -> QuaternionType:
        """
        Perform a subtraction.

        :param other:
        :return:
        """
        return self + -other

    def __rsub__(self, other: Union[int, float, QuaternionType]) -> QuaternionType:
        """
        Perform a right-sided subtraction.

        :param other:
        :return:
        """
        return other + -self

    def __mul__(self, other: Union[int, float, QuaternionType]) -> QuaternionType:
        """
        Perform an element-wise multiplication.

        :param other:
        :return:
        """
        if isinstance(other, Quaternion):
            return Quaternion(self.qi * other.qi, self.qj * other.qj, self.qk * other.qk, self.qr * other.qr)
        elif isinstance(other, (int, float)):
            return Quaternion(self.qi * other, self.qj * other, self.qk * other, self.qr * other)
        else:
            return NotImplemented

    def __rmul__(self, other: Union[int, float, QuaternionType]) -> QuaternionType:
        """
        Perform a right-sided element-wise multiplication. Equivalent to left-sided.

        :param other:
        :return:
        """
        return self.__mul__(other)

    def __truediv__(self, other: Union[int, float, QuaternionType]) -> QuaternionType:
        """
        Perform an element-wise division.

        :param other:
        :return:
        """
        if isinstance(other, Quaternion):
            return Quaternion(self.qi / other.qi, self.qj / other.qj, self.qk / other.qk, self.qr / other.qr)
        elif isinstance(other, (int, float)):
            return Quaternion(self.qi / other, self.qj / other, self.qk / other, self.qr / other)
        else:
            return NotImplemented

    def __rtruediv__(self, other: Union[int, float, QuaternionType]) -> QuaternionType:
        """
        Perform a right-sided element-wise division.

        :param other:
        :return:
        """
        if isinstance(other, Quaternion):
            return Quaternion(other.qi / self.qi, other.qj / self.qj, other.qk / self.qk, other.qr / self.qr)
        elif isinstance(other, (int, float)):
            return Quaternion(other / self.qi, other / self.qj, other / self.qk, other / self.qr)
        else:
            return NotImplemented

    def __matmul__(self, other: Union[int, float, QuaternionType]) -> QuaternionType:
        """
        Perform a quaternion multiplication.

        :param other:
        :raise ValueError:
        :return:
        """
        if isinstance(other, Quaternion):
            return Quaternion(
                self.qr * other.qi + self.qi * other.qr + self.qj * other.qk - self.qk * other.qj,
                self.qr * other.qj - self.qi * other.qk + self.qj * other.qr + self.qk * other.qi,
                self.qr * other.qk + self.qi * other.qj - self.qj * other.qi + self.qk * other.qr,
                self.qr * other.qr - self.qi * other.qi - self.qj * other.qj - self.qk * other.qk
            )
        elif isinstance(other, Matrix) and other.is_4d_vector:
            if other.is_row_vector:
                other = other.t

            if other.is_column_vector:
                return Quaternion(
                    self.qr * other[0] + self.qi * other[3] + self.qj * other[2] - self.qk * other[1],
                    self.qr * other[1] - self.qi * other[2] + self.qj * other[3] + self.qk * other[0],
                    self.qr * other[2] + self.qi * other[1] - self.qj * other[0] + self.qk * other[3],
                    self.qr * other[3] - self.qi * other[0] - self.qj * other[1] - self.qk * other[2]
                )
            else:
                raise ValueError("Expected a four-dimensional vector as operand, got '{}'.".format(other))
        else:
            return NotImplemented


def all_close(a: Any, b: Any, rel_tol: float = 1e-05, abs_tol: float = 1e-08) -> bool:
    """
    Return true if objects a and b are approximately equal.

    :param a:
    :param b:
    :param rel_tol:
    :param abs_tol:
    :raise TypeError:
    :return:
    """
    if hasattr(a, "all_close"):
        r = a.all_close(b, rel_tol, abs_tol)
        if r is NotImplemented:
            raise TypeError("unsupported operand type(s) for all_close() '{}' and '{}'".format(type(a), type(b)))
        else:
            return r
    elif hasattr(b, "all_close"):
        r = b.all_close(a, rel_tol, abs_tol)
        if r is NotImplemented:
            raise TypeError("unsupported operand type(s) for all_close() '{}' and '{}'".format(type(a), type(b)))
        else:
            return r
    else:
        raise TypeError("unsupported operand type(s) for all_close() '{}' and '{}'".format(type(a), type(b)))


def euler_step(delta_time, momentum, force, dm, df):
    """
    Evaluate the current integral step.

    :param delta_time:
    :param momentum:
    :param force:
    :param dm:
    :param df:
    :return:
    """
    dm_n = momentum + dm * delta_time
    df_n = force + df * delta_time

    return dm_n, df_n


def runge_kutta_4(delta_time, momentum, force, mass):
    """
    Perform a fourth-order Runge Kutta integration with constant force.
    Based on http://gafferongames.com/game-physics/

    :param delta_time:
    :param momentum:
    :param force:
    :param mass:
    :return:
    """
    dm_a, df_a = euler_step(0, momentum, force, Matrix((3, 1), 0), Matrix((3, 1), 0))
    dm_b, df_b = euler_step(delta_time * 0.5, momentum, force, dm_a, df_a)
    dm_c, df_c = euler_step(delta_time * 0.5, momentum, force, dm_b, df_b)
    dm_d, df_d = euler_step(delta_time, momentum, force, dm_c, df_c)

    dp = (dm_a + 2 * (dm_b + dm_c) + dm_d) * (delta_time / (6 * mass))
    dm = (df_a + 2 * (df_b + df_c) + df_d) * (delta_time / 6)

    return dp, dm


def velocity_verlet(delta_time, momentum, force, mass):
    """
    Perform a velocity verlet integration with constant force.

    :param delta_time:
    :param momentum:
    :param force:
    :param mass:
    :return:
    """
    dp = (momentum + force * delta_time / 2) * delta_time / mass
    dm = force * delta_time / mass
    return dp, dm


def equations_of_motion(delta_time, position, momentum, force, mass):
    """
    Calculate the equations of motion for a given time step.

    :param delta_time:
    :param position:
    :param momentum:
    :param force:
    :param mass:
    :return:
    """
    dp, dm = velocity_verlet(delta_time, momentum, force, mass)
    position_next = position + dp
    momentum_next = momentum + dm

    return position_next, momentum_next
