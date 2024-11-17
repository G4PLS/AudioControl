"""
Author: G4PLS
Year: 2024
"""

import json
import os.path

from .AssetManagerBackend import Asset, Manager
from src.backend.DeckManagement.Media.Media import Media


class Color(Asset):
    def __init__(self, *args, **kwargs):
        self._color: tuple[int, int, int, int] = (0,0,0,0)

        super().__init__(*args, **kwargs)

    def change(self, *args, **kwargs):
        self._color = kwargs.get("color", (0,0,0,0))

    def get_values(self):
        return self._color

    def to_json(self):
        return list(self._color)

    @classmethod
    def from_json(cls, *args):
        return cls(color=tuple(args[0]))

class Icon(Asset):
    def __init__(self, *args, **kwargs):
        self._icon: Media = None
        self._rendered: Media = None
        self._path: str = None

        super().__init__(*args, **kwargs)

    def change(self, *args, **kwargs):
        path = kwargs.get("path", None)

        if os.path.isfile(path):
            self._path = path
            self._icon = Media.from_path(path)
            self._rendered = self._icon.get_final_media()

    def get_values(self):
        return self._icon, self._rendered

    def to_json(self):
        return self._path

    @classmethod
    def from_json(cls, *args):
        return cls(path=args[0])

class AssetManager:
    def __init__(self, save_path: str):
        self.save_path = save_path
        self.colors = Manager(Color, "colors")
        self.icons = Manager(Icon, "icons")
        self.load()

    def save(self):
        save_json = {}
        save_json[self.colors.get_save_key()] = self.colors.get_override_json()
        save_json[self.icons.get_save_key()] = self.icons.get_override_json()

        with open(self.save_path, "w") as file:
            json.dump(save_json, file, indent = 4)

    def load(self):
        if not os.path.isfile(self.save_path):
            return

        with open(self.save_path) as file:
            json_data = json.load(file)

        if json_data:
            self.icons.load_json(json_data)
            self.colors.load_json(json_data)