# -*- coding: utf-8 -*-

from typing import Tuple, Dict, Any
import pathlib
import json


class Config(object):
    """
    Contains all persistent engine configuration:

    # Parameters
    * `title`: Title of the render window
    * `visibility`: Controls window visibility
    * `fullscreen`: Determines whether to render in windowed mode or fullscreen
    * `shape`: Determines the window shape, also sets the resolution
    * `vsync`: Controls vertical buffer synchronization
    * `clear_color`: Determines the renderer background color
    * `delta_time`: Controls the fixed time step of the physics simulation
    * `max_frame_duration`: Determines the maximum duration of a single frame
    * `epsilon`: Determines the smallest non-zero floating point number
    """
    def __init__(self, title: str, visibility: bool, fullscreen: bool, shape: Tuple[int, int], vsync: bool, clear_color: Tuple[float, float, float, float], delta_time: float, max_frame_duration: float, epsilon: float) -> None:
        self.title = title
        self.visibility = visibility
        self.fullscreen = fullscreen
        self.shape = shape
        self.vsync = vsync
        self.clear_color = clear_color
        self.delta_time = delta_time
        self.max_frame_duration = max_frame_duration
        self.epsilon = epsilon

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
            "delta_time": self.delta_time,
            "max_frame_duration": self.max_frame_duration,
            "epsilon": self.epsilon
        }
    
    def to_json(self, json_file: pathlib.Path) -> None:
        """
        Serialize an instance of `Config` to JSON.
        """
        with json_file.open("w") as jf:
            json.dump(self.to_dict(), jf)

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
            delta_time=0.01,
            max_frame_duration=0.25,
            epsilon=1e-5
        )

    @classmethod
    def from_dict(cls, obj: Dict[str, Any]) -> "Config":
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
            delta_time=float(obj["delta_time"]),
            max_frame_duration=float(obj["max_frame_duration"]),
            epsilon=float(obj["epsilon"])
        )

    @classmethod
    def from_json(cls, json_file: pathlib.Path) -> "Config":
        """
        Deserialize an instance of `Config` from a JSON file.
        """
        with json_file.open("r") as jf:
            return cls.from_dict(json.load(jf))