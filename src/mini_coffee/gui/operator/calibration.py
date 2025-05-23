# src/mini_coffee/gui/operator/calibration.py
import json
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsPixmapItem,
    QGraphicsEllipseItem, QGraphicsSimpleTextItem, QGraphicsPathItem, QMenu
)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QPainterPath, QPixmap, QMouseEvent
)
from mini_coffee.hardware.arm.controller import MockArmController
from typing import Dict, Optional


class SchematicView(QGraphicsView):
    component_clicked = Signal(str)
    
    def __init__(self):
        super().__init__()
        
        self._scene = QGraphicsScene()
        self.setScene(self._scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Component format: (x, y, icon|'none', scale, color_if_no_icon)
        self.components: dict[str, tuple[int, int, str, float, str]] = {
            "Arm Base": (0, 0, "home.png", 0.3, "#3498db"),
            "Coffee Machine": (-185, -275, "coffee_machine.png", 0.45, "#e67e22"),
            "Cup Dispenser S": (10, -185, "cup_S.png", 0.1, "#3e158b"),
            "Cup Dispenser M": (10, -300, "cup_M.png", 0.25, "#5E422B"),
            "Ice Cream Machine": (195, -270, "ice_cream.png", 0.45, "#9b59b6"),
            "Delivery Area": (-200, 275, "money.png", 0.3, "#e74c3c"),
            "Bin": (-50, 275, "bin.png", 0.3, "#e74c3c"),
            "Sugar Syrup": (225, -100, "sugar_syrup.png", 1, "#32b489"),
            "Salted Caramel": (220, 0, "salted_caramel.png", 1, "#32b489"),
            "Blackberry": (210, 100, "blackberry.svg", 1, "#32b489"),
            "Coconut": (210, 200, "coconut.svg", 1, "#32b489")
        }
        self.colors: dict[str, str] = {name: color for name, (_, _, _, _, color) in self.components.items()}
        self.icons: dict[str, QPixmap | None] = self.load_icons()
        self.draw_schematic()
        self.setSceneRect(-300, -200, 600, 400)
        self.setBackgroundBrush(QColor("#9bd1e4"))  # Set background to grey
    
    def load_icons(self) -> Dict[str, Optional[QPixmap]]:
        """Load SVG icons for components that need them"""
        icon_dir = Path(__file__).parent.parent.parent.parent.parent / "resources" / "icons"
        icons = {}
        for name, (_, _, icon, _, _) in self.components.items():
            if icon != "none":
                try:
                    icons[name] = QPixmap(str(icon_dir / icon))
                except FileNotFoundError:
                    print(f"Warning: Icon not found for {name}")
                    icons[name] = None
        return icons
        
    def draw_schematic(self):
        """Draw components with either icons or colored circles"""
        for name, (x, y, icon, scale, color) in self.components.items():
            if icon == "none":
                # Draw colored circle
                radius = 40
                item = QGraphicsEllipseItem(x-radius, y-radius, radius*2, radius*2)
                item.setBrush(QBrush(QColor(color)))
                item.setPen(QPen(QColor("black"), 2))
            else:
                # Draw icon if available, otherwise fallback to circle
                icon_pixmap = self.icons.get(name)
                if icon_pixmap is not None:
                    pixmap = icon_pixmap.scaledToWidth(
                        int(icon_pixmap.width() * scale),
                        Qt.TransformationMode.SmoothTransformation
                    )
                    item = QGraphicsPixmapItem(pixmap)
                    item.setPos(x - pixmap.width()/2, y - pixmap.height()/2)
                else:
                    # Fallback to colored circle
                    radius = 40
                    item = QGraphicsEllipseItem(x-radius, y-radius, radius*2, radius*2)
                    item.setBrush(QBrush(QColor(color)))
                    item.setPen(QPen(QColor('black'), 2))

            item.setData(0, name)
            item.setCursor(Qt.CursorShape.PointingHandCursor)
            self._scene.addItem(item)
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        items: list[QGraphicsItem] = self.items(event.pos())
        for item in items:
            if isinstance(item, (QGraphicsEllipseItem, QGraphicsPixmapItem)):
                self.component_clicked.emit(item.data(0))
                break
        super().mousePressEvent(event)

class Node(QGraphicsEllipseItem):
    def __init__(self, name, x, y, size, color, arm_coords, icon=None, icon_scale=1.0):
        super().__init__(-size/2, -size/2, size, size)
        self.signals = NodeSignals()
        self.name = name
        self.arm_coords = arm_coords

        self.setPos(x, y)
        self.setBrush(QBrush(QColor(color)))
        self.setPen(QPen(QColor("black"), 2))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)

        # Add icon if available
        if icon:
            pixmap = icon.scaledToWidth(int(icon.width() * icon_scale), Qt.TransformationMode.SmoothTransformation)
            self.pixmap_item = QGraphicsPixmapItem(pixmap, self)
            self.pixmap_item.setOffset(-pixmap.width()/2, -pixmap.height()/2)
            self.setBrush(Qt.BrushStyle.NoBrush)  # Remove ellipse fill if icon is present
        else:
            self.pixmap_item = None

        # Add name label
        self.label = QGraphicsSimpleTextItem(name, self)
        self.label.setPos(-self.label.boundingRect().width()/2, size/2 + 10)
        self.label.setBrush(QBrush(QColor("white")))

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        self.signals.moved.emit()


class Edge(QGraphicsPathItem):
    def __init__(self, source, dest):
        super().__init__()
        self.source = source
        self.dest = dest
        
        # Connect to node signals
        self.source.signals.moved.connect(self.update_path)
        self.dest.signals.moved.connect(self.update_path)
        
        self.setPen(QPen(QColor("#34495e"), 2, Qt.PenStyle.DashLine))
        self.update_path()
    
    def update_path(self):
        path = QPainterPath()
        path.moveTo(self.source.pos())
        path.lineTo(self.dest.pos())
        self.setPath(path)
class NodeEditor(QGraphicsView):
    NODE_SIZE = 80  # Fixed size for all nodes
    
    def __init__(self, arm_controller, components, colors) -> None:
        super().__init__()
        self.arm = arm_controller
        self._scene = QGraphicsScene()
        self.setScene(self._scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.nodes = {}
        self.edges = []

        # Create fixed nodes from components
        for name, (x, y, _, _, _) in components.items():  # Ignore icon and scale from components
            self.add_node(
                name=name,
                x=x,
                y=y,
                color=colors[name],
                arm_coords=self.arm.get_position()
            )
        
        self.setSceneRect(-300, -200, 600, 400)

    def add_node(self, name, x, y, color, arm_coords) -> None:
        # Create either icon or circle with fixed size
        radius = self.NODE_SIZE / 2
        
        # Check if we have an icon for this component
        icon_path = Path(__file__).parent.parent.parent.parent.parent / "resources" / "icons" / f"{name.replace(' ', '-')}.png"
        print(icon_path)
        if icon_path.exists():
            pixmap = QPixmap(str(icon_path)).scaled(
                self.NODE_SIZE, self.NODE_SIZE, 
                Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            item = QGraphicsPixmapItem(pixmap)
            item.setPos(x - pixmap.width()/2, y - pixmap.height()/2)
        else:
            item = QGraphicsEllipseItem(-radius, -radius, self.NODE_SIZE, self.NODE_SIZE)
            item.setBrush(QBrush(QColor(color)))
            item.setPen(QPen(QColor('black'), 2))

        node = Node(
            name=name,
            x=x,
            y=y,
            size=self.NODE_SIZE,
            color=color,
            arm_coords=arm_coords,
        )
        self.nodes[name] = node
        self._scene.addItem(node)

        # Connect to previous node
        node_names = list(self.nodes.keys())
        if len(node_names) > 1:
            prev_name = node_names[-2]
            edge = Edge(self.nodes[prev_name], node)
            self._scene.addItem(edge)
            self.edges.append(edge)

        self.save_nodes()

    def load_nodes(self):
        config_path = Path("config/calibration/nodes.json")
        if not config_path.exists():
            return
            
        with open(config_path, "r") as f:
            data = json.load(f)
            for node in data["nodes"]:
                self.add_node(
                    name=node["id"],
                    x=node["x"],
                    y=node["y"],
                    color=self.arm.get_position(),  # You may want to replace this with the correct color
                    arm_coords=node["arm_coords"]
                )
    
    def save_nodes(self):
        config_path = Path("config/calibration/nodes.json")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        nodes_data = [{
            "id": node_id,
            "x": node.scenePos().x(),
            "y": node.scenePos().y(),
            "arm_coords": node.arm_coords
        } for node_id, node in self.nodes.items()]
        
        with open(config_path, "w") as f:
            json.dump({"nodes": nodes_data}, f, indent=2)
    
    def contextMenuEvent(self, event):
        menu = QMenu()
        add_action = menu.addAction("Add Node")
        add_action.triggered.connect(
            lambda: self.add_node(
                name=f"node_{len(self.nodes)+1}",
                x=event.pos().x(),
                y=event.pos().y(),
                color="#3498db",  # Default color or choose appropriately
                arm_coords=self.arm.get_position()
            )
        )
        menu.exec(event.globalPos())

class CalibrationWindow(QWidget):
    def __init__(self, arm_controller: MockArmController):
        super().__init__()
        self.arm = arm_controller
        self.schematic = SchematicView()
        self.node_editor = NodeEditor(
            self.arm,
            self.schematic.components,
            self.schematic.colors
        )
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout()
        layout.addWidget(self.schematic, 1)
        layout.addWidget(self.node_editor, 1)
        self.setLayout(layout)
        self.schematic.component_clicked.connect(self.handle_component_click)
    
    def handle_component_click(self, component):
        positions = {
            "Arm Base": {"x": 0, "y": 0, "z": 0, "pitch": 0, "roll": 0, "yaw": 0},
            "Coffee Machine": {"x": 300, "y": -100, "z": 150, "pitch": -15, "roll": 0},
            "Cup Dispenser": {"x": -250, "y": 50, "z": 100, "pitch": 10, "roll": 20},
            "Ice Cream Machine": {"x": 200, "y": 180, "z": 120, "pitch": -5, "roll": -10},
            "Delivery Area": {"x": 0, "y": 250, "z": 80, "pitch": 0, "roll": 0}
        }
        
        if component in positions:
            # Move arm to component position
            self.arm.move_to(**positions[component])
            
            # Get component visual parameters
            # size = self.schematic.components[component][2]  # Radius from schematic
            # color = self.schematic.colors[component]
            # arm_coords = positions[component]
            
            # Get position in node editor view
            # comp_x, comp_y, _, _, _ = self.schematic.components[component]
            # scene_point = self.schematic.mapToScene(comp_x, comp_y)
            # view_point = self.node_editor.mapFromScene(scene_point)
            
            # Add node with all required parameters
            # self.node_editor.add_node(
            #     name=component,
            #     x=view_point.x(),
            #     y=view_point.y(),
            #     size=size,
            #     color=color,
            #     arm_coords=arm_coords
            # )

class NodeSignals(QObject):
    moved = Signal()
    
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    
    app = QApplication([])
    window = CalibrationWindow(MockArmController())
    window.resize(1200, 800)
    window.show()
    app.exec()