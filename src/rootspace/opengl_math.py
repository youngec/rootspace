# -*- coding: utf-8 -*-

import math
import collections


Matrix4x4 = collections.namedtuple("Matrix4x4", "a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p")


def mat4x4_identity():
    return Matrix4x4(1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1)


def mat4x4_rotation_z(angle):
    s = math.sin(angle)
    c = math.cos(angle)

    return Matrix4x4(c, s, 0, 0, -s, c, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1)


def mat4x4_ortho(left, right, bottom, top, near, far):
    a = 2 / (right - left)
    b = 2 / (top - bottom)
    c = -2 / (far - near)
    d = -(right + left) / (right - left)
    e = -(top + bottom) / (top - bottom)
    f = -(far + near) / (far - near)

    return Matrix4x4(a, 0, 0, 0, 0, b, 0, 0, 0, 0, c, 0, d, e, f, 1)
