# -*- coding: utf-8 -*-

import abc
import json
import pathlib
from typing import TypeVar, Type, Dict, Any, Optional

SER = TypeVar("SER", bound="SerDeTrait")


class SerDeTrait(object, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        Return a dictionary-based representation of the instance.
        """
        pass

    def to_json(self, json_file: pathlib.Path, indent: Optional[int] = None) -> None:
        """
        Serialize an instance to JSON.
        """
        with json_file.open("w") as jf:
            json.dump(self.to_dict(), jf, indent=indent)

    @classmethod
    @abc.abstractmethod
    def from_dict(cls: Type[SER], obj: Dict[str, Any]) -> SER:
        """
        Construct an instance from a dictionary.
        """
        pass

    @classmethod
    def from_json(cls: Type[SER], json_file: pathlib.Path) -> SER:
        """
        Deserialize an instance from a JSON file.
        """
        with json_file.open("r") as jf:
            return cls.from_dict(json.load(jf))
        