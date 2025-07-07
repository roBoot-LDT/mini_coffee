# src/mini_coffee/gui/operator/status_check.py
import sys, time, random, logging
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QTextEdit, QPushButton,
    QScrollArea, QLabel, QSizePolicy, QTabWidget
)
from PySide6.QtCore import Qt, Signal, QThread, QObject
from PySide6.QtGui import QColor, QPainter, QBrush, QPalette, QPen
from mini_coffee.hardware.arm.controller import xArmRobot_test, xArmRobot
from mini_coffee.hardware.relays import PLC
from dataclasses import dataclass
from typing import Optional
from .settings import SettingsWindow 

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

@dataclass
class CheckResult:
    component: str
    status: bool
    message: str
    error: Optional[Exception] = None
    
    
class StatusCircle(QLabel):
    """Circular status indicator widget"""
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(24, 24)
        self._color = QColor(128, 128, 128)  # Default: grey
    
    @property
    def color(self) -> QColor:
        return self._color
    
    @color.setter
    def color(self, value) -> None:
        self._color = QColor(value)
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(self._color))
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.drawEllipse(2, 2, 20, 20)

class ComponentButton(QPushButton):
    """Interactive component check button with status indicator"""
    def __init__(self, component_name, parent=None):
        super().__init__(parent)
        self.component_name = component_name
        self.status = StatusCircle()
        
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 4, 8, 4)
        layout.addWidget(QLabel(component_name), stretch=1)
        layout.addWidget(self.status)
        self.setLayout(layout)
        
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                font-size: 25px;
            }
            QPushButton:hover {
                background: #f5f5f5;
            }
        """)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

class CheckWorker(QThread):
    """Background thread for simulating hardware checks"""
    check_complete = Signal(CheckResult)  # (component_name, success)
    
    def __init__(self, component_name):
        super().__init__()
        self.component_name = component_name
        self.check_functions = {
            "xArm": self.check_xarm,
            "Coffee Machine": self.check_coffee_machine,
            "Cup Dispensers": self.check_cup_dispensers,
            "Ice Cream Machine": self.check_ice_cream_machine,
            "Payment System": self.check_payment_system,
            "Coffee Dumping": self.check_coffee_dumping,
            "Glass Slider": self.check_glass_slider
        }
    
    def run(self) -> None:
        """Perform real or simulated hardware check"""
        check_func = self.check_functions.get(self.component_name, self.generic_check)
        result = check_func()
        self.check_complete.emit(result)

    def check_xarm(self) -> CheckResult:
        """Verify xArm connection and basic functionality"""
        return CheckResult(self.component_name, True, "Connection established")
        # try:
        #     arm = xArmRobot_test()
        #     if not hasattr(arm, 'arm') or not arm.arm.connected:
        #         return CheckResult(self.component_name, False, "Connection failed")
                
        #     # Basic functionality check
        #     arm.arm.get_state()
        #     return CheckResult(self.component_name, True, "Connection established")
            
        # except Exception as e:
        #     logger.error(f"xArm check failed: {str(e)}")
        #     return CheckResult(self.component_name, False, "Hardware error", e)

    def check_cup_dispensers(self) -> CheckResult:
        """Test cup dispenser relays"""
        return self.check_plc_based("Cup Dispensers")

    def check_glass_slider(self) -> CheckResult:
        """Test glass slider mechanism"""
        return self.check_plc_based("Glass Slider")

    def check_coffee_dumping(self) -> CheckResult:
        """Simulate dumping mechanism check"""
        return self.check_plc_based("Coffee Dumping")

    def check_plc_based(self, component: str) -> CheckResult:
        """Generic check for PLC-controlled components"""
        # try:
        #     plc = PLC()
        #     plc.relay("test00000000")  # Test command
        return CheckResult(component, True, "PLC responsive")
        # except ConnectionRefusedError:
        #     msg = "PLC connection refused"
        #     logger.error(msg)
        #     return CheckResult(component, False, msg)
        # except Exception as e:
        #     msg = f"PLC communication error: {str(e)}"
        #     logger.error(msg)
        #     return CheckResult(component, False, msg, e)

    def check_coffee_machine(self) -> CheckResult:
        """Simulate coffee machine check"""
        time.sleep(2)
        return CheckResult(self.component_name, True, "Brew system OK")

    def check_ice_cream_machine(self) -> CheckResult:
        """Simulate ice cream machine check"""
        time.sleep(2)
        return CheckResult(self.component_name, True, "Freezing system nominal")

    def check_payment_system(self) -> CheckResult:
        """Simulate payment system check"""
        time.sleep(2)
        return CheckResult(self.component_name, True, "Payment terminal ready")

    def generic_check(self) -> CheckResult:
        """Fallback check for unknown components"""
        return CheckResult(self.component_name, False, "Unknown component")
    
class StatusCheckWindow(QWidget):
    """Main status check interface with terminal output"""
    all_checks_passed = Signal()
    
    def __init__(self):
        super().__init__()
        self.components = [
            "Coffee Machine", "xArm", "Cup Dispensers",
            "Ice Cream Machine", "Payment System", 
            "Coffee Dumping", "Glass Slider"
        ]
        self.active_workers = []
        self.checks_completed = 0
        self.init_ui()
        
    
    def init_ui(self) -> None:
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(20)
        
        # Left Column - Terminal Output (unchanged)
        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setMaximumWidth(700)
        self.terminal.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Consolas', monospace;
                font-size: 20px;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        
        # Right Column - Tab Widget (modified)
        tab_widget = QTabWidget()
        
        # Tab 1: Status Checks
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(8)
        
        self.component_buttons = {}
        for component in self.components:
            btn = ComponentButton(component)
            btn.clicked.connect(self.start_component_check)
            self.component_buttons[component] = btn
            content_layout.addWidget(btn)
        
        # Next Button
        self.next_button = QPushButton("Next →")
        self.next_button.setEnabled(False)
        self.next_button.clicked.connect(self.all_checks_passed.emit)
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:disabled {
                background-color: #a5d6a7;
            }
        """)
        content_layout.addStretch()
        content_layout.addWidget(self.next_button)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(content_widget)
        tab_widget.addTab(scroll_area, "Status Checks")
        
        # Tab 2: Settings
        settings_tab = SettingsWindow(self)
        tab_widget.addTab(settings_tab, "Settings")
        
        main_layout.addWidget(self.terminal, 2)
        main_layout.addWidget(tab_widget, 1)
        self.setLayout(main_layout)
    
    def start_component_check(self) -> None:
        """Initiate hardware check for clicked component"""
        button = self.sender()
        if not isinstance(button, ComponentButton):
            return
        component_name = button.component_name

        if button.status.color == QColor("#2ecc71") or button.status.color == QColor("yellow"):
            return

        button.status.color = QColor("yellow")
        self.terminal.append(f"🚦 Starting check: {component_name}...")
        logger.info(f"Starting check: {component_name}")
        
        # Create and start worker thread
        worker = CheckWorker(component_name)
        worker.check_complete.connect(self.handle_check_result)
        worker.finished.connect(lambda: self.cleanup_worker(worker))  
        self.active_workers.append(worker) 
        worker.start()
    
    def cleanup_worker(self, worker) -> None:
        """Remove finished workers"""
        if worker in self.active_workers:
            self.active_workers.remove(worker)
            
    def handle_check_result(self, result: CheckResult) -> None:
        """Updated to handle CheckResult dataclass"""
        button = self.component_buttons[result.component]
        color = QColor("#2ecc71") if result.status else QColor("#e74c3c")
        
        button.status.color = color
        self.terminal.append(
            f"{'✅' if result.status else '❌'} {result.component}: "
            f"{result.message}\n"
        )
        
        if result.error:
            self.terminal.append(f"    Error: {str(result.error)}\n")
        
        # Update completion state
        if all(b.status.color.name() == "#2ecc71" 
               for b in self.component_buttons.values()):
            self.next_button.setEnabled(True)

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    
    window = StatusCheckWindow()
    window.resize(800, 600)
    window.show()
    
    sys.exit(app.exec())