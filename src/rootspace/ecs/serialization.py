# -*- coding: utf-8 -*-

import abc
import json
import pathlib
from typing import TypeVar, Type, Dict, Any, Optional

S = TypeVar("S", bound="SerDeTrait")


class SerDeTrait(object, metaclass=abc.ABCMeta):
    @classmethod
    @abc.abstractmethod
    def new(cls) -> "SerDeTrait":
        """
        Construct a new, default instance.
        """
        pass

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
    def from_dict(cls: Type[S], obj: Dict[str, Any]) -> S:
        """
        Construct an instance from a dictionary.
        """
        pass

    @classmethod
    def from_json(cls: Type[S], json_file: pathlib.Path) -> S:
        """
        Deserialize an instance from a JSON file.
        """
        with json_file.open("r") as jf:
            return cls.from_dict(json.load(jf))
        
