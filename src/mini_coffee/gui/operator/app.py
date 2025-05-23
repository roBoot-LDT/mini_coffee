# src/mini_coffee/gui/operator/app.py
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from mini_coffee.gui.operator.status_check import StatusCheckWindow
from mini_coffee.gui.operator.calibration import CalibrationWindow
from mini_coffee.hardware.arm.controller import MockArmController
from PySide6.QtGui import QColor, QPalette
from PySide6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.arm_controller = MockArmController()
        self.init_ui()
        self.setWindowTitle("RoboCafe Control System")
        self.resize(1200, 800)

    def init_ui(self) -> None:
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Initialize windows
        self.status_window = StatusCheckWindow()
        self.calibration_window = CalibrationWindow(self.arm_controller)

        # Connect signals
        self.status_window.all_checks_passed.connect(self.show_calibration)

        # Add to stack
        self.stacked_widget.addWidget(self.status_window)
        self.stacked_widget.addWidget(self.calibration_window)

    def show_calibration(self) -> None:
        self.stacked_widget.setCurrentIndex(1)
        self.setWindowTitle("Calibration Mode - RoboCafe")

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