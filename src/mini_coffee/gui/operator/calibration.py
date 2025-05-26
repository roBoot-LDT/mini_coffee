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
    FILES = {
        0: "calibration.json",
        1: "components.json",
        2: "nodes.json"
    }

    def __init__(self, mode: int = 1):
        # Default mode is 1 (components.json) for backward compatibility
        self.mode = mode
        self.path = Path(__file__).parent / "config" / "calibration" / self.FILES[self.mode]
        self.data = self.load_data()

    def save_data(self, data: dict) -> None:
        """Save data dict to the selected JSON file."""
        serializable = {k: list(v) if isinstance(v, (list, tuple)) else v for k, v in data.items()}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(serializable, f, indent=2)
        self.data = data

    def load_data(self) -> dict:
        """Load data dict from the selected JSON file."""
        if not self.path.exists():
            return {}
        try:
            with open(self.path, "r") as f:
                data = json.load(f)
                return {k: v for k, v in data.items()}
        except (json.JSONDecodeError, OSError):
            return {}

    def edit_entry(self, name: str, new_value) -> None:
        """Edit an entry and save changes."""
        self.data[name] = new_value
        self.save_data(self.data)

    def remove_entry(self, name: str) -> None:
        """Remove an entry and save changes."""
        if name in self.data:
            del self.data[name]
            self.save_data(self.data)
        
class SchematicView(QGraphicsView):
    component_clicked = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.data = Data(1)  # Load components.json by default
        self._scene = QGraphicsScene()
        self.setScene(self._scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Component format: (x, y, icon|'none', scale, color_if_no_icon)
        self.components: dict[str, list] = self.data.load_data()
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
        for name, (_, _, icon, _, _) in self.components.items():
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

class Node(QGraphicsItem):
    def __init__(self, name, x, y, size, color, arm_coords, icon=None):
        super().__init__()
        self.signals = NodeSignals()
        self.name = name
        self.arm_coords = arm_coords
        self.size = size
        
        # Create child items
        self.background = QGraphicsEllipseItem(-size/2, -size/2, size, size, self)
        self.label = QGraphicsSimpleTextItem(name, self)
        
        if icon:
            self.pixmap = QGraphicsPixmapItem(icon, self)
            self.pixmap.setOffset(-icon.width()/2, -icon.height()/2)
            self.background.hide()
        else:
            self.background.setBrush(QBrush(QColor(color)))
            self.background.setPen(QPen(QColor("black"), 2))

        # Position label
        self.label.setPos(-self.label.boundingRect().width()/2, size/2 + 10)
        self.label.setBrush(QBrush(QColor("white")))
        self.setPos(x, y)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)

    def boundingRect(self):
        return self.childrenBoundingRect()

    def paint(self, painter, option, widget=None):
        pass  # Painting handled by child items

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
    
    def remove(self):
        # Disconnect signals to avoid double-free on shutdown
        try:
            self.source.signals.moved.disconnect(self.update_path)
        except (TypeError, RuntimeError):
            pass
        try:
            self.dest.signals.moved.disconnect(self.update_path)
        except (TypeError, RuntimeError):
            pass
        
class NodeEditor(QGraphicsView):
    NODE_SIZE = 80  # Fixed size for all nodes

    def __init__(self, arm_controller, components, colors, connections=None, icons=None) -> None:
        super().__init__()
        self.arm = arm_controller
        self.data = Data(mode=2)  # Use mode=2 for nodes.json
        self._scene = QGraphicsScene()
        self.setScene(self._scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.nodes = {}
        self.edges = []
        self.connections = connections or []
        self.icons = icons if icons is not None else self.load_icons(components)

        for name, (x, y, _, scale, _) in components.items():
            self.add_node(
                name=name,
                x=x,
                y=y,
                color=colors[name],
                arm_coords=self.arm.get_position(),
                
            )

        # Draw edges after all nodes are added
        self.create_edges_from_connections()

        self.setSceneRect(-300, -200, 600, 400)

    def load_icons(self, components) -> Dict[str, Optional[QPixmap]]:
        """Load SVG icons for components that need them"""
        icon_dir = Path(__file__).parent.parent.parent.parent.parent / "resources" / "icons"
        icons = {}
        for name, (_, _, icon, _, _) in components.items():
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

    def add_node(self, name, x, y, color, arm_coords) -> None:
        icon = None
        if self.icons and name in self.icons:
            icon = self.icons[name]
        if icon is not None:
            icon = icon.scaled(
                self.NODE_SIZE, self.NODE_SIZE,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

        node = Node(
            name=name,
            x=x,
            y=y,
            size=self.NODE_SIZE,
            color=color,
            arm_coords=arm_coords,
            icon=icon
        )
        self.nodes[name] = node
        self._scene.addItem(node)        


    def create_edges_from_connections(self) -> None:
        # Remove existing edges
        for edge in self.edges:
            edge.remove()  # <-- disconnect signals
            self._scene.removeItem(edge)
        self.edges.clear()
        # Add edges based on self.connections
        for src, dst in self.connections:
            if src in self.nodes and dst in self.nodes:
                edge = Edge(self.nodes[src], self.nodes[dst])
                self.edges.append(edge)
                self._scene.addItem(edge)

    def load_nodes(self) -> None:
        # Loads nodes from the Data class (nodes.json)
        data = self.data.load_data()
        for name, node in data.items():
            self.add_node(
                name=name,
                x=node.get("x", 0),
                y=node.get("y", 0),
                color="#3498db",  # You may want to replace this with the correct color
                arm_coords=node.get("arm_coords", {}),
                
            )

    def save_nodes(self) -> None:
        # Saves nodes to the Data class (nodes.json)
        nodes_data = {}
        for node_id, node in self.nodes.items():
            nodes_data[node_id] = {
                "x": node.scenePos().x(),
                "y": node.scenePos().y(),
                "arm_coords": node.arm_coords
            }
        self.data.save_data(nodes_data)

    def contextMenuEvent(self, event) -> None:
        menu = QMenu()
        add_action = menu.addAction("Add Node")
        add_action.triggered.connect(
            lambda: self.add_node(
                name=f"node_{len(self.nodes)+1}",
                x=event.pos().x(),
                y=event.pos().y(),
                color="#3498db",
                arm_coords=self.arm.get_position(),
            )
        )
        menu.exec(event.globalPos())

class CalibrationWindow(QWidget):
    def __init__(self, arm_controller: MockArmController) -> None:
        super().__init__()
        self.arm = arm_controller
        self.schematic = SchematicView()
        self.data = Data(0)  # Load calibration.json by default
        # Define node sets for each tab
        all_nodes = list(self.schematic.components.keys())
        nodes = {
            "All": 0,
            "Coffee": 1,
            "Ice Cream": 2,
            "Bin": 3
        }
        # Load node sets and connections from self.data (calibration.json)
        coffee_nodes = self.data.data["tabs"][nodes["Coffee"]].get("nodes", [])
        ice_cream_nodes = self.data.data["tabs"][nodes["Ice Cream"]].get("nodes", [])
        bin_nodes = self.data.data["tabs"][nodes["Bin"]].get("nodes", [])

        all_connections = self.data.data["tabs"][nodes["All"]].get("connections", [])
        coffee_connections = self.data.data["tabs"][nodes["Coffee"]].get("connections", [])
        ice_cream_connections = self.data.data["tabs"][nodes["Ice Cream"]].get("connections", [])
        bin_connections = self.data.data["tabs"][nodes["Bin"]].get("connections", [])
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
    
    def init_ui(self) -> None:
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
    
    def handle_component_click(self, component) -> None:
        positions = self.data.data.get("positions", {})
        
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