# src/mini_coffee/gui/operator/calibration.py
import json
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsPixmapItem,
    QGraphicsEllipseItem, QGraphicsSimpleTextItem, QGraphicsPathItem, QMenu, QTabWidget
)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QPainterPath, QPixmap, QMouseEvent
)
from mini_coffee.hardware.arm.controller import MockArmController
from typing import Dict, Optional

class Data:
    def __init__(self, path="/home/dev/projects/mini_coffee/src/mini_coffee/gui/operator/config/calibration/components.json"):
        self.path = Path(path)
        self.components = self.load_components()

    def save_components(self, components: dict) -> None:
        """Save components dict to a JSON file."""
        serializable = {k: list(v) for k, v in components.items()}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(serializable, f, indent=2)
        self.components = components

    def load_components(self) -> dict:
        """Load components dict from a JSON file."""
        if not self.path.exists():
            return {}
        try:
            with open(self.path, "r") as f:
                data = json.load(f)
                return {k: v for k, v in data.items()}
        except (json.JSONDecodeError, OSError):
            return {}

    def edit_component(self, name: str, new_value: list) -> None:
        """Edit a component and save changes."""
        self.components[name] = new_value
        self.save_components(self.components)

    def remove_component(self, name: str) -> None:
        """Remove a component and save changes."""
        if name in self.components:
            del self.components[name]
            self.save_components(self.components)
        
        
class SchematicView(QGraphicsView):
    component_clicked = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.data = Data()
        self._scene = QGraphicsScene()
        self.setScene(self._scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Component format: (x, y, icon|'none', scale, color_if_no_icon)
        self.components: dict[str, list] = self.data.load_components()
        self.colors: dict[str, str] = {name: color for name, (_, _, _, _, color) in self.components.items()}
        self.icons: dict[str, QPixmap | None] = self.load_icons()
        self.draw_schematic()
        self.setSceneRect(-300, -200, 600, 400)
        self.setBackgroundBrush(QColor("#9bd1e4"))  # Set background to grey
    
    def load_icons(self) -> Dict[str, Optional[QPixmap]]:
        """Load SVG icons for components that need them"""
        icon_dir = Path(__file__).parent.parent.parent.parent.parent / "resources" / "icons"
        icons = {}
        # Use self.data.components to ensure icons match loaded data
        for name, (_, _, icon, _, _) in self.data.components.items():
            if icon != "none":
                icon_path = icon_dir / icon
                if icon_path.exists():
                    icons[name] = QPixmap(str(icon_path))
                else:
                    print(f"Warning: Icon not found for {name} at {icon_path}")
                    icons[name] = None
            else:
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
        items: list[QGraphicsItem] = self.items(event.position().toPoint())
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
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)

        # Add icon if available
        if icon:
            # Scale icon to fit node size while maintaining aspect ratio
            scaled_pixmap = icon.scaled(
                size, size, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            self.pixmap_item = QGraphicsPixmapItem(scaled_pixmap, self)
            self.pixmap_item.setOffset(-scaled_pixmap.width()/2, -scaled_pixmap.height()/2)
            self.setBrush(Qt.BrushStyle.NoBrush)
            self.setPen(QPen(Qt.PenStyle.NoPen))  # Remove ellipse outline
        else:
            # Fallback to colored circle
            self.setBrush(QBrush(QColor(color)))
            self.setPen(QPen(QColor("black"), 2))
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
        
        self.setPen(QPen(QColor("#8e9ca7"), 2, Qt.PenStyle.DashLine))
        self.setZValue(-1)  # Ensure edges are drawn below nodes
        self.update_path()
    
    def update_path(self):
        path = QPainterPath()
        path.moveTo(self.source.pos())
        path.lineTo(self.dest.pos())
        self.setPath(path)
        
class NodeEditor(QGraphicsView):
    NODE_SIZE = 80  # Fixed size for all nodes

    def __init__(self, arm_controller, components, colors, connections=None, icons=None) -> None:
        super().__init__()
        self.arm = arm_controller
        self.data = Data()
        self._scene = QGraphicsScene()
        self.setScene(self._scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.nodes = {}
        self.edges = []
        self.connections = connections or []
        self.icons = self.load_icons() if icons is None else icons

        for name, (x, y, _, scale, _) in components.items():
            self.add_node(
                name=name,
                x=x,
                y=y,
                color=colors[name],
                arm_coords=self.arm.get_position(),
                icon=self.icons.get(name),
                icon_scale=scale
            )

        # Draw edges after all nodes are added
        self.create_edges_from_connections()

        self.setSceneRect(-300, -200, 600, 400)

    def load_icons(self) -> Dict[str, Optional[QPixmap]]:
        """Load SVG icons for components that need them"""
        icon_dir = Path(__file__).parent.parent.parent.parent.parent / "resources" / "icons"
        icons = {}
        # Use self.data.components to ensure icons match loaded data
        for name, (_, _, icon, _, _) in self.data.components.items():
            if icon != "none":
                icon_path = icon_dir / icon
                if icon_path.exists():
                    icons[name] = QPixmap(str(icon_path))
                else:
                    print(f"Warning: Icon not found for {name} at {icon_path}")
                    icons[name] = None
            else:
                icons[name] = None
        return icons

    def add_node(self, name, x, y, color, arm_coords, icon=None, icon_scale=1.0) -> None:
        node = Node(
            name=name,
            x=x,
            y=y,
            size=self.NODE_SIZE,
            color=color,
            arm_coords=arm_coords,
            icon=icon,
            icon_scale=icon_scale
        )
        self.nodes[name] = node
        self._scene.addItem(node)
        # Redraw edges to ensure connections are visible when nodes are added dynamically
        self.create_edges_from_connections()

    def create_edges_from_connections(self):
        # Remove existing edges
        for edge in self.edges:
            self._scene.removeItem(edge)
        self.edges.clear()
        # Add edges based on self.connections
        for src, dst in self.connections:
            if src in self.nodes and dst in self.nodes:
                edge = Edge(self.nodes[src], self.nodes[dst])
                self.edges.append(edge)
                self._scene.addItem(edge)
                

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
                    color="#3498db",  # You may want to replace this with the correct color
                    arm_coords=node["arm_coords"],
                    icon=None,
                    icon_scale=1.0
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
                color="#3498db",
                arm_coords=self.arm.get_position(),
                icon=None,
                icon_scale=1.0
            )
        )
        menu.exec(event.globalPos())

class CalibrationWindow(QWidget):
    def __init__(self, arm_controller: MockArmController):
        super().__init__()
        self.arm = arm_controller
        self.schematic = SchematicView()
        
        # Define node sets for each tab
        all_nodes = list(self.schematic.components.keys())
        coffee_nodes = ["Arm Base", "Cup Dispenser M", "Cup Dispenser S", "Coffee Machine", "Delivery Area", "Bin"]
        ice_cream_nodes = [
            "Arm Base", "Cup Dispenser M", "Cup Dispenser S", "Ice Cream Machine",
            "Sugar Syrup", "Salted Caramel", "Coconut", "Blackberry", "Delivery Area", "Bin"
        ]
        bin_nodes = ["Arm Base", "Delivery Area", "Bin"]

        # Define connections for each tab
        all_connections = [
        ("Arm Base", "Cup Dispenser M"),
        ("Arm Base", "Cup Dispenser S"),
        ("Cup Dispenser M", "Coffee Machine"),
        ("Cup Dispenser S", "Coffee Machine"),
        ("Cup Dispenser M", "Ice Cream Machine"),
        ("Cup Dispenser S", "Ice Cream Machine"),
        ("Ice Cream Machine", "Delivery Area"),
        ("Coffee Machine", "Delivery Area"),
        ("Delivery Area", "Arm Base"),
        ("Ice Cream Machine", "Sugar Syrup"),
        ("Ice Cream Machine", "Salted Caramel"),
        ("Ice Cream Machine", "Blackberry"),
        ("Ice Cream Machine", "Coconut"),
        ("Sugar Syrup", "Delivery Area"),
        ("Salted Caramel", "Delivery Area"),
        ("Blackberry", "Delivery Area"),
        ("Coconut", "Delivery Area"),
        ("Sugar Syrup", "Salted Caramel"),
        ("Sugar Syrup", "Blackberry"),
        ("Sugar Syrup", "Coconut"),
        ("Salted Caramel", "Blackberry"),
        ("Salted Caramel", "Coconut"),
        ("Blackberry", "Coconut"),
        ("Delivery Area", "Bin"),
        ]
        coffee_connections = [
            ("Arm Base", "Cup Dispenser M"),
            ("Arm Base", "Cup Dispenser S"),
            ("Cup Dispenser M", "Coffee Machine"),
            ("Cup Dispenser S", "Coffee Machine"),
            ("Coffee Machine", "Delivery Area"),
            ("Delivery Area", "Bin"),
        ]
        ice_cream_connections = [
            ("Arm Base", "Cup Dispenser M"),
            ("Arm Base", "Cup Dispenser S"),
            ("Cup Dispenser M", "Ice Cream Machine"),
            ("Cup Dispenser S", "Ice Cream Machine"),
            ("Ice Cream Machine", "Sugar Syrup"),
            ("Ice Cream Machine", "Salted Caramel"),
            ("Ice Cream Machine", "Blackberry"),
            ("Ice Cream Machine", "Coconut"),
            ("Sugar Syrup", "Delivery Area"),
            ("Salted Caramel", "Delivery Area"),
            ("Blackberry", "Delivery Area"),
            ("Coconut", "Delivery Area"),
            ("Delivery Area", "Bin"),
        ]
        bin_connections = [
            ("Arm Base", "Delivery Area"),
            ("Delivery Area", "Bin"),
        ]
        # Helper to filter components/colors/icons for each tab
        def filter_dict(d, keys):
            return {k: v for k, v in d.items() if k in keys}
        
        # Create NodeEditors for each tab
        self.node_editors = [
            NodeEditor(self.arm,
                       filter_dict(self.schematic.components, all_nodes),
                       filter_dict(self.schematic.colors, all_nodes),
                       connections=all_connections,
                       icons=filter_dict(self.schematic.icons, all_nodes)),
            NodeEditor(self.arm,
                       filter_dict(self.schematic.components, coffee_nodes),
                       filter_dict(self.schematic.colors, coffee_nodes),
                       connections=coffee_connections,
                       icons=filter_dict(self.schematic.icons, coffee_nodes)),
            NodeEditor(self.arm,
                       filter_dict(self.schematic.components, ice_cream_nodes),
                       filter_dict(self.schematic.colors, ice_cream_nodes),
                       connections=ice_cream_connections,
                       icons=filter_dict(self.schematic.icons, ice_cream_nodes)),
            NodeEditor(self.arm,
                       filter_dict(self.schematic.components, bin_nodes),
                       filter_dict(self.schematic.colors, bin_nodes),
                       connections=bin_connections,
                       icons=filter_dict(self.schematic.icons, bin_nodes)),
        ]
        
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout()
        layout.addWidget(self.schematic, 1)

        tabs = QTabWidget()
        tabs.addTab(self.node_editors[0], "All")
        tabs.addTab(self.node_editors[1], "Coffee")
        tabs.addTab(self.node_editors[2], "Ice Cream")
        tabs.addTab(self.node_editors[3], "Bin")

        layout.addWidget(tabs, 1)
        self.setLayout(layout)
        self.schematic.component_clicked.connect(self.handle_component_click)
    
    def handle_component_click(self, component):
        positions = {
            "Arm Base": {"x": 0, "y": 0, "z": 0, "pitch": 0, "roll": 0, "yaw": 0},
            "Coffee Machine": {"x": 300, "y": -100, "z": 150, "pitch": -15, "roll": 0},
            "Ice Cream Machine": {"x": 200, "y": 180, "z": 120, "pitch": -5, "roll": -10},
            "Delivery Area": {"x": 0, "y": 250, "z": 80, "pitch": 0, "roll": 0},
            "Bin": {"x": -300, "y": 200, "z": 100, "pitch": 0, "roll": 0},
            "Sugar Syrup": {"x": 100, "y": -200, "z": 50, "pitch": 0, "roll": 0},
            "Salted Caramel": {"x": 150, "y": -250, "z": 50, "pitch": 0, "roll": 0},
            "Blackberry": {"x": 200, "y": -300, "z": 50, "pitch": 0, "roll": 0},
            "Coconut": {"x": 250, "y": -350, "z": 50, "pitch": 0, "roll": 0},
            "Cup Dispenser M": {"x": -200, "y": 100, "z": 100, "pitch": 0, "roll": 0},
            "Cup Dispenser S": {"x": -150, "y": 50, "z": 100, "pitch": 0, "roll": 0},
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