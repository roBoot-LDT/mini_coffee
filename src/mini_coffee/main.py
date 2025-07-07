# src/mini_coffee/gui/operator/app.py
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QMessageBox
from mini_coffee.gui.operator.status_check import StatusCheckWindow
from mini_coffee.gui.operator.calibration import CalibrationWindow
from mini_coffee.hardware.arm.controller import MockArmController
from PySide6.QtGui import QColor, QPalette
from PySide6.QtCore import Qt
from mini_coffee.gui.operator.settings import SettingsWindow
from dotenv import load_dotenv # type: ignore
from mini_coffee.hardware.relays import PLC
from mini_coffee.utils.logger import setup_logger

logger = setup_logger()

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.arm_controller = MockArmController()
        self.init_ui()
        self.setWindowTitle("RoboCafe Control System")
        self.resize(1350, 800)
        self.show_status()

    def init_ui(self) -> None:
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Initialize windows
        self.settings_window = SettingsWindow()
        self.status_window = StatusCheckWindow()
        self.calibration_window = CalibrationWindow(self.arm_controller)

        # Connect signals
        self.settings_window.save_btn.clicked.connect(self.load_environment)
        self.status_window.all_checks_passed.connect(self.show_calibration)

        # Add to stack
        self.stacked_widget.addWidget(self.settings_window)
        self.stacked_widget.addWidget(self.status_window)
        self.stacked_widget.addWidget(self.calibration_window)

    def show_status(self) -> None:
        self.stacked_widget.setCurrentIndex(1)
        self.setWindowTitle("Status Check - RoboCafe")

    def load_environment(self) -> None:
        # Reload environment variables after save
        load_dotenv(override=True)
        # Update other components with new settings
        self.settings_window.plc = PLC()
    
    def show_calibration(self) -> None:
        self.stacked_widget.setCurrentIndex(2)
        self.setWindowTitle("Calibration Mode - RoboCafe")

    def closeEvent(self, event):
        """Handle window closure safely."""
        reply = QMessageBox.question(
            self, "Exit", "Exit application?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            logger.info("Application closed")
            event.accept()
        else:
            event.ignore()

def run():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Set dark theme
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(142, 45, 197))
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    
    app.setPalette(dark_palette)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run()