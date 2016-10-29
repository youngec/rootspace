# -*- coding: utf-8 -*-

import abc
import argparse
import collections
import attr
from attr.validators import instance_of


@attr.s
class Executable(object, metaclass=abc.ABCMeta):
    _args = attr.ib(validator=instance_of(collections.Iterable))
    _ctx = attr.ib(validator=instance_of(dict))
    
    @abc.abstractmethod
    def __call__(self):
        return 0


@attr.s
class ListDir(Executable):
    def __call__(self):
        parser = argparse.ArgumentParser(
            description="List the contents of a directory."
        )
        parser.add_argument(
            "targets", type=int, nargs="+", help=""
        )
        args = parser.parse_args(self._args)
        return 0

