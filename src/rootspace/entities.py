# -*- coding: utf-8 -*-

import uuid

from .components import Transform, Projection, Model, PhysicsState, PhysicsProperties, BoundingVolume
from .utilities import camelcase_to_underscore


class EntityMeta(type):
    """
    EntityMeta registers all Entities in EntityMeta.classes
    """
    classes = dict()

    def __new__(mcs, name, bases, cls_dict):
        register = cls_dict.pop("register", True)
        cls = super(EntityMeta, mcs).__new__(mcs, name, bases, cls_dict)
        if register:
            mcs.classes[camelcase_to_underscore(cls.__name__)] = cls

        return cls


class Entity(object, metaclass=EntityMeta):
    """
    An entity is a container with a unique identifier.
    """
    def __init__(self, name: str) -> None:
        self.name = name
        self._ident = uuid.uuid4()

    @property
    def components(self):
        raise NotImplementedError()

    def __hash__(self) -> int:
        return self._ident.int

    def __repr__(self) -> str:
        return "{}(...)".format(self.__class__.__name__)

    def __str__(self) -> str:
        return "{} ({})".format(self.name, self.__class__.__name__)


class Camera(Entity):
    def __init__(self, name: str, transform: Transform, projection: Projection,
                 bounding_volume: BoundingVolume,
                 physics_properties: PhysicsProperties,
                 physics_state: PhysicsState) -> None:
        super(Camera, self).__init__(name)
        self.transform = transform
        self.projection = projection
        self.bounding_volume = bounding_volume
        self.physics_properties = physics_properties
        self.physics_state = physics_state

    @property
    def components(self):
        return (self.transform, self.projection, self.bounding_volume,
                self.physics_properties, self.physics_state)


class StaticObject(Entity):
    def __init__(self, name: str, transform: Transform, model: Model,
                 bounding_volume: BoundingVolume) -> None:
        super(StaticObject, self).__init__(name)
        self.transform = transform
        self.model = model
        self.bounding_volume = bounding_volume

    @property
    def components(self):
        return (self.transform, self.model, self.bounding_volume)


class DynamicObject(Entity):
    def __init__(self, name: str, transform: Transform, model: Model,
                 bounding_volume: BoundingVolume,
                 physics_properties: PhysicsProperties,
                 physics_state: PhysicsState) -> None:
        super(DynamicObject, self).__init__(name)
        self.transform = transform
        self.model = model
        self.bounding_volume = bounding_volume
        self.physics_properties = physics_properties
        self.physics_state = physics_state

    @property
    def components(self):
        return (self.transform, self.model, self.bounding_volume,
                self.physics_properties, self.physics_state)

