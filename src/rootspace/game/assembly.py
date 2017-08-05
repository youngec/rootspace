# -*- coding: utf-8 -*-

from typing import Tuple, Optional, Sequence, Type, Dict, Any

from ..ecs.core import AssemblyTrait, ViewTrait, Entity, ComponentContainer, SystemTrait, LoopStage
from ..ecs.serialization import SerDeTrait, S
from .._math import Matrix


class PhysicsProperties(SerDeTrait):
    def __init__(self, mass: float, inertia: float, center_of_mass: Matrix, g: Matrix) -> None:
        self.mass = mass
        self.inertia = inertia
        self.center_of_mass = center_of_mass
        self.g = g

    @classmethod
    def new(cls: Type[S]) -> S:
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
    def from_dict(cls: Type[S], obj: Dict[str, Any]) -> S:
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
    def new(cls: Type[S]) -> S:
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
    def from_dict(cls: Type[S], obj: Dict[str, Any]) -> S:
        return cls(
            momentum=Matrix.from_dict(obj["momentum"]),
            force=Matrix.from_dict(obj["force"])
        )

class PhysicsSystem(SystemTrait):
    __slots__ = ()
    
    def get_name(self) -> str:
        return "PhysicsSystem"

    def get_mask(self) -> int:
        return 0b11

    def get_stage(self) -> LoopStage:
        return LoopStage.Update

    def update(self, components: Sequence[View], time: float, delta_time: float) -> None:
        for view in components:
            pass


class View(ViewTrait):
    __slots__ = ("physics_properties", "physics_state")

    def __init__(self, physics_properties: Optional[PhysicsProperties] = None, physics_state: Optional[PhysicsState] = None) -> None:
        self.physics_properties = physics_properties
        self.physics_state = physics_state


class Assembly(AssemblyTrait):
    __slots__ = ("physics_properties", "physics_state")

    def __init__(self, physics_properties: ComponentContainer[PhysicsProperties], physics_state: ComponentContainer[PhysicsState]) -> None:
        self.physics_properties = physics_properties
        self.physics_state = physics_state

    @classmethod
    def new(cls) -> "Assembly":
        return cls(
            physics_properties=ComponentContainer.new(),
            physics_state=ComponentContainer.new()
        )

    def match_mask(self, entity: Entity, mask: int) -> bool:
        a = (mask & 0b01) > 0
        b = (mask & 0b10) > 0
        c = self.physics_properties.contains(entity)
        d = self.physics_state.contains(entity)
        return (a and c) or (b and d) or ((a or b) and c and d)

    def remove(self, entity: Entity) -> None:
        self.physics_properties.remove(entity)
        self.physics_state.remove(entity)

    def get_view(self, entity: Entity) -> View:
        return View(
            physics_properties=self.physics_properties.get(entity),
            physics_state=self.physics_state.get(entity)
        )