#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Create and execute the Core object."""

from engine.core import Core


def main():
    """
    Enter into the execution of the Core object.

    :return:
    """
    exc = Core.create_core()
    exc.execute()


if __name__ == "__main__":
    main()
