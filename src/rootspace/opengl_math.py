# -*- coding: utf-8 -*-

import math
import numpy
import quaternion


def identity():
    return numpy.eye(4)


def orientation(quat):
    ori = numpy.eye(4)
    ori[:3, :3] = quaternion.as_rotation_matrix(quat)
    return ori


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

    return numpy.array((
        (1 / (a * t), 0, 0, 0),
        (0, 1 / t, 0, 0),
        (0, 0, (f + n) / (f - n), 1),
        (0, 0, -2 * (f * n) / (f - n), 1)
    ))
