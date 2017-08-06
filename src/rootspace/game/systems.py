# -*- coding: utf-8 -*-

from typing import Sequence

from ..ecs.core import SystemTrait, LoopStage


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


