#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Create and execute the Core object."""

from pong.core import PongCore


def main():
    """
    Enter into the execution of the Core object.

    :return:
    """

    exc = PongCore()
    try:
        exc.execute()
    finally:
        del exc


if __name__ == "__main__":
    main()
