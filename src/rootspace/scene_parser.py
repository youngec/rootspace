# -*- coding: utf-8 -*-

import json
import pathlib
import attr


@attr.s
class SceneParser(object):
    def load(self, scene_path):
        if not isinstance(scene_path, pathlib.Path):
            scene_path = pathlib.Path(scene_path)

        with scene_path.open(mode="r") as f:
            scene_tree = json.load(f)
