# -*- coding: utf-8 -*-

import abc
import collections
import enum
from typing import Generic, TypeVar, List, Optional, Iterator, Deque, Sequence, Any, Dict, Type, Union

from .serialization import SerDeTrait

C = TypeVar("C")
A = TypeVar("A", bound="AssemblyTrait")
E = TypeVar("E", bound="EventTrait")
S = TypeVar("S", bound="SystemTrait")


class EventTrait(object, metaclass=abc.ABCMeta):
    """
    Abstract base class of an event. Events should not carry around a lot of data.
    """
    __slots__ = ()


class Entity(object):
    __slots__ = ("name", "uuid", "idx")

    def __init__(self, name: str, uuid: int, idx: int) -> None:
        self.name = name
        self.uuid = uuid
        self.idx = idx

    def __repr__(self) -> str:
        return "Entity({})".format(self.name)
    
    def __str__(self) -> str:
        return repr(self)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Entity):
            return self.name == other.name and self.uuid == other.uuid and self.idx == other.idx
        else:
            return False

    def increment(self) -> None:
        self.uuid += 1
        self.idx += 1

    def clone(self) -> "Entity":
        return Entity(
            name=self.name,
            uuid=self.uuid, 
            idx=self.idx
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "uuid": self.uuid,
            "idx": self.idx
        }

    @classmethod
    def from_dict(cls, obj: Dict[str, Any]) -> "Entity":
        return cls(
            name=str(obj["name"]),
            uuid=int(obj["uuid"]),
            idx=int(obj["idx"])
        )


class EntityDataIndex(object):
    __slots__ = ("uuid", "data_idx")

    def __init__(self, uuid: int, data_idx: int) -> None:
        self.uuid = uuid
        self.data_idx = data_idx

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, EntityDataIndex):
            return self.uuid == other.uuid and self.data_idx == other.data_idx
        else:
            return False

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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "uuid": self.uuid,
            "data_idx": self.data_idx
        }

    @classmethod
    def from_dict(cls, obj: Dict[str, Any]) -> "EntityDataIndex":
        return cls(
            uuid=int(obj["uuid"]),
            data_idx=int(obj["data_idx"])
        )


class ComponentContainer(Generic[C]):
    __slots__ = ("data_type", "data", "entities", "indices")

    def __init__(self, data_type: Type[C], data: List[C], entities: List[Entity], indices: List[EntityDataIndex]) -> None:
        self.data_type = data_type
        self.data = data
        self.entities = entities
        self.indices = indices

    def __iter__(self) -> Iterator[C]:
        yield from self.data

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, ComponentContainer):
            return self.data_type == other.data_type and self.data == other.data and self.entities == other.entities and self.indices == other.indices
        else:
            return False

    @classmethod
    def new(cls, data_type: Type[C]) -> "ComponentContainer":
        return cls(
            data_type=data_type,
            data=list(),
            entities=list(),
            indices=list()
        )

    def contains(self, entity: Entity) -> bool:
        assert(entity.uuid > 0)
        return (entity.idx < len(self.indices)) and (self.indices[entity.idx].uuid == entity.uuid)

    def add(self, entity: Entity, component: C) -> None:
        if not isinstance(component, self.data_type):
            raise TypeError("This ComponentContainer can only collect objects of type '{}'".format(self.data_type.__name__))

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

    def to_dict(self) -> Dict[str, Any]:
        if all(isinstance(c, (type(None), bool, int, float, str)) for c in self.data):
            return {
                "data": [c for c in self.data],
                "entities": [e.to_dict() for e in self.entities],
                "indices": [i.to_dict() for i in self.indices]
            }
        elif all(isinstance(c, SerDeTrait) for c in self.data):
            return {
                "data": [c.to_dict() for c in self.data],
                "entities": [e.to_dict() for e in self.entities],
                "indices": [i.to_dict() for i in self.indices]
            }
        else:
            raise TypeError("Cannot serialize the following object: {!r}".format(type(self.data[0])))

    @classmethod
    def from_dict(cls: Type["ComponentContainer"], component_class: Union[Type[None], Type[bool], Type[int], Type[float], Type[str], Type[SerDeTrait]], obj: Dict[str, Any]) -> "ComponentContainer":
        if issubclass(component_class, (type(None), bool, int, float, str)):
            return cls(
                data_type=component_class,
                data=[c for c in obj["data"]],
                entities=[Entity.from_dict(e) for e in obj["entities"]],
                indices=[EntityDataIndex.from_dict(i) for i in obj["indices"]]
            )
        elif issubclass(component_class, SerDeTrait):
            return cls(
                data_type=component_class,
                data=[component_class.from_dict(c) for c in obj["data"]],
                entities=[Entity.from_dict(e) for e in obj["entities"]],
                indices=[EntityDataIndex.from_dict(i) for i in obj["indices"]]
            )
        else:
            raise TypeError("Cannot deserialize the following object: {!r}".format(component_class))


class ViewTrait(object, metaclass=abc.ABCMeta):
    pass


class LoopStage(enum.Enum):
    Dispatch = 0
    Update = 1
    Render = 2


class SystemTrait(object, metaclass=abc.ABCMeta):
    __slots__ = ()

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, SystemTrait) and other.get_name() == self.get_name():
            return True
        elif isinstance(other, str) and other == self.get_name():
            return True
        else:
            return False

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

    def to_dict(self) -> Dict[str, Any]:
        return {}

    @classmethod
    def from_dict(cls: Type[S], obj: Dict[str, Any]) -> S:
        return cls()


class AssemblyTrait(object, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def match_mask(self, entity: Entity, mask: int) -> bool:
        pass

    @abc.abstractmethod
    def remove(self, entity: Entity) -> None:
        pass

    @abc.abstractmethod
    def get_view(self, entity: Entity) -> ViewTrait:
        pass

    @abc.abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass

    @classmethod
    @abc.abstractmethod
    def from_dict(cls: Type[A], obj: Dict[str, Any]) -> A:
        pass

    @classmethod
    @abc.abstractmethod
    def get_known_systems(cls) -> Dict[str, Type[SystemTrait]]:
        pass


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

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, World):
            return self.next_entity == other.next_entity and self.free_indices == other.free_indices and self.entities == other.entities and self.components == other.components and self.systems == other.systems and self.event_queue == other.event_queue
        else:
            return False

    @classmethod
    def new(cls, assembly: AssemblyTrait) -> "World":
        return cls(
            next_entity=Entity(name="", uuid=1, idx=0),
            free_indices=collections.deque(),
            entities=ComponentContainer.new(bool),
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

    def remove_system(self, system_name: str) -> None:
        self.systems.remove(system_name)

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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "next_entity": self.next_entity.to_dict(),
            "free_indices": [i for i in self.free_indices],
            "entities": self.entities.to_dict(),
            "components": self.components.to_dict(),
            "systems": [{"class": s.__class__.__name__, "kwargs": s.to_dict()} for s in self.systems]
        }

    @classmethod
    def from_dict(cls, assembly_class: Type[AssemblyTrait], obj: Dict[str, Any]) -> "World":
        known_systems = assembly_class.get_known_systems()
        return cls(
            next_entity=Entity.from_dict(obj["next_entity"]),
            free_indices=collections.deque(int(i) for i in obj["free_indices"]),
            entities=ComponentContainer.from_dict(bool, obj["entities"]),
            components=assembly_class.from_dict(obj["components"]),
            systems=[known_systems[s["class"]].from_dict(s["kwargs"]) for s in obj["systems"]],
            event_queue=collections.deque()
        )