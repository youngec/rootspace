# -*- coding: utf-8 -*-

from typing import Sequence, Dict, Any, Type

import pytest

from rootspace.ecs.core import Entity, ComponentContainer, ViewTrait, AssemblyTrait, SystemTrait, World, LoopStage, EntityDataIndex, A
from rootspace.ecs.serialization import SerDeTrait, SER


class ExampleComponent(SerDeTrait):
    def __init__(self, some: float) -> None:
        self.some = some

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, ExampleComponent):
            return self.some == other.some
        else:
            return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "some": self.some
        }

    @classmethod
    def from_dict(cls: Type[SER], obj: Dict[str, Any]) -> SER:
        return cls(
            some=float(obj["some"])
        )


class ExampleView(ViewTrait):
    def __init__(self, a: int, b: ExampleComponent) -> None:
        self.a = a
        self.b = b

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, ExampleView):
            return self.a == other.a and self.b == other.b
        else:
            return False


class ExampleSystem(SystemTrait):
    __slots__ = ()

    def get_name(self) -> str:
        return "ExampleSystem"

    def get_mask(self) -> int:
        return 0b01

    def get_stage(self) -> LoopStage:
        return LoopStage.Render

    def render(self, components: Sequence[ExampleView]) -> None:
        assert len(components) == 2
        assert all([c.a is not None for c in components])


class ExampleAssembly(AssemblyTrait):
    def __init__(self, a: ComponentContainer[int], b: ComponentContainer[ExampleComponent]) -> None:
        self.a = a
        self.b = b

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, ExampleAssembly):
            return self.a == other.a and self.b == other.b
        else:
            return False

    @classmethod
    def new(cls) -> "ExampleAssembly":
        return cls(
            a=ComponentContainer.new(int),
            b=ComponentContainer.new(ExampleComponent)
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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "a": self.a.to_dict(),
            "b": self.b.to_dict()
        }

    @classmethod
    def from_dict(cls: Type[A], obj: Dict[str, Any]) -> A:
        return cls(
            a=ComponentContainer.from_dict(int, obj["a"]),
            b=ComponentContainer.from_dict(ExampleComponent, obj["b"])
        )

    @classmethod
    def get_known_systems(cls) -> Dict[str, Type[SystemTrait]]:
        return {
            "ExampleSystem": ExampleSystem
        }


class TestEntity(object):
    def test_equality(self) -> None:
        assert Entity("", 1, 0) == Entity("", 1, 0)
        assert Entity("", 1, 0) != Entity("", 2, 1)

    def test_to_dict(self) -> None:
        assert Entity("anon", 1, 2).to_dict() == {"name": "anon", "uuid": 1, "idx": 2}

    def test_from_dict(self) -> None:
        e = Entity.from_dict({"name": "anon", "uuid": 1, "idx": 2})
        assert e == Entity("anon", 1, 2)


class TestEntityDataIndex(object):
    def test_equality(self) -> None:
        assert EntityDataIndex(1, 0) == EntityDataIndex(1, 0)
        assert EntityDataIndex(1, 0) != EntityDataIndex(2, 1)

    def test_to_dict(self) -> None:
        assert EntityDataIndex(1, 2).to_dict() == {"uuid": 1, "data_idx": 2}

    def test_from_dict(self) -> None:
        i = EntityDataIndex.from_dict({"uuid": 1, "data_idx": 2})
        assert i == EntityDataIndex(1, 2)


class TestComponentContainer(object):
    def test_equality(self) -> None:
        assert ComponentContainer(bool, [True], [Entity("", 1, 0)], [EntityDataIndex(1, 0)]) == ComponentContainer(bool, [True], [Entity("", 1, 0)], [EntityDataIndex(1, 0)])
        assert ComponentContainer(bool, [True], [Entity("", 1, 0)], [EntityDataIndex(1, 0)]) != ComponentContainer(bool, [True], [Entity("", 2, 0)], [EntityDataIndex(1, 0)])

    def test_type_checking(self) -> None:
        container = ComponentContainer.new(bool)
        container.add(Entity("anon", 1, 0), True)
        with pytest.raises(TypeError):
            container.add(Entity("anon", 2, 1), 1.0)

    def test_to_dict(self) -> None:
        component = ExampleComponent(1.0)
        entity = Entity("anon", 1, 0)
        idx = EntityDataIndex(0, 0)
        assert ComponentContainer(bool, [True], [entity], [idx]).to_dict() == {"data": [True], "entities": [entity.to_dict()], "indices": [idx.to_dict()]}
        assert ComponentContainer(ExampleComponent, [component], [entity], [idx]).to_dict() == {"data": [component.to_dict()], "entities": [entity.to_dict()], "indices": [idx.to_dict()]}

    def test_from_dict(self) -> None:
        component = ExampleComponent(1.0)
        entity = Entity("anon", 1, 0)
        idx = EntityDataIndex(0, 0)
        ca = ComponentContainer.from_dict(bool, {"data": [True], "entities": [entity.to_dict()], "indices": [idx.to_dict()]})
        assert ca == ComponentContainer(bool, [True], [entity], [idx])
        cb = ComponentContainer.from_dict(ExampleComponent, {"data": [component.to_dict()], "entities": [entity.to_dict()], "indices": [idx.to_dict()]})
        assert cb == ComponentContainer(ExampleComponent, [component], [entity], [idx])


class TestAssembly(object):
    def test_to_dict(self) -> None:
        component = ExampleComponent(1.0)
        entity = Entity("anon", 1, 0)
        idx = EntityDataIndex(0, 0)
        container_a = ComponentContainer(int, [1], [entity], [idx])
        container_b = ComponentContainer(ExampleComponent, [component], [entity], [idx])
        assembly = ExampleAssembly(container_a, container_b)
        assert assembly.to_dict() == {"a": container_a.to_dict(), "b": container_b.to_dict()}

    def test_from_dict(self) -> None:
        component = ExampleComponent(1.0)
        entity = Entity("anon", 1, 0)
        idx = EntityDataIndex(0, 0)
        container_a = ComponentContainer(int, [1], [entity], [idx])
        container_b = ComponentContainer(ExampleComponent, [component], [entity], [idx])
        assembly = ExampleAssembly(container_a, container_b)
        a = ExampleAssembly.from_dict({"a": container_a.to_dict(), "b": container_b.to_dict()})
        assert a == assembly


class TestSystem(object):
    def test_system(self) -> None:
        sys_a = ExampleSystem()
        sys_b = ExampleSystem()

        assert sys_a == sys_b
        assert sys_a == "ExampleSystem"


class TestWorld(object):
    def test_world(self) -> None:
        world = World.new(ExampleAssembly.new())
        e = world.make("e")
        world.components.a.add(e, 1)
        world.components.b.add(e, ExampleComponent(1.0))

        f = world.make("f")
        world.components.a.add(f, 2)

        g = world.make("g")
        world.components.b.add(g, ExampleComponent(3.0))

        world.add_system(ExampleSystem())
        world.render()

    def test_system_management(self) -> None:
        world = World.new(ExampleAssembly.new())
        world.add_system(ExampleSystem())
        with pytest.raises(ValueError):
            world.add_system(ExampleSystem())

        world.remove_system("ExampleSystem")
        with pytest.raises(ValueError):
            world.remove_system("ExampleSystem")

    def test_to_dict(self) -> None:
        assembly = ExampleAssembly.new()
        world = World.new(assembly)
        entity = world.make("anon")
        world.components.a.add(entity, 1)
        world.components.b.add(entity, ExampleComponent(1.0))
        world.add_system(ExampleSystem())
        assert world.to_dict() == {
            "next_entity": Entity("", 2, 1).to_dict(),
            "free_indices": [],
            "entities": world.entities.to_dict(),
            "components": assembly.to_dict(),
            "systems": [{"class": "ExampleSystem", "kwargs": {}}]
        }

    def test_from_dict(self) -> None:
        assembly = ExampleAssembly.new()
        world = World.new(assembly)
        entity = world.make("anon")
        world.components.a.add(entity, 1)
        world.components.b.add(entity, ExampleComponent(1.0))
        world.add_system(ExampleSystem())
        serialized_world = {
            "next_entity": Entity("", 2, 1).to_dict(),
            "free_indices": [],
            "entities": world.entities.to_dict(),
            "components": assembly.to_dict(),
            "systems": [{"class": "ExampleSystem", "kwargs": {}}]
        }
        w = World.from_dict(ExampleAssembly, serialized_world)
        assert w == world