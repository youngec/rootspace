# -*- coding: utf-8 -*-

from .ecs import AssemblyTrait, ViewTrait, Entity


class RootspaceView(ViewTrait):
    __slots__ = ()

    def __init__(self) -> None:
        pass


class RootspaceAssembly(AssemblyTrait):
    __slots__ = ()

    def __init__(self) -> None:
        pass

    @classmethod
    def new(cls) -> "RootspaceAssembly":
        return cls()

    def match_mask(self, entity: Entity, mask: int) -> bool:
        return False

    def remove(self, entity: Entity) -> None:
        pass

    def get_view(self, entity: Entity) -> RootspaceView:
        return RootspaceView()