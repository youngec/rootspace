# -*- coding: utf-8 -*-

import math
import numpy


def mat4x4_identity():
    return numpy.eye(4)


def mat4x4_rotation_z(angle):
    s = math.sin(angle)
    c = math.cos(angle)
    Q = (
        (c, -s, 0, 0),
        (s, c, 0, 0),
        (0, 0, 1, 0),
        (0, 0, 0, 1)
    )

    return numpy.array(Q)


def mat4x4_ortho(left, right, bottom, top, near, far):
    l = left
    r = right
    b = bottom
    t = top
    n = near
    f = far
    P = (
        (2 / (r - l), 0, 0, -(r + l) / (r - l)),
        (0, 2 / (t - b), 0, -(t + b) / (t - b)),
        (0, 0, -2 / (f - n), -(f + n) / (f - n)),
        (0, 0, 0, 1)
    )

    return numpy.array(P)
