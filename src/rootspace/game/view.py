# -*- coding: utf-8 -*-

from typing import Optional

from rootspace.ecs.core import ViewTrait
from rootspace.game.components import PhysicsProperties, PhysicsState


class View(ViewTrait):
    def __init__(self, physics_properties: Optional[PhysicsProperties], physics_state: Optional[PhysicsState]) -> None:
        self.physics_properties = physics_properties
        self.physics_state = physics_state
