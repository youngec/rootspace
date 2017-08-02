# -*- coding: utf-8 -*-

import abc
import collections
import enum
import json
import pathlib
from typing import List, TypeVar, Generic, Optional, Sequence, Type, Deque, Iterator, Any, Dict, Union


C = TypeVar("C")
S = TypeVar("S", bound="SerDeTrait")


class SerDeTrait(object, metaclass=abc.ABCMeta):
    @classmethod
    @abc.abstractmethod
    def new(cls) -> "SerDeTrait":
        """
        Construct a new, default instance.
        """
        pass

    @abc.abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        Return a dictionary-based representation of the instance.
        """
        pass

    def to_json(self, json_file: pathlib.Path, indent: Optional[int] = None) -> None:
        """
        Serialize an instance to JSON.
        """
        with json_file.open("w") as jf:
            json.dump(self.to_dict(), jf, indent=indent)

    @classmethod
    @abc.abstractmethod
    def from_dict(cls: Type[S], obj: Dict[str, Any]) -> S:
        """
        Construct an instance from a dictionary.
        """
        pass

    @classmethod
    def from_json(cls: Type[S], json_file: pathlib.Path) -> S:
        """
        Deserialize an instance from a JSON file.
        """
        with json_file.open("r") as jf:
            return cls.from_dict(json.load(jf))
        

class Scene(SerDeTrait):
    def __init__(self, systems: Sequence[Dict[str, Union[str, Dict[str, Any]]]], entities: Dict[str, Sequence[str]], components: Dict[str, Dict[str, Any]]) -> None:
        self.systems = systems
        self.entities = entities
        self.components = components

    @classmethod
    def new(cls) -> "Scene":
        return cls(
            systems=[
                {"class": "player_movement_system", "kwargs": {}},
                {"class": "camera_control_system", "kwargs": {}},
                {"class": "physics_system", "kwargs": {}},
                {"class": "collision_system", "kwargs": {}},
                {"class": "open_gl_renderer", "kwargs": {}}
            ],
            entities={
                "camera": ["cam_trf", "cam_proj", "cam_bv", "cam_phys_prop", "cam_phys_state"],
                "floor": ["floor_trf", "floor_mdl", "floor_bv"],
                "cube": ["cube_trf", "cube_mdl", "cube_bv", "cube_prp", "cube_sta"],
                "table": ["table_trf", "table_mdl", "table_bv"]
            },
            components={
                "cam_trf": {"class": "transform", "kwargs": {"camera": True}},
                "cam_proj": {"class": "projection", "kwargs": {"field_of_view": 0.78539716, "window_shape": "window_shape", "near_plane": 0.1, "far_plane": 1000.0}},
                "cam_bv": {"class": "bounding_volume", "kwargs": {}},
                "cam_phys_prop": {"class": "physics_properties", "kwargs": {"g": [0, 0, 0]}},
                "cam_phys_state": {"class": "physics_state", "kwargs": {}},
                "floor_trf": {"class": "transform", "kwargs": {"position": [0, -2, -10], "orientation": [0, 0, 0, 1], "scale": [8, 0.1, 8]}},
                "floor_bv": {"class": "bounding_volume", "kwargs": {}},
                "floor_mdl": {"class": "model", "kwargs": {"mesh_path": "models/floor.ply", "vertex_shader_path": "shaders/floor-vertex.glsl", "fragment_shader_path": "shaders/floor-fragment.glsl"}},
                "cube_trf": {"class": "transform", "kwargs": {"position": [0, 1, -10], "orientation": [0, 0, 0, 1], "scale": [0.5, 0.5, 0.5]}},
                "cube_bv": {"class": "bounding_volume", "kwargs": {}},
                "cube_mdl": {"class": "model", "kwargs": {"mesh_path": "models/cube.ply", "vertex_shader_path": "shaders/cube-vertex.glsl", "fragment_shader_path": "shaders/cube-fragment.glsl"}},
                "cube_prp": {"class": "physics_properties", "kwargs": {}},
                "cube_sta": {"class": "physics_state", "kwargs": {}},
                "table_trf": {"class": "transform", "kwargs": {"position": [10, 0, -10], "orientation": [0, 0, 0, 1], "scale": [1, 1, 1]}},
                "table_bv": {"class": "bounding_volume", "kwargs": {}},
                "table_mdl": {"class": "model", "kwargs": {"mesh_path": "models/table.ply", "vertex_shader_path": "shaders/table-vertex.glsl", "fragment_shader_path": "shaders/table-fragment.glsl", "texture_path": "textures/table.png"}}
            }
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "systems": self.systems,
            "entities": self.entities,
            "components": self.components
        }

    @classmethod
    def from_dict(cls: Type["Scene"], obj: Dict[str, Any]) -> "Scene":
        return cls(
            systems=[{"class": str(s["class"]), "kwargs": dict(s["kwargs"])} for s in obj["systems"]],
            entities={str(name): [str(c) for c in comps] for name, comps in obj["entities"].items()},
            components={str(name): {"class": str(comp["class"]), "kwargs": dict(comp["kwargs"])} for name, comp in obj["components"].items()}
        )

class EventTrait(object, metaclass=abc.ABCMeta):
    """
    Abstract base class of an event.
    """
    __slots__ = ()


class SceneEvent(EventTrait):
    __slots__ = ("scene",)

    def __init__(self, scene: Scene) -> None:
        self.scene = scene



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
    def new(cls, assembly: AssemblyTrait, scene: Optional[Scene] = None) -> "World":
        inst = cls(
            next_entity=Entity(name="", uuid=1, idx=0),
            free_indices=collections.deque(),
            entities=ComponentContainer.new(),
            components=assembly,
            systems=list(),
            event_queue=collections.deque(),
        )
        if scene is not None:
            inst.load_scene(scene)
        return inst

    def load_scene(self, scene: Scene) -> None:
        raise NotImplementedError()

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
        self.systems.append(system)

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