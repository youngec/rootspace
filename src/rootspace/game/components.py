# -*- coding: utf-8 -*-

from typing import Type, Dict, Any

from ..ecs.serialization import SerDeTrait, SER
from .._math import Matrix


class PhysicsProperties(SerDeTrait):
    def __init__(self, mass: float, inertia: float, center_of_mass: Matrix, g: Matrix) -> None:
        self.mass = mass
        self.inertia = inertia
        self.center_of_mass = center_of_mass
        self.g = g

    @classmethod
    def new(cls) -> "PhysicsProperties":
        return cls(
            mass=1.0,
            inertia=1.0,
            center_of_mass=Matrix((3, 1), (0, 0, 0)),
            g=Matrix((3, 1), (0, -9.80665, 0))
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mass": self.mass,
            "inertia": self.inertia,
            "center_of_mass": self.center_of_mass.to_dict(),
            "g": self.g.to_dict()
        }

    @classmethod
    def from_dict(cls: Type[SER], obj: Dict[str, Any]) -> SER:
        return cls(
            mass=float(obj["mass"]),
            inertia=float(obj["inertia"]),
            center_of_mass=Matrix.from_dict(obj["center_of_mass"]),
            g=Matrix.from_dict(obj["g"])
        )


class PhysicsState(SerDeTrait):
    def __init__(self, momentum: Matrix, force: Matrix) -> None:
        self.momentum = momentum
        self.force = force

    @classmethod
    def new(cls) -> "PhysicsState":
        return cls(
            momentum=Matrix((3, 1), (0, 0, 0)),
            force=Matrix((3, 1), (0, 0, 0))
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "momentum": self.momentum.to_dict(),
            "force": self.force.to_dict()
        }

    @classmethod
    def from_dict(cls: Type[SER], obj: Dict[str, Any]) -> SER:
        return cls(
            momentum=Matrix.from_dict(obj["momentum"]),
            force=Matrix.from_dict(obj["force"])
        )
