# -*- coding: utf-8 -*-

import abc
import collections
import enum
from typing import Generic, TypeVar, List, Optional, Iterator, Deque, Sequence, Any

C = TypeVar("C")


class EventTrait(object, metaclass=abc.ABCMeta):
    """
    Abstract base class of an event.
    """
    __slots__ = ()


class Entity(object):
    __slots__ = ("name", "uuid", "idx")

    def __init__(self, name: str, uuid: int, idx: int) -> None:
        self.name = name
        self.uuid = uuid
        self.idx = idx

    def increment(self) -> None:
        self.uuid += 1
        self.idx += 1

    def clone(self) -> "Entity":
        return Entity(
            name=self.name,
            uuid=self.uuid, 
            idx=self.idx
        )

    def __repr__(self) -> str:
        return "Entity({})".format(self.name)
    
    def __str__(self) -> str:
        return repr(self)


class EntityDataIndex(object):
    __slots__ = ("uuid", "data_idx")

    def __init__(self, uuid: int, data_idx: int) -> None:
        self.uuid = uuid
        self.data_idx = data_idx

    @classmethod
    def new(cls) -> "EntityDataIndex":
        return cls(
            uuid=0,
            data_idx=0
        )

    def clone(self) -> "EntityDataIndex":
        return EntityDataIndex(
            uuid=self.uuid,
            data_idx=self.data_idx
        )


class ComponentContainer(Generic[C]):
    __slots__ = ("data", "entities", "indices")

    def __init__(self, data: List[C], entities: List[Entity], indices: List[EntityDataIndex]) -> None:
        self.data = data
        self.entities = entities
        self.indices = indices

    @classmethod
    def new(cls) -> "ComponentContainer":
        return cls(
            data=list(),
            entities=list(),
            indices=list()
        )

    def contains(self, entity: Entity) -> bool:
        assert(entity.uuid > 0)
        return (entity.idx < len(self.indices)) and (self.indices[entity.idx].uuid == entity.uuid)

    def add(self, entity: Entity, component: C) -> None:
        assert(len(self.data) == len(self.entities))
        if self.contains(entity):
            self.data[self.indices[entity.idx].data_idx] = component
        else:
            if entity.idx >= len(self.indices):
                # resize the indices vector
                for _ in range(len(self.indices), entity.idx + 1):
                    self.indices.append(EntityDataIndex.new())
            
            self.data.append(component)
            self.entities.append(entity.clone())
            self.indices[entity.idx] = EntityDataIndex(
                uuid=entity.uuid,
                data_idx=len(self.data) - 1
            )

    def remove(self, entity: Entity) -> None:
        assert(len(self.data) == len(self.entities))
        if self.contains(entity):
            removed_idx = self.indices[entity.idx].clone()
            self.indices[entity.idx] = EntityDataIndex.new()

            if removed_idx.data_idx != len(self.entities) - 1:
                last_entity = self.entities[-1].clone()
                self.entities.pop(removed_idx.data_idx)
                self.indices[last_entity.idx] = EntityDataIndex(
                    uuid=last_entity.uuid,
                    data_idx=removed_idx.data_idx
                )
            else:
                self.entities.pop(removed_idx.data_idx)

    def get(self, entity: Entity) -> Optional[C]:
        if self.contains(entity):
            return self.data[self.indices[entity.idx].data_idx]
        else:
            return None

    def iter_ent(self) -> Iterator[Entity]:
        yield from self.entities

    def __iter__(self) -> Iterator[C]:
        yield from self.data


class ViewTrait(object, metaclass=abc.ABCMeta):
    __slots__ = ()


class AssemblyTrait(object, metaclass=abc.ABCMeta):
    __slots__ = ()

    @classmethod
    @abc.abstractmethod
    def new(cls) -> "AssemblyTrait":
        pass

    @abc.abstractmethod
    def match_mask(self, entity: Entity, mask: int) -> bool:
        pass

    @abc.abstractmethod
    def remove(self, entity: Entity) -> None:
        pass

    @abc.abstractmethod
    def get_view(self, entity: Entity) -> ViewTrait:
        pass


class LoopStage(enum.Enum):
    Dispatch = 0
    Update = 1
    Render = 2


class SystemTrait(object, metaclass=abc.ABCMeta):
    __slots__ = ()

    @abc.abstractmethod
    def get_name(self) -> str:
        pass

    @abc.abstractmethod
    def get_mask(self) -> int:
        pass

    @abc.abstractmethod
    def get_stage(self) -> LoopStage:
        pass

    def on_event(self, components: Sequence[ViewTrait], event: EventTrait) -> None:
        pass

    def update(self, components: Sequence[ViewTrait], time: float, delta_time: float) -> None:
        pass

    def render(self, components: Sequence[ViewTrait]) -> None:
        pass

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, SystemTrait) and other.__class__.__name__ == self.__class__.__name__:
            return True
        else:
            return NotImplemented


class World(object):
    __slots__ = ("next_entity", "free_indices", "entities", "components", "systems", "event_queue")

    def __init__(self, next_entity: Entity, free_indices: Deque[int], entities: ComponentContainer[bool], 
                 components: AssemblyTrait, systems: List[SystemTrait], event_queue: Deque[EventTrait]) -> None:
        self.next_entity = next_entity
        self.free_indices = free_indices
        self.entities = entities
        self.components = components
        self.systems = systems
        self.event_queue = event_queue

    @classmethod
    def new(cls, assembly: AssemblyTrait) -> "World":
        return cls(
            next_entity=Entity(name="", uuid=1, idx=0),
            free_indices=collections.deque(),
            entities=ComponentContainer.new(),
            components=assembly,
            systems=list(),
            event_queue=collections.deque(),
        )

    def make(self, name: str) -> Entity:
        entity = Entity(
            name=name,
            uuid=self.next_entity.uuid,
            idx=(self.free_indices.popleft() if len(self.free_indices) > 0 else self.next_entity.idx)
        )
        self.next_entity.increment()
        self.entities.add(entity, True)
        return entity

    def remove(self, entity: Entity) -> None:
        self.free_indices.append(entity.idx)
        self.entities.remove(entity)
        self.components.remove(entity)

    def add_system(self, system: SystemTrait) -> None:
        if system not in self.systems:
            self.systems.append(system)
        else:
            raise ValueError("Attempting to activate an already present system: '{}'".format(system.__class__.__name__))

    def process_events(self) -> None:
        while len(self.event_queue) > 0:
            self.dispatch(self.event_queue.popleft())

    def queue(self, event: EventTrait) -> None:
        self.event_queue.append(event)

    def dispatch(self, event: EventTrait) -> None:
        assembly = self.components
        for system in self.systems:
            if system.get_stage() is LoopStage.Event:
                mask = system.get_mask()
                candidates = (e.clone() for e in self.entities.iter_ent() if assembly.match_mask(e, mask))
                components = [assembly.get_view(e) for e in candidates]

                if len(components) > 0:
                    system.on_event(components, event)

    def update(self, time: float, delta_time: float) -> None:
        assembly = self.components

        for system in self.systems:
            if system.get_stage() is LoopStage.Update:
                mask = system.get_mask()
                candidates = (e.clone() for e in self.entities.iter_ent() if assembly.match_mask(e, mask))
                components = [assembly.get_view(e) for e in candidates]

                if len(components) > 0:
                    system.update(components, time, delta_time)

    def render(self) -> None:
        assembly = self.components

        for system in self.systems:
            if system.get_stage() is LoopStage.Render:
                mask = system.get_mask()
                candidates = (e.clone() for e in self.entities.iter_ent() if assembly.match_mask(e, mask))
                components = [assembly.get_view(e) for e in candidates]

                if len(components) > 0:
                    system.render(components)