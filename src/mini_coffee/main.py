# src/mini_coffee/gui/operator/app.py
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QMessageBox, QTabWidget
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
        self.resize(1600, 900)
        self.show()    

    def init_ui(self) -> None:
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.tabs.setTabPosition(QTabWidget.TabPosition.West)
        self.tabs.setStyleSheet("""
            QTabBar::tab {
                border: 1px solid #444;
                padding: 45px 12px;
                margin: 2px;
                border-radius: 5px;
            }
            QTabBar::tab:selected {
                background: #666;
            }
        """)
        # Initialize tabs
        self.settings_window = SettingsWindow()
        self.status_window = StatusCheckWindow()
        self.calibration_window = CalibrationWindow(self.arm_controller)

        # Add to stack
        self.tabs.addTab(self.settings_window, "Settings")
        self.tabs.addTab(self.status_window, "Status Check")
        self.tabs.addTab(self.calibration_window, "Calibration")

    def load_environment(self) -> None:
        # Reload environment variables after save
        load_dotenv(override=True)
        # Update other components with new settings
        self.settings_window.plc = PLC()

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