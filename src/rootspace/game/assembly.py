# -*- coding: utf-8 -*-

from typing import Tuple, Optional, Sequence, Type, Dict, Any

from ..ecs.core import AssemblyTrait, ViewTrait, Entity, ComponentContainer, SystemTrait, LoopStage, A
from .view import View
from .components import PhysicsProperties, PhysicsState
from .systems import PhysicsSystem


class Assembly(AssemblyTrait):
    def __init__(self, physics_properties: ComponentContainer[PhysicsProperties], physics_state: ComponentContainer[PhysicsState]) -> None:
        self.physics_properties = physics_properties
        self.physics_state = physics_state

    @classmethod
    def new(cls) -> "Assembly":
        return cls(
            physics_properties=ComponentContainer.new(PhysicsProperties),
            physics_state=ComponentContainer.new(PhysicsState)
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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "physics_properties": self.physics_properties.to_dict(),
            "physics_state": self.physics_state.to_dict()
        }

    @classmethod
    def from_dict(cls: Type[A], obj: Dict[str, Any]) -> A:
        return cls(
            physics_properties=ComponentContainer.from_dict(PhysicsProperties, obj["physics_properties"]),
            physics_state=ComponentContainer.from_dict(PhysicsState, obj["physics_state"])
        )

    @classmethod
    def get_known_systems(cls) -> Dict[str, Type[SystemTrait]]:
        return {
            "PhysicsSystem": PhysicsSystem
        }