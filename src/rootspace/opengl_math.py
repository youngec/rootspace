# -*- coding: utf-8 -*-

import math
import numpy
import collections


Vector3 = collections.namedtuple("Vector3", ("x", "y", "z"))


def identity():
    return numpy.eye(4)


def translation(vector):
    return numpy.array((
        (1, 0, 0, vector.x),
        (0, 1, 0, vector.y),
        (0, 0, 1, vector.z),
        (0, 0, 0, 1)
    ))


def rotation_z(angle):
    s = math.sin(angle % (2 * math.pi))
    c = math.cos(angle % (2 * math.pi))

    return numpy.array((
        (c, -s, 0, 0),
        (s,  c, 0, 0),
        (0,  0, 1, 0),
        (0,  0, 0, 1)
    ))


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

    return numpy.array((
        (1 / (a * t), 0, 0, 0),
        (0, 1 / t, 0, 0),
        (0, 0, f / (n - f), -1),
        (0, 0, -(f * n) / (f - n), 1)
    ))
