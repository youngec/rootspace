# -*- coding: utf-8 -*-

from typing import Sequence

import pytest

from rootspace.ecs import Entity, ComponentContainer, ViewTrait, AssemblyTrait, SystemTrait, World, LoopStage


class ExampleView(ViewTrait):
    __slots__ = ("a", "b")

    def __init__(self, a: int, b: float) -> None:
        self.a = a
        self.b = b


class ExampleAssembly(AssemblyTrait):
    __slots__ = ("a", "b")

    def __init__(self, a: ComponentContainer[int], b: ComponentContainer[float]) -> None:
        self.a = a
        self.b = b

    @classmethod
    def new(cls) -> "ExampleAssembly":
        return cls(
            a=ComponentContainer.new(),
            b=ComponentContainer.new()
        )

    def match_mask(self, entity: Entity, mask: int) -> bool:
        a = (mask & 0b01) > 0
        b = (mask & 0b10) > 0
        c = self.a.contains(entity)
        d = self.b.contains(entity)
        return (a and c) or (b and d) or ((a or b) and c and d)

    def remove(self, entity: Entity) -> None:
        self.a.remove(entity)
        self.b.remove(entity)

    def get_view(self, entity: Entity) -> ViewTrait:
        return ExampleView(
            a=self.a.get(entity),
            b=self.b.get(entity)
        )


class ExampleSystem(SystemTrait):
    __slots__ = ()

    def get_name(self) -> str:
        return "ExampleSystem"

    def get_mask(self) -> int:
        return 0b01

    def get_stage(self) -> LoopStage:
        return LoopStage.Render

    def render(self, components: Sequence[ViewTrait]) -> None:
        print(components)
        assert len(components) == 2
        assert all([c.a is not None for c in components])


class TestWorld(object):
    def test_world(self) -> None:
        world = World.new(ExampleAssembly.new())
        e = world.make("e")
        world.components.a.add(e, 1)
        world.components.b.add(e, 1.0)

        f = world.make("f")
        world.components.a.add(f, 2)

        g = world.make("g")
        world.components.b.add(g, 3.0)

        world.add_system(ExampleSystem())
        world.render()
