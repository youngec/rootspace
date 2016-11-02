# -*- coding: utf-8 -*-

import abc
import argparse
import collections

import attr
from attr.validators import instance_of


registry = dict()


def register(cls):
    registry[cls.uuid] = cls

    return cls


@attr.s
class Executable(object, metaclass=abc.ABCMeta):
    _args = attr.ib(validator=instance_of(collections.Iterable))
    _ctx = attr.ib(validator=instance_of(dict))
    
    @abc.abstractmethod
    def __call__(self):
        return 0


@register
@attr.s
class ListDir(Executable):
    uuid = "18c34948-53e1-4ef4-94a3-64136f106e58"

    def __call__(self):
        parser = argparse.ArgumentParser(
            description="List the contents of a directory."
        )
        parser.add_argument(
            "targets", type=int, nargs="+", help=""
        )
        args = parser.parse_args(self._args)
        return 0

