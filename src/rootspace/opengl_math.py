# -*- coding: utf-8 -*-

import math
import numpy


def identity():
    return numpy.eye(4)


def rotaiton_z(angle):
    s = math.sin(angle % (2 * math.pi))
    c = math.cos(angle % (2 * math.pi))
    Q = (
        (c, -s, 0, 0),
        (s, c, 0, 0),
        (0, 0, 1, 0),
        (0, 0, 0, 1)
    )

    return numpy.array(Q)


def orthographic(left, right, bottom, top, near, far):
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


def perspective():
    return numpy.eye(4)
