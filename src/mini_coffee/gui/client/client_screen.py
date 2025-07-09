# src/mini_coffee/gui/client/client_screen.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGraphicsOpacityEffect, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QIcon, QFont
from pathlib import Path
import json
import time
from mini_coffee.utils.logger import setup_logger
from mini_coffee.gui.operator.calibration import Data
from mini_coffee.hardware.arm.controller import XArmAPI
from mini_coffee.hardware.relays import PLC

logger = setup_logger()

class ClientScreen(QWidget):
    order_started = Signal(str)
    order_completed = Signal(str)
    arm_status_changed = Signal(str)
    
    def __init__(self, arm_controller: XArmAPI, plc: PLC, parent=None):
        super().__init__(parent)
        self.arm = arm_controller
        self.plc = plc
        self.current_order = None
        self.order_path = []
        self.setStyleSheet(self._get_stylesheet())
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.init_ui()
        
    def load_recipes(self, flavor):
        """Load ice cream recipes from Data(3)"""
        data = Data(3)
        try:
            recipes = data.recipes if hasattr(data, "recipes") else data.load_data()
            if not recipes:
                raise ValueError("No recipes found in Data(3)")
            return recipes[flavor] if flavor in recipes else {}
        except Exception as e:
            logger.error(f"Failed to load recipes from Data(3): {e}. Using defaults.")
            
    
    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        # Title label at the top
        title_label = QLabel("🍦 Mini Coffee Ice Cream Robot 🍦")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 56px;
            font-weight: bold;
            color: #FFD166;
            letter-spacing: 2px;
            margin-bottom: 30px;
            text-shadow: 2px 2px 8px #00000088;
        """)
        main_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        # Spacer to push icons to vertical center
        main_layout.addStretch(1)

        # Ice cream options centered
        options_layout = QHBoxLayout()
        options_layout.setSpacing(100)
        options_layout.setContentsMargins(50, 0, 50, 0)

        # Load icons
        icon_dir = Path(__file__).parent.parent.parent.parent.parent / "resources" / "icons"

        # Track order state to disable buttons during processing
        self.current_order = None        

        # Vanilla
        vanilla_icon = str(icon_dir / "l_ice.png")
        vanilla_btn = self.create_icon_button(vanilla_icon, "Vanilla")
        vanilla_label = self.create_flavor_label("Vanilla")
        self.vanilla_btn = vanilla_btn
        self.vanilla_btn.clicked.connect(lambda: self.start_order("vanilla"))
        vanilla_widget = self.create_icon_with_label_widget(vanilla_btn, vanilla_label)
        options_layout.addWidget(vanilla_widget)

        # Mix
        mix_icon = str(icon_dir / "m_ice.png")
        mix_btn = self.create_icon_button(mix_icon, "Chocolate & Vanilla")
        mix_label = self.create_flavor_label("Chocolate & Vanilla")
        self.mix_btn = mix_btn
        self.mix_btn.clicked.connect(lambda: self.start_order("mix"))
        mix_widget = self.create_icon_with_label_widget(mix_btn, mix_label)
        options_layout.addWidget(mix_widget)

        # Chocolate
        chocolate_icon = str(icon_dir / "r_ice.png")
        chocolate_btn = self.create_icon_button(chocolate_icon, "Chocolate")
        chocolate_label = self.create_flavor_label("Chocolate")
        self.chocolate_btn = chocolate_btn
        self.chocolate_btn.clicked.connect(lambda: self.start_order("chocolate"))
        chocolate_widget = self.create_icon_with_label_widget(chocolate_btn, chocolate_label)
        options_layout.addWidget(chocolate_widget)

        # Add the options layout centered horizontally
        main_layout.addLayout(options_layout, stretch=0)

        # Spacer to keep icons vertically centered
        main_layout.addStretch(2)

    def create_icon_button(self, icon_path, tooltip):
        """Create a clickable icon button with animation and shadow"""
        btn = QPushButton()
        btn.setToolTip(tooltip)
        btn.setMinimumSize(420, 420)
        btn.setMaximumSize(600, 600)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        if Path(icon_path).exists():
            pixmap = QPixmap(icon_path)
            btn.setIcon(QIcon(pixmap))
            btn.setIconSize(pixmap.size().scaled(420, 420, Qt.AspectRatioMode.KeepAspectRatio))

        # Add hover animation
        opacity_effect = QGraphicsOpacityEffect(btn)
        btn.setGraphicsEffect(opacity_effect)

        hover_animation = QPropertyAnimation(opacity_effect, b"opacity")
        hover_animation.setDuration(200)
        hover_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        def animate_hover(enter):
            hover_animation.stop()
            hover_animation.setStartValue(opacity_effect.opacity())
            hover_animation.setEndValue(0.7 if enter else 1.0)
            hover_animation.start()

        btn.enterEvent = lambda e: animate_hover(True)
        btn.leaveEvent = lambda e: animate_hover(False)

        btn.setStyleSheet("""
            QPushButton {
                border: 6px solid #FFD166;
                border-radius: 48px;
                background: qradialgradient(
                    cx:0.5, cy:0.5, radius: 1.0,
                    fx:0.5, fy:0.5,
                    stop:0 #23243a, stop:1 #1A1A2E
                );
                box-shadow: 0 12px 48px #00000044;
            }
            QPushButton:hover {
                border: 6px solid #4ECDC4;
                background: qradialgradient(
                    cx:0.5, cy:0.5, radius: 1.0,
                    fx:0.5, fy:0.5,
                    stop:0 #292F36, stop:1 #23243a
                );
            }
            QToolTip {
                font-size: 28px;
                color: white;
                background-color: #292F36;
                padding: 18px;
                border-radius: 12px;
                opacity: 220;
            }
        """)

        return btn

    def create_flavor_label(self, text):
        """Create a label for the flavor under the icon"""
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("""
            font-size: 38px;
            font-weight: 600;
            color: #FFD166;
            margin-top: 24px;
            letter-spacing: 1px;
        """)
        return label

    def create_icon_with_label_widget(self, btn, label):
        """Combine icon button and label in a vertical layout"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignHCenter)
        widget.setLayout(layout)
        return widget
    
    def start_order(self, flavor):
        """Start processing an ice cream order"""
        if self.current_order:
            logger.warning(f"Already processing {self.current_order} order")
            return
        
        self.current_order = flavor
        self.order_started.emit(flavor)
        
        # Disable buttons during processing
        self.vanilla_btn.setEnabled(False)
        self.mix_btn.setEnabled(False)
        self.chocolate_btn.setEnabled(False)
        
        # Get recipe path
        self.recipes = self.load_recipes(flavor)
        if not self.recipes:
            logger.error(f"No recipe found for flavor: {flavor}")
            self.complete_order()
            return

        def process_next(index=0):
            if index >= len(self.recipes):
                self.complete_order()
                return

            coord = self.recipes[index]
            # If coord is a list with a single int, handle special action
            if isinstance(coord, list) and len(coord) == 1 and isinstance(coord[0], int):
                code = coord[0]
                if code == 0:
                    self.arm_status_changed.emit("Dispensing Vanilla...")
                    self.plc.l_ice(7)
                    time.sleep(4)
                elif code == 1:
                    self.arm_status_changed.emit("Dispensing Mix...")
                    self.plc.m_ice(7)
                    time.sleep(4)
                elif code == 2:
                    self.arm_status_changed.emit("Dispensing Chocolate...")
                    self.plc.r_ice(7)
                    time.sleep(4)
                elif code == 3:
                    self.arm_status_changed.emit("Dispensing Cup...")
                    self.plc.dispenserS(1)
                else:
                    logger.warning(f"Unknown code: {code}")
                # Simulate time for action, then continue
                QTimer.singleShot(1, lambda: process_next(index + 1))
            else:
                # Move arm linearly to the coordinate
                self.arm_status_changed.emit(f"Moving arm to {coord}...")
                try:
                    angles = coord
                    wait_param = True if isinstance(angles, list) and len(angles) >= 7 else False
                    self.arm._arm.set_servo_angle(angle=angles[:6], wait=wait_param, speed=75, mvacc=600, radius=50)
                except Exception as e:
                    logger.error(f"Arm movement failed: {e}")
                QTimer.singleShot(0, lambda: process_next(index + 1))

        process_next()
           

   
    
    
    def complete_order(self):
        """Complete the current order"""
        flavor = self.current_order
        self.current_order = None
        self.order_completed.emit(flavor)
        
        # Re-enable buttons
        self.vanilla_btn.setEnabled(True)
        self.mix_btn.setEnabled(True)
        self.chocolate_btn.setEnabled(True)
        
    
    def update_status(self, flavor):
        """Update the status label based on order state"""
        if self.current_order:
            self.status_label.setText(f"Making your {flavor} ice cream... 🍦")
            self.status_label.setStyleSheet("""
                font-size: 32px;
                font-weight: 500;
                color: #FFD166;
                text-align: center;
                margin-bottom: 20px;
            """)
        else:
            self.status_label.setText(f"Your {flavor} ice cream is ready! Enjoy! 🎉")
            self.status_label.setStyleSheet("""
                font-size: 32px;
                font-weight: 500;
                color: #4ECDC4;
                text-align: center;
                margin-bottom: 20px;
            """)
            # Reset after 5 seconds
            QTimer.singleShot(5000, lambda: self.status_label.setText("Ready to take your order!"))
    
    def update_arm_status(self, status):
        """Update the arm status display"""
        self.arm_status_label.setText(f"🤖 Arm Status: {status}")
        # Ensure the label resizes to fit the text
        self.arm_status_label.setMinimumHeight(50)
        self.arm_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.arm_status_label.adjustSize()
    
    def showEvent(self, event):
        """Handle show event to ensure fullscreen"""
        self.showFullScreen()
        super().showEvent(event)
    
    def _get_stylesheet(self):
        return """
            QWidget {
                background-color: #1A1A2E;
            }
        """

    def keyPressEvent(self, event):
        """Handle key presses (Esc exits fullscreen)"""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        super().keyPressEvent(event)