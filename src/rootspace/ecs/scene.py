# -*- coding: utf-8 -*-

from typing import Dict, Union, Sequence, Any, Type

from rootspace.ecs.serialization import SerDeTrait


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
