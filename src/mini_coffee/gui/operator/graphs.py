import json, time
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import (QPainter)
from PySide6.QtWidgets  import (QWidget, QHBoxLayout, QVBoxLayout)
from typing import Optional, Dict, Any
from mini_coffee.utils.logger import setup_logger
from collections import dataclass

logger = setup_logger()

def debugger(func):
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__} with args: {args}, kwargs: {kwargs}")
        result = func(*args, **kwargs)
        return result
    return wrapper

@dataclass
class Pos:
    x: float
    y: float
    z: float
    roll: float
    pitch: float
    yaw: float

    def __str__(self) -> str:
        return (
            f"Pos("
            f"x={self.x}, "
            f"y={self.y}, "
            f"z={self.z}, "
            f"roll={self.roll}, "
            f"pitch={self.pitch}, "
            f"yaw={self.yaw}"
            f")"
        )
    
class CalibrationWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Calibration Window")
        self.item_list = ItemList()
        self.recipe_tab = RecipeTab()
        self.coord_panel = CoordPanel()
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()

        # Left Items List panel
        self.item_list.setMinimumWidth(250)
        layout.addWidget(self.item_list)

        # Maib panel with Recipies
        layout.addWidget(self.recipe_tab)

        # Additional panel for coordinates
        layout.addWidget(self.coord_panel)
        self.coord_panel.hide()

        self.setLayout(layout)

class ItemList(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.current_expanded = None

    def add_item(self, icon_path:  str, name: str, pos: Pos, settings: dict) -> None:
        pass
        