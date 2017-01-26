# -*- coding: utf-8 -*-

import collections
import math
import numpy

import attr
from attr.validators import instance_of


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


def to_quaternion(value):
    if value is None:
        return None
    elif isinstance(value, collections.Iterable):
        return Quaternion.from_iterable(value)
    elif isinstance(value, Quaternion):
        return value
    else:
        raise TypeError("Expected 'value' to be either an iterable, a Quaternion or None.")


@attr.s
class Quaternion(object):
    r = attr.ib(default=1.0, validator=instance_of(float), convert=float)
    i = attr.ib(default=0.0, validator=instance_of(float), convert=float)
    j = attr.ib(default=0.0, validator=instance_of(float), convert=float)
    k = attr.ib(default=0.0, validator=instance_of(float), convert=float)

    @property
    def T(self):
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

    def __mul__(self, other):
        return Quaternion(self.r * other.r, self.i * other.i, self.j * other.j, self.k * other.k)

    def __matmul__(self, other):
        return Quaternion(
            self.r * other.r - self.i * other.i - self.j * other.j - self.k * other.k,
            self.r * other.i + self.i * other.r + self.j * other.k - self.k * other.j,
            self.r * other.j - self.i * other.k + self.j * other.r + self.k * other.i,
            self.r * other.k + self.i * other.j - self.j * other.i + self.k * other.r
        )

    @classmethod
    def from_axis(cls, axis, angle):
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
    def from_iterable(cls, orientation):
        return cls(*orientation)
