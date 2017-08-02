# -*- coding: utf-8 -*-

from typing import Tuple, Dict, Any, Type

from .ecs import SerDeTrait


class Config(SerDeTrait):
    """
    Contains all persistent engine configuration.
    """
    def __init__(self, title: str, visibility: bool, fullscreen: bool, shape: Tuple[int, int], vsync: bool, clear_color: Tuple[float, float, float, float], cursor_mode: int, cursor_origin: Tuple[int, int], depth_test: bool, depth_function: int, face_culling: bool, front_face: int, cull_face: int, delta_time: float, max_frame_duration: float, epsilon: float) -> None:
        self.title = title
        self.visibility = visibility
        self.fullscreen = fullscreen
        self.shape = shape
        self.vsync = vsync
        self.clear_color = clear_color
        self.cursor_mode = cursor_mode
        self.cursor_origin = cursor_origin
        self.depth_test = depth_test
        self.depth_function = depth_function
        self.face_culling = face_culling
        self.front_face = front_face
        self.cull_face = cull_face
        self.delta_time = delta_time
        self.max_frame_duration = max_frame_duration
        self.epsilon = epsilon

    @classmethod
    def new(cls) -> "Config":
        """
        Create a new default instance of `Config`.
        """
        return cls(
            title="Rootspace",
            visibility=True,
            fullscreen=False,
            shape=(1024, 768),
            vsync=True,
            clear_color=(0.0, 0.0, 0.0, 0.0),
            cursor_mode=212995,
            cursor_origin=(512, 384),
            depth_test=True,
            depth_function=513,
            face_culling=True,
            front_face=2305,
            cull_face=1029,
            delta_time=0.01,
            max_frame_duration=0.25,
            epsilon=1e-5
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Return a dictionary-based representation of `Config`.
        """
        return {
            "title": self.title,
            "visibility": self.visibility,
            "fullscreen": self.fullscreen,
            "shape": self.shape,
            "vsync": self.vsync,
            "clear_color": self.clear_color,
            "cursor_mode": self.cursor_mode,
            "cursor_origin": self.cursor_origin,
            "depth_test": self.depth_test,
            "depth_function": self.depth_function,
            "face_culling": self.face_culling,
            "front_face": self.front_face,
            "cull_face": self.cull_face,
            "delta_time": self.delta_time,
            "max_frame_duration": self.max_frame_duration,
            "epsilon": self.epsilon
        }
    
    @classmethod
    def from_dict(cls: Type["Config"], obj: Dict[str, Any]) -> "Config":
        """
        Construct an instance of `Config` from a dictionary.
        """
        return cls(
            title=str(obj["title"]),
            visibility=bool(obj["visibility"]),
            fullscreen=bool(obj["fullscreen"]),
            shape=(int(obj["shape"][0]), int(obj["shape"][1])),
            vsync=bool(obj["vsync"]),
            clear_color=(float(obj["clear_color"][0]), float(obj["clear_color"][1]), float(obj["clear_color"][2]), float(obj["clear_color"][3])),
            cursor_mode=int(obj["cursor_mode"]),
            cursor_origin=(int(obj["cursor_origin"][0]), int(obj["cursor_origin"][1])),
            depth_test=bool(obj["depth_test"]),
            depth_function=int(obj["depth_function"]),
            face_culling=bool(obj["face_culling"]),
            front_face=int(obj["front_face"]),
            cull_face=int(obj["cull_face"]),
            delta_time=float(obj["delta_time"]),
            max_frame_duration=float(obj["max_frame_duration"]),
            epsilon=float(obj["epsilon"])
        )
