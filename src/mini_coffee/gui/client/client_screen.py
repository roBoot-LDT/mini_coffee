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
            recipes = data.recipes if hasattr(data, "recipes") else data.get("recipes", {})
            if not recipes:
                raise ValueError("No recipes found in Data(3)")
            return recipes[flavor] if flavor in recipes else {}
        except Exception as e:
            logger.error(f"Failed to load recipes from Data(3): {e}. Using defaults.")
            
    
    def init_ui(self):
        # Main layout with background
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)
        
        # Background container
        bg_widget = QWidget()
        bg_widget.setStyleSheet("background-color: #1A1A2E;")
        bg_layout = QVBoxLayout(bg_widget)
        bg_layout.setContentsMargins(50, 50, 50, 50)
        bg_layout.setSpacing(40)
        
        # Header
        header = QLabel("Mini Ice Cream Barista")
        header.setStyleSheet("""
            font-size: 48px;
            font-weight: bold;
            color: #FF6B6B;
            text-align: center;
            margin-top: 20px;
        """)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bg_layout.addWidget(header)
        
        # Instruction
        instruction = QLabel("Select your ice cream flavor:")
        instruction.setStyleSheet("""
            font-size: 32px;
            color: #4ECDC4;
            text-align: center;
            margin-bottom: 40px;
        """)
        instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bg_layout.addWidget(instruction)
        
        # Ice cream options
        options_layout = QHBoxLayout()
        options_layout.setSpacing(50)
        options_layout.setContentsMargins(50, 0, 50, 0)
        
        # Load icons
        icon_dir = Path(__file__).parent.parent.parent.parent.parent / "resources" / "icons"
        
        # Vanilla
        vanilla_icon = str(icon_dir / "l_ice.png")
        self.vanilla_btn = self.create_icon_button(vanilla_icon, "Vanilla")
        self.vanilla_btn.clicked.connect(lambda: self.start_order("vanilla"))
        options_layout.addWidget(self.vanilla_btn)
        
        # Mix
        mix_icon = str(icon_dir / "m_ice.png")
        self.mix_btn = self.create_icon_button(mix_icon, "Chocolate & Vanilla")
        self.mix_btn.clicked.connect(lambda: self.start_order("mix"))
        options_layout.addWidget(self.mix_btn)
        
        # Chocolate
        chocolate_icon = str(icon_dir / "r_ice.png")
        self.chocolate_btn = self.create_icon_button(chocolate_icon, "Chocolate")
        self.chocolate_btn.clicked.connect(lambda: self.start_order("chocolate"))
        options_layout.addWidget(self.chocolate_btn)
        
        bg_layout.addLayout(options_layout)
        
        # Status area
        status_widget = QWidget()
        status_widget.setStyleSheet("""
            background-color: #292F36;
            border-radius: 25px;
            padding: 30px;
        """)
        status_layout = QVBoxLayout(status_widget)
        status_layout.setSpacing(20)
        
        self.status_label = QLabel("Ready to take your order!")
        self.status_label.setStyleSheet("""
            font-size: 32px;
            font-weight: 500;
            color: #4ECDC4;
            text-align: center;
            margin-bottom: 20px;
        """)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.status_label)
        
        # Progress bar simulation
        self.progress_label = QLabel()
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setMinimumHeight(30)
        self.progress_label.setStyleSheet("""
            font-size: 24px;
            color: #FFD166;
            font-family: 'Courier New', monospace;
        """)
        status_layout.addWidget(self.progress_label)
        
        # Arm status
        self.arm_status_label = QLabel()
        self.arm_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.arm_status_label.setMinimumHeight(30)
        self.arm_status_label.setStyleSheet("""
            font-size: 24px;
            color: #FF6B6B;
            font-family: 'Courier New', monospace;
        """)
        status_layout.addWidget(self.arm_status_label)
        
        # Back button (for operator)
        back_btn = QPushButton("Operator Mode")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #6A0572;
                color: white;
                padding: 15px 30px;
                border-radius: 10px;
                font-size: 20px;
                font-weight: bold;
                margin-top: 20px;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #7D3C98;
            }
        """)
        back_btn.clicked.connect(self.close)
        status_layout.addWidget(back_btn, 0, Qt.AlignmentFlag.AlignRight)
        
        bg_layout.addWidget(status_widget)
        main_layout.addWidget(bg_widget)
        
        # Set size policies
        bg_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Connect signals
        self.order_started.connect(self.update_status)
        self.order_completed.connect(self.update_status)
        self.arm_status_changed.connect(self.update_arm_status)
    
    def create_icon_button(self, icon_path, tooltip):
        """Create a clickable icon button with animation"""
        btn = QPushButton()
        btn.setToolTip(tooltip)
        btn.setMinimumSize(300, 300)
        btn.setMaximumSize(400, 400)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        if Path(icon_path).exists():
            pixmap = QPixmap(icon_path)
            btn.setIcon(QIcon(pixmap))
            btn.setIconSize(pixmap.size().scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio))
        
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
                border: none;
                background: transparent;
            }
            QToolTip {
                font-size: 24px;
                color: white;
                background-color: #292F36;
                padding: 15px;
                border-radius: 10px;
                opacity: 200;
            }
        """)
        
        return btn
    
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
        path = self.recipes[flavor]
        self.order_path = path.copy()
        def process_next_step():
            if not self.order_path:
                self.complete_order()
                return

            step = self.order_path.pop(0)
            coord = self.load_recipes(flavor)
            if isinstance(coord, list) and len(coord) == 6:
                self.arm_status_changed.emit(f"Moving to {step}...")
                try:
                    self.arm.set_position(*coord, wait=True)
                except Exception as e:
                    logger.error(f"Arm move failed at {step}: {e}")
                    self.arm_status_changed.emit(f"Error at {step}")
                    self.complete_order()
                    return
                QTimer.singleShot(500, process_next_step)
            else:
                # Handle special steps for ice cream dispensing
                if isinstance(coord, list) and len(coord) == 1 and isinstance(coord[0], int):
                    if coord[0] == 0:
                        self.arm_status_changed.emit("Dispensing Vanilla...")
                        self.plc.l_ice(1)
                    elif coord[0] == 1:
                        self.arm_status_changed.emit("Dispensing Mix...")
                        self.plc.m_ice(1)
                    elif coord[0] == 2:
                        self.arm_status_changed.emit("Dispensing Chocolate...")
                        self.plc.r_ice(1)
                    elif coord[0] == 3:
                        self.arm_status_changed.emit("Dispensing Cup...")
                        self.plc.dispenserS(1)
                    else:
                        logger.warning(f"Unknown ice cream code: {coord[0]}")
                else:
                    # Skip steps that are not valid 6D coordinates
                    logger.warning(f"Skipping invalid step: {step} -> {coord}")
                QTimer.singleShot(100, process_next_step)

        process_next_step()
   
    
    
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