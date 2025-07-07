# src/mini_coffee/gui/operator/calibration.py
import json, time
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsPixmapItem, QGroupBox, QMessageBox, QLineEdit, QFormLayout,
    QGraphicsEllipseItem, QGraphicsSimpleTextItem, QGraphicsPathItem, QMenu, QTabWidget, QDialog, QPushButton, QVBoxLayout, QLabel,
    QComboBox, QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QPainterPath, QPixmap, QMouseEvent, QFont, QRadialGradient
)
from mini_coffee.hardware.arm.controller import MockArmController
from typing import Dict, Optional
from mini_coffee.utils.logger import setup_logger
from mini_coffee.utils.helpers import Pathfinder

logger = setup_logger()

class Data:
    FILES = {
        0: "calibration.json",
        1: "components.json",
        2: "nodes.json",
        3: "receipts.json"
    }

    def __init__(self, mode: int = 1):
        # Default mode is 1 (components.json) for backward compatibility
        self.mode = mode
        self.path = Path(__file__).parent / "config" / "calibration" / self.FILES[self.mode]
        self.data = self.load_data()

        # Load nodes data for all modes
        self.nodes_data = self._load_nodes_data()
    
    def _load_nodes_data(self):
        nodes_path = Path(__file__).parent / "config" / "calibration" / self.FILES[2]
        if not nodes_path.exists():
            return {}
        try:
            with open(nodes_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {} 
    
    def get_node_status(self, node_name):
        return self.nodes_data.get(node_name, {}).get("calibrated", False)
    
    def mark_node_calibrated(self, node_name):
        if node_name in self.nodes_data:
            self.nodes_data[node_name]["calibrated"] = True
            nodes_path = Path(__file__).parent / "config" / "calibration" / self.FILES[2]
            with open(nodes_path, "w") as f:
                json.dump(self.nodes_data, f, indent=2)

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
        """Load SVG icons with _r suffix for uncalibrated nodes"""
        icon_dir = Path(__file__).parent.parent.parent.parent.parent / "resources" / "icons"
        data = Data(2)  # Access node calibration status
        icons = {}
        for name, component_data in self.components.items():
            _, _, base_icon, _, _ = component_data
            
            if base_icon == "none":
                icons[name] = None
                continue
                
            # Get calibration status from nodes.json
            is_calibrated = data.get_node_status(name)
    
            # Use _r suffix only for uncalibrated components
            icon_file = base_icon if is_calibrated else self._get_uncalibrated_icon(base_icon)
            for attempt in [icon_file, base_icon]:
                icon_path = icon_dir / attempt
                if icon_path.exists():
                    icons[name] = QPixmap(str(icon_path))
                    break
            else:
                logger.warning(f"Icon not found for {name}: {icon_file} or {base_icon}")
                icons[name] = None

        return icons
    
    def _get_uncalibrated_icon(self, base_icon):
        """Safely append _r suffix"""
        if not base_icon.endswith('_r'):
            parts = base_icon.rsplit('.', 1)
            return f"{parts[0]}_r.{parts[1]}" if len(parts) > 1 else f"{base_icon}_r"
        return base_icon

    def draw_schematic(self, current_position=None):
        """Draw components with either icons or colored circles"""
        self._scene.clear()
        for name, (x, y, icon, scale, color) in self.components.items():
            highlight = (name == current_position)
            if icon == "none":
                # Draw colored circle
                radius = 40
                item = QGraphicsEllipseItem(x-radius, y-radius, radius*2, radius*2)
                item.setBrush(QBrush(QColor(color)))
                item.setPen(QPen(QColor("black"), 2))
            else:
                icon_pixmap = self.icons.get(name)
                if icon_pixmap is not None:
                    pixmap = icon_pixmap.scaledToWidth(
                        int(icon_pixmap.width() * scale),
                        Qt.TransformationMode.SmoothTransformation
                    )
                    item = QGraphicsPixmapItem(pixmap)
                    item.setPos(x - pixmap.width()/2, y - pixmap.height()/2)
                else:
                    radius = 40
                    item = QGraphicsEllipseItem(x-radius, y-radius, radius*2, radius*2)
                    item.setBrush(QBrush(QColor(color)))
                    item.setPen(QPen(QColor('black'), 2))

            item.setData(0, name)
            item.setCursor(Qt.CursorShape.PointingHandCursor)
            self._scene.addItem(item)

            # Draw highlight if this is the current arm position
            if highlight:
                # Create a modern, elegant highlight marker
                marker_size = 80
                
                # Outer animated ring (pulsing effect)
                ring = QGraphicsEllipseItem(
                    x - marker_size/2, y - marker_size/2, marker_size, marker_size
                )
                ring_pen = QPen(QColor("#FF5722"), 3)  # Vibrant orange
                ring.setPen(ring_pen)
                ring.setBrush(Qt.BrushStyle.NoBrush)
                ring.setZValue(20)
                self._scene.addItem(ring)
                
                # Inner filled circle with gradient
                inner_size = 24
                inner = QGraphicsEllipseItem(
                    x - inner_size/2, y - inner_size/2, inner_size, inner_size
                )
                
                # Create radial gradient for a 3D effect
                gradient = QRadialGradient(x, y, inner_size)
                gradient.setColorAt(0, QColor("#FF5722"))  # Bright center
                gradient.setColorAt(1, QColor("#E64A19"))  # Darker edge
                inner.setBrush(QBrush(gradient))
                
                inner_pen = QPen(QColor("#FFFFFF"), 1.5)  # White border
                inner.setPen(inner_pen)
                inner.setZValue(21)
                self._scene.addItem(inner)
        
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

    def __init__(self, arm_controller, components, colors, connections=None, tab_index=0) -> None:
        super().__init__()
        self.tab_index = tab_index  # Track which calibration.json tab this belongs to
        self.arm = arm_controller
        self.data = Data(mode=2)  # nodes.json
        self._scene = QGraphicsScene()
        self.setScene(self._scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.nodes = {}
        self.edges = []
        self.connections = connections or []
        self.icons = self.load_icons(components)

        for name, (x, y, _, _, _) in components.items():
            self.add_node(
                name=name,
                x=x,
                y=y,
                color=colors[name],
                arm_coords=self.arm.get_position_name(),
                
            )

        # Draw edges after all nodes are added
        self.create_edges_from_connections()
        self.setSceneRect(-300, -200, 600, 400)

    def load_icons(self, components) -> Dict[str, Optional[QPixmap]]:
        """Load icons with '_r' suffix removed from filenames"""
        icon_dir = Path(__file__).parent.parent.parent.parent.parent / "resources" / "icons"
        icons = {}
        
        for name, (_, _, icon, _, _) in components.items():
            if icon == "none":
                icons[name] = None
                continue
                
            # Remove '_r' suffix if present
            clean_name = icon.replace('_r', '')
            icon_path = icon_dir / clean_name
            
            # Fallback to original name if cleaned doesn't exist
            if not icon_path.exists():
                icon_path = icon_dir / icon
                
            if icon_path.exists():
                icons[name] = QPixmap(str(icon_path))
            else:
                logger.warning(f"Icon not found: {clean_name} or {icon}")
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
        add_action.triggered.connect(lambda: self._add_node_with_config(event.pos()))
        menu.exec(event.globalPos())

    def _add_node_with_config(self, pos):
        # Create temporary node
        temp_name = f"node_{len(self.nodes)+1}"
        self.add_node(
            name=temp_name,
            x=pos.x(), y=pos.y(),
            color="#3498db",  # Default color
            arm_coords={}  # Placeholder
        )
        
        # Get existing node names for dropdowns
        existing_nodes = list(self.nodes.keys())
        
        # Show configuration dialog
        dlg = NodeConfigDialog(existing_nodes, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            # Update arm coordinates
            arm_data = {
                "x": float(dlg.x_input.text()),
                "y": float(dlg.y_input.text()),
                "z": float(dlg.z_input.text()),
                "yaw": float(dlg.yaw_input.text()),
                "pitch": float(dlg.pitch_input.text()),
                "roll": float(dlg.roll_input.text())
            }
            
            # Update node data in components.json (mode=1)
            comp_data = [
                self.nodes[temp_name].scenePos().x(),
                self.nodes[temp_name].scenePos().y(),
                "none",  # Default icon
                0.1,    # Default scale
                "#3498db" # Default color
            ]
            Data(mode=1).edit_entry(temp_name, comp_data)
            
            # Save to nodes.json (mode=2)
            Data(mode=2).edit_entry(temp_name, {
                "x": self.nodes[temp_name].scenePos().x(),
                "y": self.nodes[temp_name].scenePos().y(),
                "arm_coords": arm_data
            })
            
            # Add connections to calibration.json (mode=0)
            prev_node = dlg.prev_combo.currentText()
            next_node = dlg.next_combo.currentText()
            calib_data = Data(mode=0).load_data()
            
            if prev_node:
                calib_data["tabs"][self.tab_index]["connections"].append((prev_node, temp_name))
            if next_node:
                calib_data["tabs"][self.tab_index]["connections"].append((temp_name, next_node))
            
            Data(mode=0).save_data(calib_data)
            
            # Redraw edges
            self.create_edges_from_connections()
        else:
            # Remove temporary node if canceled
            self._scene.removeItem(self.nodes[temp_name])
            del self.nodes[temp_name]

class CheckDialog(QDialog):
    def __init__(self, component, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Check {component}")
        self.check_result = None
        self.setStyleSheet(self._get_stylesheet())
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)
        
        question = QLabel(f"⚠️ Confirm component position\nfor '{component}'")
        question.setAlignment(Qt.AlignmentFlag.AlignCenter)
        question.setStyleSheet("font-size: 16px; font-weight: 500;")
        layout.addWidget(question)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        self.edit_btn = QPushButton("✏️ Edit Position")
        self.good_btn = QPushButton("✅ Confirm Position")
        # Make the confirm button round and green
        self.good_btn.setStyleSheet("""
            QPushButton {
            background-color: #4CAF50;
            color: white;
            border-radius: 12px;
            min-width: 48px;
            max-width: 250px;
            max-height: 35px;
            font-size: 18px;
            }
            QPushButton:hover {
            background-color: #45a049;
            }
        """)
        self.edit_btn.setStyleSheet("""
            QPushButton {
            background-color: #4CAF50;
            color: white;
            border-radius: 12px;
            min-width: 48px;
            max-width: 250px;
            max-height: 35px;
            font-size: 18px;
            }
            QPushButton:hover {
            background-color: #45a049;
            }
        """)
        
        self.good_btn.clicked.connect(self.good)
        self.edit_btn.clicked.connect(self.edit)
        
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.good_btn)
        layout.addLayout(btn_layout)
        
        self.setMinimumWidth(400)

    def good(self):
        self.check_result = "good"
        self.accept()

    def edit(self):
        self.check_result = "edit"
        self.accept()

    def _get_stylesheet(self):
        return """
            QDialog {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border-radius: 8px;
            }
            QPushButton {
                padding: 10px 15px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                min-width: 120px;
            }
            QPushButton:hover {
                opacity: 0.9;
            }
            QPushButton#edit_btn {
                background-color: #3498db;
                color: white;
            }
            QPushButton#good_btn {
                background-color: #4CAF50;
                color: white;
            }
        """
        
class CalibrationControls(QWidget):
    calibration_done = Signal(str)  # emits the node/component name
    def __init__(self, arm, component, parent=None):
        super().__init__(parent)
        self.data = Data(2)  # Load nodes.json 
        self.arm = arm
        self.component = component
        self.parent_widget = parent
        self.step_size = 1
        self.setStyleSheet(self._get_stylesheet())
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(20)
        
        header = QLabel(f"🔧 Calibrating: {component}")
        header.setStyleSheet("font-size: 18px; font-weight: 600; color: #88c0d0;")
        layout.addWidget(header)
        
        # Current coordinates display
        self.coords_label = QLabel()
        self.coords_label.setStyleSheet("""
            background-color: #3b4252;
            border-radius: 6px;
            padding: 10px;
            font-family: 'Consolas', monospace;
        """)
        self.update_coordinates_display()
        layout.addWidget(self.coords_label)
        
        # Step size controls
        step_group = QGroupBox("Step Size Adjustment")
        step_group.setStyleSheet("QGroupBox { font-size: 14px; }")
        step_layout = QVBoxLayout(step_group)
        step_controls = self._create_step_controls()
        step_layout.addWidget(step_controls)
        layout.addWidget(step_group)
        
        # Movement controls
        movement_group = QGroupBox("Axis Controls")
        movement_group.setStyleSheet("QGroupBox { font-size: 14px; }")
        movement_layout = QVBoxLayout(movement_group)
        movement_layout.setSpacing(12)
        
        axes = ["x", "y", "z", "yaw", "pitch", "roll"]
        for axis in axes:
            axis_control = self._create_axis_control(axis)
            movement_layout.addWidget(axis_control)
        
        layout.addWidget(movement_group)
        
        # Save button
        self.save_btn = QPushButton("💾 Save Calibration")
        self.save_btn.clicked.connect(self.save)
        layout.addWidget(self.save_btn)

    def _create_step_controls(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        btn_minus = QPushButton("-")
        btn_plus = QPushButton("+")
        self.step_label = QLabel("1")
        
        # Styling to match axis controls
        for btn in [btn_minus, btn_plus]:
            btn.setFixedSize(40, 30)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3b4252;
                    color: #e0e0e0;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #434c5e;
                }
                QPushButton:disabled {
                    background-color: #2d2d2d;
                    color: #6b6b6b;
                }
            """)
        
        self.step_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.step_label.setStyleSheet("""
            font-weight: 500; 
            min-width: 60px;
            color: #88c0d0;
            font-size: 16px;
        """)
        
        # Connections
        btn_minus.clicked.connect(self._decrease_step)
        btn_plus.clicked.connect(self._increase_step)
        
        layout.addWidget(btn_minus)
        layout.addWidget(self.step_label)
        layout.addWidget(btn_plus)
        
        return widget
    
    def _increase_step(self):
        new_step = min(100, int(self.step_label.text()) + 1)
        self.step_label.setText(str(new_step))
        self.step_size = new_step

    def _decrease_step(self):
        new_step = max(1, int(self.step_label.text()) - 1)
        self.step_label.setText(str(new_step))
        self.step_size = new_step
        
    def move_axis(self, axis, direction):
        """Move specified axis by current step size"""
        try:
            # Calculate movement amount
            amount = direction * self.step_size
            getattr(self.arm, f"move_{axis}")(amount)
            logger.info(f"Moved {axis} by {amount}")
            
            # Update coordinates display
            self.update_coordinates_display()
            
        except Exception as e:
            logger.error(f"Movement error: {str(e)}")

    def save(self):
        # Save calibration, update icon, and return to node editor
        self.parent_widget.update_icon(self.component) # type: ignore
        self.parent_widget.layout().removeWidget(self) # type: ignore
        self.deleteLater()
        self.parent_widget.calib_widget = None  # type: ignore
        self.parent_widget.layout().itemAt(1).widget().show()  # type: ignore # Show node editor tabs
        self.calibration_done.emit(self.component)  # Notify parent
    
    def _create_axis_control(self, axis):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        btn_minus = QPushButton("-")
        btn_plus = QPushButton("+")
        label = QLabel(axis.upper())
        
        # Styling
        for btn in [btn_minus, btn_plus]:
            btn.setFixedSize(40, 30)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3b4252;
                    color: #e0e0e0;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #434c5e;
                }
            """)
            
        label.setStyleSheet("font-weight: 500; min-width: 40px;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Connections
        btn_minus.clicked.connect(lambda _, a=axis: self.move_axis(a, -1))
        btn_plus.clicked.connect(lambda _, a=axis: self.move_axis(a, 1))
        
        layout.addWidget(btn_minus)
        layout.addWidget(label)
        layout.addWidget(btn_plus)
        
        return widget
    
    def update_coordinates_display(self):
        """Update displayed coordinates with current arm position"""
        pos = self.arm.get_position_name()
        pos_data = self.data.data.get("positions", {}).get(pos, {})
        coords = [
            f"🏗️  X: {pos_data.get('x', 0):.2f} mm",
            f"🏗️  Y: {pos_data.get('y', 0):.2f} mm",
            f"🏗️  Z: {pos_data.get('z', 0):.2f} mm",
            f"🎚️  Yaw: {pos_data.get('yaw', 0):.2f}°",
            f"🎚️  Pitch: {pos_data.get('pitch', 0):.2f}°",
            f"🎚️  Roll: {pos_data.get('roll', 0):.2f}°"
        ]
        self.coords_label.setText("\n".join(coords))
        
    def _update_step_size(self, size):
        self.step_size = int(size)

    def _get_stylesheet(self):
        return """
            QWidget {
                background-color: #2d2d2d;
                color: #e0e0e0;
            }
            QGroupBox {
                border: 1px solid #3c3c3c;
                border-radius: 6px;
                padding: 15px 10px;
                margin-top: 10px;
            }
            QGroupBox::title {
                color: #88c0d0;
                subcontrol-origin: margin;
                left: 10px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 12px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """         

class CalibrationWindow(QWidget):
    def __init__(self, arm_controller: MockArmController) -> None:
        super().__init__()
        self.arm = arm_controller
        self.schematic = SchematicView()
        self.data = Data(0)  # Load calibration.json by default
        
        # Path finding logic
        self.current_tab = "All"
        self.pathfinder = None
        self.update_pathfinder()
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
                       connections=all_connections, tab_index=0),
            NodeEditor(self.arm,
                       filter_dict(self.schematic.components, coffee_nodes),
                       filter_dict(self.schematic.colors, coffee_nodes),
                       connections=coffee_connections, tab_index=1),
            NodeEditor(self.arm,
                       filter_dict(self.schematic.components, ice_cream_nodes),
                       filter_dict(self.schematic.colors, ice_cream_nodes),
                       connections=ice_cream_connections, tab_index=2),
            NodeEditor(self.arm,
                       filter_dict(self.schematic.components, bin_nodes),
                       filter_dict(self.schematic.colors, bin_nodes),
                       connections=bin_connections, tab_index=3),
        ]
        self.schematic.draw_schematic(self.arm.get_position_name())
        self.init_ui()
        
    
    
    def init_ui(self) -> None:
        layout = QHBoxLayout()
        layout.addWidget(self.schematic, 1)

        tabs = QTabWidget()
        tabs.addTab(self.node_editors[0], "All")
        tabs.addTab(self.node_editors[1], "Coffee")
        tabs.addTab(self.node_editors[2], "Ice Cream")
        tabs.addTab(self.node_editors[3], "Bin")

        # Add client mode button
        client_btn = QPushButton("Switch to Client Mode")
        client_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 15px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                margin: 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        client_btn.clicked.connect(self.show_client_screen)
        
        control_layout = QVBoxLayout()
        control_layout.addWidget(tabs)
        control_layout.addWidget(client_btn)
        
        layout.addLayout(control_layout, 1)
        self.setLayout(layout)
        self.schematic.component_clicked.connect(self.handle_component_click)
    
    def show_client_screen(self):
        """Switch to full-screen client view"""
        from mini_coffee.gui.client.client_screen import ClientScreen
        from src.mini_coffee.hardware.arm.xarm.wrapper import XArmAPI
        from mini_coffee.hardware.relays import PLC
        from mini_coffee.hardware.arm.controller import RobotMain
        self.arm = XArmAPI('192.168.1.191', baud_checkset=False)
        self.robot = RobotMain(self.arm)
        self.plc = PLC()
        self.client_screen = ClientScreen(self.robot, self.plc)
        self.client_screen.showFullScreen()
        self.hide()
    
    def enter_calibration_mode(self, component):
        layout = self.layout()
        if layout is None:
            return
        # Safely remove and delete previous calibration widget if it exists and is valid
        if hasattr(self, 'calib_widget') and self.calib_widget is not None:
            try:
                layout.removeWidget(self.calib_widget)
                self.calib_widget.deleteLater()
            except RuntimeError:
                pass 
            self.calib_widget = None
        self.calib_widget = CalibrationControls(self.arm, component, self)
        self.calib_widget.calibration_done.connect(self.on_calibration_done)
        # Hide node editor tabs if present
        item = layout.itemAt(1)
        if item is not None and item.widget() is not None:
            item.widget().hide()
        layout.addWidget(self.calib_widget)
        self._pending_calibration_node = component  # Track which node is being calibrated
    
    def on_calibration_done(self, node):
        # Mark node as calibrated after editing
        data = Data(2)
        data.mark_node_calibrated(node)
        # After calibration, verify and continue
        self._verify_calibration_completion(node)
        # If you are in a movement path, resume it
        if hasattr(self, "_current_path") and self._current_path:
            self.execute_movement_path(self._current_path)
            
    def update_icon(self, component):
        # Remove '_r' from icon name and reload
        icon_name = self.schematic.components[component][2]
        new_icon = icon_name 

        # Update component data
        comp = list(self.schematic.components[component])
        comp[2] = new_icon
        self.schematic.components[component] = comp
        self.schematic.icons[component] = QPixmap(str(
            Path(__file__).parent.parent.parent.parent.parent / "resources" / "icons" / new_icon
        ))
        self.schematic._scene.clear()
        self.schematic.draw_schematic(self.arm.get_position_name())
    
    def update_pathfinder(self):
        current_tab_data = next(t for t in self.data.data["tabs"] if t["name"] == self.current_tab)
        self.pathfinder = Pathfinder(current_tab_data["connections"])

    def handle_component_click(self, component) -> None:
        current_position = self.arm.get_position_name() 
        positions = self.data.data.get("positions", {})
        target = component
        
        if component in positions:
            path = self.pathfinder.find_path(current_position, target) #type: ignore
            if not path:
                QMessageBox.warning(self, "No Path", f"No valid path from {current_position} to {target}")
                return      
            self.execute_movement_path(path)
          
    def execute_movement_path(self, path):
        """Move through path with calibration checks"""
        self._current_path = path.copy()
        while self._current_path:
            node = self._current_path.pop(0)
            # Skip first node (current position)
            if node == self.arm.get_position_name():
                continue

            if not self._handle_node_calibration(node):
                self._pending_node = node
                return

            # Move to next node
            if node in self.data.data["positions"]:
                position = self.data.data["positions"][node]
                logger.info(f"Moving to {node} at {position}")
                self.arm.move_to(**position)
                time.sleep(0.5)
                # Update arm position name after each move
                self.arm.set_position_name(node)
                self.schematic.draw_schematic(self.arm.get_position_name())
            else:
                logger.error(f"Position data missing for {node}")
    
       
    def _handle_node_calibration(self, node):
        """Check and calibrate node if needed"""
        data = Data(2)
        if data.get_node_status(node):
            return True
            
        # Node needs calibration
        dlg = CheckDialog(node, self)
        result = dlg.exec()
                                
        if result == QDialog.DialogCode.Accepted:
            if dlg.check_result == "good":
                data.mark_node_calibrated(node)
                self.schematic._scene.clear()
                self.update_icon(node)
                self.schematic.draw_schematic(self.arm.get_position_name())
                return True
            elif dlg.check_result == "edit":
                self.enter_calibration_mode(node)
                return False # Wait for calibration completion
        return False
    
    def _verify_calibration_completion(self, node):
        """Check if node was calibrated after editing"""
        data = Data(mode=2)  # Load nodes.json
        if data.get_node_status(node):
            # Reload icons and redraw schematic
            self.schematic.icons = self.schematic.load_icons()
            self.schematic._scene.clear()
            self.schematic.draw_schematic(self.arm.get_position_name())
            return True
            
        QMessageBox.warning(self, "Calibration Required", 
            f"{node} must be calibrated before proceeding!")
        return False
                
class NodeSignals(QObject):
    moved = Signal()


class NodeConfigDialog(QDialog):
    def __init__(self, existing_nodes, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Node")
        layout = QVBoxLayout(self)
        
        # Arm Coordinates Input
        self.x_input = QLineEdit()
        self.y_input = QLineEdit()
        self.z_input = QLineEdit()
        self.yaw_input = QLineEdit()
        self.pitch_input = QLineEdit()
        self.roll_input = QLineEdit()
        
        coords_layout = QFormLayout()
        coords_layout.addRow("X (mm):", self.x_input)
        coords_layout.addRow("Y (mm):", self.y_input)
        coords_layout.addRow("Z (mm):", self.z_input)
        coords_layout.addRow("Yaw (°):", self.yaw_input)
        coords_layout.addRow("Pitch (°):", self.pitch_input)
        coords_layout.addRow("Roll (°):", self.roll_input)
        layout.addLayout(coords_layout)
        
        # Previous/Next Node Selection
        self.prev_combo = QComboBox()
        self.next_combo = QComboBox()
        self.prev_combo.addItems([""] + existing_nodes)
        self.next_combo.addItems([""] + existing_nodes)
        
        conn_layout = QFormLayout()
        conn_layout.addRow("Previous Node:", self.prev_combo)
        conn_layout.addRow("Next Node:", self.next_combo)
        layout.addLayout(conn_layout)
        
        # Buttons
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)
        
        
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    
    app = QApplication([])
    window = CalibrationWindow(MockArmController())
    window.resize(1200, 800)
    window.show()
    app.exec()