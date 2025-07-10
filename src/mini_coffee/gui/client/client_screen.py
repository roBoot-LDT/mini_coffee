# src/mini_coffee/gui/client/client_screen.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGraphicsOpacityEffect, QSizePolicy, QGridLayout, QStackedWidget
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
        self.is_cooking = False  # Track cooking state
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

        # Create stacked widget for screens
        self.screen_stack = QStackedWidget()
        main_layout.addWidget(self.screen_stack, 1)  # Takes most space

        # Create screens
        self.main_screen = self.create_main_screen()
        self.coffee_screen = self.create_coffee_screen()
        self.icecream_screen = self.create_icecream_screen()
        
        # Add screens to stack
        self.screen_stack.addWidget(self.main_screen)
        self.screen_stack.addWidget(self.coffee_screen)
        self.screen_stack.addWidget(self.icecream_screen)
        
        # Status bar at bottom
        status_bar = QWidget()
        status_layout = QVBoxLayout()
        self.status_label = QLabel("Ready to take your order!")
        self.status_label.setStyleSheet("""
            font-size: 32px;
            font-weight: 500;
            color: #FFD166;
            text-align: center;
        """)
        status_layout.addWidget(self.status_label)
        
        self.arm_status_label = QLabel("🤖 Arm Status: Ready")
        self.arm_status_label.setStyleSheet("""
            font-size: 24px;
            color: #4ECDC4;
            text-align: center;
        """)
        status_layout.addWidget(self.arm_status_label)
        status_bar.setLayout(status_layout)
        main_layout.addWidget(status_bar)
        
        # Show main screen initially
        self.show_screen("main")

    def create_main_screen(self):
        """Create the main screen with coffee and ice cream icons"""
        screen = QWidget()
        screen.setStyleSheet("background-color: #1A1A2E;")
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title label at the top
        title_label = QLabel("☕ Mini Coffee & Ice Cream Robot 🍦")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 56px;
            font-weight: bold;
            color: #FFD166;
            letter-spacing: 2px;
            margin-bottom: 30px;
            text-shadow: 2px 2px 8px #00000088;
        """)
        layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        
        # Spacer to push icons to vertical center
        layout.addStretch(1)
        
        # Main options centered
        options_layout = QHBoxLayout()
        options_layout.setSpacing(100)
        options_layout.setContentsMargins(50, 0, 50, 0)
        
        # Load icons
        icon_dir = Path(__file__).parent.parent.parent.parent.parent / "resources" / "icons"
        
        # Coffee button
        coffee_icon = str(icon_dir / "coffee.png")
        coffee_btn = self.create_icon_button(coffee_icon, "Coffee Menu")
        coffee_btn.clicked.connect(lambda: self.show_screen("coffee"))
        coffee_widget = self.create_icon_with_label_widget(coffee_btn, QLabel("Coffee"))
        options_layout.addWidget(coffee_widget)
        
        # Ice Cream button
        icecream_icon = str(icon_dir / "ice_cream.png")
        icecream_btn = self.create_icon_button(icecream_icon, "Ice Cream Menu")
        icecream_btn.clicked.connect(lambda: self.show_screen("icecream"))
        icecream_widget = self.create_icon_with_label_widget(icecream_btn, QLabel("Ice Cream"))
        options_layout.addWidget(icecream_widget)
        
        layout.addLayout(options_layout, stretch=0)
        layout.addStretch(2)  # Bottom spacer
        
        screen.setLayout(layout)
        return screen
    
    def create_coffee_screen(self):
        """Create the coffee selection screen"""
        screen = QWidget()
        screen.setStyleSheet("background-color: #1A1A2E;")
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 0)
        
        # Top navigation bar
        nav_bar = QHBoxLayout()
        nav_bar.setContentsMargins(0, 0, 0, 20)
        
        # Home button
        icon_dir = Path(__file__).parent.parent.parent.parent.parent / "resources" / "icons"
        home_icon = str(icon_dir / "home.png")
        home_btn = self.create_nav_button(home_icon, "Home")
        home_btn.clicked.connect(lambda: self.show_screen("main"))
        nav_bar.addWidget(home_btn)
        
        # Title
        title = QLabel("COFFEE MENU")
        title.setStyleSheet("""
            font-size: 48px;
            font-weight: bold;
            color: #FFD166;
            text-align: center;
        """)
        nav_bar.addWidget(title, 1)
        
        # Ice cream button
        icecream_icon = str(icon_dir / "ice_cream.png")
        icecream_btn = self.create_nav_button(icecream_icon, "Ice Cream")
        icecream_btn.clicked.connect(lambda: self.show_screen("icecream"))
        nav_bar.addWidget(icecream_btn)
        
        layout.addLayout(nav_bar)
        
        # Coffee options grid
        coffee_options = [
            "Espresso", "Americano", "Cappuccino", 
            "Latte", "Mocha", "Macchiato",
            "Flat White", "Cold Brew"
        ]
        
        grid = QGridLayout()
        grid.setSpacing(30)
        
        for i, coffee in enumerate(coffee_options):
            btn = QPushButton(coffee)
            btn.setFont(QFont("Arial", 24, QFont.Bold))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #4ECDC4;
                    color: #1A1A2E;
                    border-radius: 20px;
                    padding: 20px;
                }
                QPushButton:disabled {
                    background-color: #555555;
                    color: #aaaaaa;
                }
            """)
            btn.setMinimumSize(300, 100)
            btn.clicked.connect(lambda _, c=coffee: self.start_coffee_order(c))
            grid.addWidget(btn, i // 2, i % 2)
            
        layout.addLayout(grid, 1)
        screen.setLayout(layout)
        
        # Store coffee buttons for enabling/disabling
        self.coffee_buttons = []
        for i in range(grid.count()):
            widget = grid.itemAt(i).widget()
            if isinstance(widget, QPushButton):
                self.coffee_buttons.append(widget)
                
        return screen

    def create_icecream_screen(self):
        """Create the ice cream selection screen"""
        screen = QWidget()
        screen.setStyleSheet("background-color: #1A1A2E;")
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 0)
        
        # Top navigation bar
        nav_bar = QHBoxLayout()
        nav_bar.setContentsMargins(0, 0, 0, 20)
        
        # Home button
        icon_dir = Path(__file__).parent.parent.parent.parent.parent / "resources" / "icons"
        home_icon = str(icon_dir / "home.png")
        home_btn = self.create_nav_button(home_icon, "Home")
        home_btn.clicked.connect(lambda: self.show_screen("main"))
        nav_bar.addWidget(home_btn)
        
        # Title
        title = QLabel("ICE CREAM MENU")
        title.setStyleSheet("""
            font-size: 48px;
            font-weight: bold;
            color: #FFD166;
            text-align: center;
        """)
        nav_bar.addWidget(title, 1)
        
        # Coffee button
        coffee_icon = str(icon_dir / "coffee.png")
        coffee_btn = self.create_nav_button(coffee_icon, "Coffee")
        coffee_btn.clicked.connect(lambda: self.show_screen("coffee"))
        nav_bar.addWidget(coffee_btn)
        
        layout.addLayout(nav_bar)
        
        # Ice cream options
        options_layout = QHBoxLayout()
        options_layout.setSpacing(50)
        options_layout.setContentsMargins(50, 0, 50, 0)

        # Vanilla
        vanilla_icon = str(icon_dir / "l_ice.png")
        vanilla_btn = self.create_icon_button(vanilla_icon, "Salted Caramel")
        vanilla_btn.clicked.connect(lambda: self.start_order("vanilla"))
        vanilla_label = self.create_flavor_label("Salted Caramel")
        self.vanilla_btn = vanilla_btn
        vanilla_widget = self.create_icon_with_label_widget(vanilla_btn, vanilla_label)
        options_layout.addWidget(vanilla_widget)

        # Mix
        mix_icon = str(icon_dir / "m_ice.png")
        mix_btn = self.create_icon_button(mix_icon, "Mix")
        mix_btn.clicked.connect(lambda: self.start_order("mix"))
        mix_label = self.create_flavor_label("Mix")
        self.mix_btn = mix_btn
        mix_widget = self.create_icon_with_label_widget(mix_btn, mix_label)
        options_layout.addWidget(mix_widget)

        # Chocolate
        chocolate_icon = str(icon_dir / "r_ice.png")
        chocolate_btn = self.create_icon_button(chocolate_icon, "Vanilla")
        chocolate_btn.clicked.connect(lambda: self.start_order("chocolate"))
        chocolate_label = self.create_flavor_label("Vanilla")
        self.chocolate_btn = chocolate_btn
        chocolate_widget = self.create_icon_with_label_widget(chocolate_btn, chocolate_label)
        options_layout.addWidget(chocolate_widget)

        layout.addLayout(options_layout, 1)
        screen.setLayout(layout)
        
        # Store ice cream buttons for enabling/disabling
        self.icecream_buttons = [self.vanilla_btn, self.mix_btn, self.chocolate_btn]
        
        return screen
    
    def create_nav_button(self, icon_path, tooltip):
        """Create a navigation button for top bar"""
        btn = QPushButton()
        btn.setToolTip(tooltip)
        btn.setFixedSize(80, 80)
        
        if Path(icon_path).exists():
            pixmap = QPixmap(icon_path)
            btn.setIcon(QIcon(pixmap))
            btn.setIconSize(pixmap.size().scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio))

        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: #444466;
                border-radius: 40px;
            }
        """)
        
        return btn

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
            QPushButton:disabled {
                border: 6px solid #555555;
                background: qradialgradient(
                    cx:0.5, cy:0.5, radius: 1.0,
                    fx:0.5, fy:0.5,
                    stop:0 #333333, stop:1 #222222
                );
            }
            QPushButton:hover:enabled {
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
    
    def show_screen(self, screen_name):
        """Switch between different screens"""
        screens = {
            "main": 0,
            "coffee": 1,
            "icecream": 2
        }
        self.screen_stack.setCurrentIndex(screens[screen_name])
    

    def start_coffee_order(self, coffee_type):
        """Start processing a coffee order (simulated)"""
        if self.is_cooking:
            logger.warning("Already processing an order")
            return
            
        self.is_cooking = True
        self.update_button_states()
        self.status_label.setText(f"Making {coffee_type}...")
        self.order_started.emit(coffee_type)
        
        # Simulate coffee preparation
        QTimer.singleShot(5000, lambda: self.complete_coffee_order(coffee_type))

    def complete_coffee_order(self, coffee_type):
        """Complete the coffee order"""
        self.is_cooking = False
        self.status_label.setText(f"{coffee_type} ready! Enjoy!")
        self.order_completed.emit(coffee_type)
        self.update_button_states()
        
        # Reset status after delay
        QTimer.singleShot(5000, lambda: self.status_label.setText("Ready to take your order!")) 

    def start_order(self, flavor):
        """Start processing an ice cream order"""
        if self.is_cooking:
            logger.warning(f"Already processing an order")
            return
        
        self.is_cooking = True
        self.update_button_states()
        self.status_label.setText(f"Making your {flavor} ice cream...")
        self.order_started.emit(flavor)
        
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
                    self.plc.l_ice(5)
                    time.sleep(7)
                elif code == 1:
                    self.arm_status_changed.emit("Dispensing Mix...")
                    self.plc.m_ice(5)
                    time.sleep(7)
                elif code == 2:
                    self.arm_status_changed.emit("Dispensing Chocolate...")
                    self.plc.r_ice(5)
                    time.sleep(7)
                elif code == 3:
                    self.arm_status_changed.emit("Dispensing Cup...")
                    self.plc.dispenserS(1)
                    time.sleep(0.3)
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
                    self.arm._arm.set_servo_angle(angle=angles[:6], wait=wait_param, speed=60, mvacc=400, radius=50)
                except Exception as e:
                    logger.error(f"Arm movement failed: {e}")
                QTimer.singleShot(0, lambda: process_next(index + 1))

        process_next()
           
    def complete_order(self):
        """Complete the current order"""
        if not self.current_order:
            return
            
        flavor = self.current_order
        self.current_order = None
        self.is_cooking = False
        self.status_label.setText(f"Your {flavor} ice cream is ready! Enjoy!")
        self.order_completed.emit(flavor)
        self.update_button_states()
        
        # Reset status after delay
        QTimer.singleShot(5000, lambda: self.status_label.setText("Ready to take your order!"))
        
    def update_button_states(self):
        """Enable/disable buttons based on cooking state"""
        # Enable navigation buttons always
        # Disable selection buttons during cooking
        state = not self.is_cooking
        
        # Update coffee buttons if they exist
        if hasattr(self, 'coffee_buttons'):
            for btn in self.coffee_buttons:
                btn.setEnabled(state)
        
        # Update ice cream buttons
        if hasattr(self, 'icecream_buttons'):
            for btn in self.icecream_buttons:
                btn.setEnabled(state)

    def update_arm_status(self, status):
        """Update the arm status display"""
        self.arm_status_label.setText(f"🤖 Arm Status: {status}")
        self.arm_status_label.setMinimumHeight(50)
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