# -*- coding: utf-8 -*-

import collections
import math
import array

import numpy


def epsilon(*float_values, iterable=False):
    """
    Return the supplied numbers if their absolute value is greater or equal the machine epsilon, otherwise return 0.

    :param float_values:
    :param iterable:
    :return:
    """
    threshold = 7/3 - 4/3 - 1
    value = tuple(v if abs(v) >= threshold else 0.0 for v in float_values)
    if len(value) == 1 and not iterable:
        return value[0]
    else:
        return value


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


class Vector(object):
    """
    The base class for vectors of real numbers.
    """
    def __init__(self, *args, data_type="f"):
        """
        Create a Vector instance from either a iterable, or positional arguments.

        :param args:
        :param data_type:
        """
        if len(args) == 1 and isinstance(args[0], collections.Iterable):
            data = args[0]
        elif len(args) > 0 and all(isinstance(a, (bool, int, float)) for a in args):
            data = args
        else:
            raise ValueError("Expected an iterable as first argument, or scalar values as positional arguments.")

        self._data = array.array(data_type, epsilon(*data, iterable=True))

    def to_bytes(self):
        """
        Return a bytes-based representation of the Vector3.

        :return:
        """
        return self._data.tobytes()

    def normalize(self, inplace=True):
        """
        Normalize the vector. If inplace is false, return a new, normalized vector.

        :param inplace:
        :return:
        """
        n = self / abs(self)
        if inplace:
            self[:] = n[:]
        else:
            return n

    def dot(self, other):
        """
        Calculate the dot product. This is equivalent to the @ operator.

        :param other:
        :return:
        """
        return self @ other

    def cross(self, other):
        """
        Calculate the cross product.

        :param other:
        :return:
        """
        if isinstance(other, Vector):
            if len(self) == len(other):
                if len(self) == 3:
                    return Vector(
                        self[1] * other[2] - self[2] * other[1],
                        self[2] * other[0] - self[0] * other[2],
                        self[0] * other[1] - self[1] * other[0]
                    )
                elif len(self) == 7:
                    raise NotImplementedError("I have no idea how to calculate the seven-dimensional cross-product. :)")
                else:
                    raise ValueError("The cross product of vectors only exists for dimensionalities 3 and 7.")
            else:
                raise ValueError("Dimensionality mismatch between '{}' and '{}'.".format(self, other))
        else:
            raise TypeError("unsupported operand type(s) of cross(): '{}' and '{}'".format(Vector, type(other)))

    def __getitem__(self, item):
        """
        Access the Vector components by index.

        :param item:
        :return:
        """
        selection = self._data[item]
        if isinstance(selection, array.ArrayType):
            return Vector(selection)
        else:
            return self._data[item]

    def __setitem__(self, key, value):
        """
        Set the Vector components by index.

        :param key:
        :param value:
        :return:
        """
        self._data[key] = epsilon(value)

    def __repr__(self):
        """
        Return a representation of a Vector that can be evaluated as code.

        :return:
        """
        return "{}({})".format(self.__class__.__name__, ", ".join(str(e) for e in self._data))

    def __str__(self):
        """
        Return a printable representation of a Vector.

        :return:
        """
        return "({})".format(", ".join(str(e) for e in self._data))

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
        Return equal if all elements of the Vector are equal.

        :param other:
        :return:
        """
        if isinstance(other, Vector):
            return len(self) == len(other) and all(s == o for s, o in zip(self, other))
        else:
            return False

    def __abs__(self):
        """
        Return the L2 norm of the vector

        :return:
        """
        return math.sqrt(self @ self)

    def __add__(self, other):
        """
        Perform a left-sided element-wise addition.

        :param other:
        :return:
        """
        if isinstance(other, Vector) and len(self) == len(other):
            return Vector(s + o for s, o in zip(self, other))
        elif isinstance(other, (int, float)):
            return Vector(s + other for s in self)
        else:
            raise TypeError("unsupported operand type(s) for +: '{}' and '{}'".format(Vector, type(other)))

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
        if isinstance(other, Vector) and len(self) == len(other):
            return Vector(s - o for s, o in zip(self, other))
        elif isinstance(other, (int, float)):
            return Vector(s - other for s in self)
        else:
            raise TypeError("unsupported operand type(s) for -: '{}' and '{}'".format(Vector, type(other)))

    def __rsub__(self, other):
        """
        Perform a right-sided element-wise subtraction.

        :param other:
        :return:
        """
        if isinstance(other, Vector) and len(self) == len(other):
            return Vector(o - s for s, o in zip(self, other))
        elif isinstance(other, (int, float)):
            return Vector(other - s for s in self)
        else:
            raise TypeError("unsupported operand type(s) for -: '{}' and '{}'".format(type(other), Vector))

    def __mul__(self, other):
        """
        Perform a left-sided element-wise multiplication.

        :param other:
        :return:
        """
        if isinstance(other, Vector) and len(self) == len(other):
            return Vector(s * o for s, o in zip(self, other))
        elif isinstance(other, (int, float)):
            return Vector(s * other for s in self)
        else:
            raise TypeError("unsupported operand type(s) for *: '{}' and '{}'".format(Vector, type(other)))

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
        if isinstance(other, Vector) and len(self) == len(other):
            return Vector(s / o for s, o in zip(self, other))
        elif isinstance(other, (int, float)):
            return Vector(s / other for s in self)
        else:
            raise TypeError("unsupported operand type(s) for /: '{}' and '{}'".format(Vector, type(other)))

    def __rtruediv__(self, other):
        """
        Perform a right-sided element wise division.

        :param other:
        :return:
        """
        if isinstance(other, Vector) and len(self) == len(other):
            return Vector(o / s for s, o in zip(self, other))
        elif isinstance(other, (int, float)):
            return Vector(other / s for s in self)
        else:
            raise TypeError("unsupported operand type(s) for /: '{}' and '{}'".format(type(other), Vector))

    def __matmul__(self, other):
        """
        Perform a dot-product.

        :param other:
        :return:
        """
        if isinstance(other, Vector) and len(self) == len(other):
            return sum(s * o for s, o in zip(self, other))
        else:
            raise TypeError("unsupported operand type(s) for @: '{}' and '{}'".format(Vector, type(other)))


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
        if len(args) == 1 and isinstance(args[0], collections.Iterable):
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
        axis = Vector(axis)
        axis.normalize()
        angle %= 2 * math.pi

        sin = math.sin(angle / 2)
        return cls(
            math.cos(angle / 2),
            axis[0] * sin, 
            axis[1] * sin, 
            axis[2] * sin
        )
