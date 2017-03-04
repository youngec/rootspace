# -*- coding: utf-8 -*-

import uuid

import attr
from attr.validators import instance_of

from .components import Transform, Projection, Model, PhysicsState, PhysicsProperties, BoundingVolume
from .utilities import camelcase_to_underscore


class EntityMeta(type):
    """
    EntityMeta registers all Entities in EntityMeta.classes
    """
    classes = dict()

    def __new__(meta, name, bases, cls_dict):
        register = cls_dict.pop("register", True)
        cls_dict["_ident"] = uuid.uuid4()
        cls = super(EntityMeta, meta).__new__(meta, name, bases, cls_dict)
        if register:
            meta.classes[camelcase_to_underscore(cls.__name__)] = cls

        return cls


@attr.s(hash=False)
class Entity(object, metaclass=EntityMeta):
    """
    An entity is a container with a unique identifier.
    """
    @property
    def components(self):
        return attr.astuple(self, recurse=False, filter=lambda a, c: not a.name.startswith("_"))

    def __hash__(self):
        return self._ident.int


@attr.s(hash=False)
class Camera(Entity):
    transform = attr.ib(validator=instance_of(Transform))
    projection = attr.ib(validator=instance_of(Projection))
    bounding_volume = attr.ib(validator=instance_of(BoundingVolume))
    physics_properties = attr.ib(validator=instance_of(PhysicsProperties))
    physics_state = attr.ib(validator=instance_of(PhysicsState))


@attr.s(hash=False)
class StaticObject(Entity):
    transform = attr.ib(validator=instance_of(Transform))
    model = attr.ib(validator=instance_of(Model))
    bounding_volume = attr.ib(validator=instance_of(BoundingVolume))


@attr.s(hash=False)
class DynamicObject(Entity):
    transform = attr.ib(validator=instance_of(Transform))
    model = attr.ib(validator=instance_of(Model))
    bounding_volume = attr.ib(validator=instance_of(BoundingVolume))
    physics_properties = attr.ib(validator=instance_of(PhysicsProperties))
    physics_state = attr.ib(validator=instance_of(PhysicsState))

