# src/mini_coffee/gui/operator/settings.py
import os
from pathlib import Path
from dotenv import load_dotenv, dotenv_values
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
    QLabel, QMessageBox, QInputDialog
)
from PySide6.QtCore import Qt
from mini_coffee.hardware.relays import PLC

class SettingsWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.plc = PLC()
        self.env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
        self.init_ui()
        self.load_settings()

    def init_ui(self) -> None:
        layout = QVBoxLayout()

        # Network Settings
        layout.addWidget(QLabel("Relay Settings:"))
        self.ip_input = QLineEdit()
        self.port_input = QLineEdit()
        self.buffer_input = QLineEdit()
        self.xarm_input = QLineEdit()
        self.disS = QLineEdit()
        self.disM = QLineEdit()
        self.shield = QLineEdit()
        self.bin = QLineEdit()

        layout.addWidget(QLabel("Relay IP:"))
        layout.addWidget(self.ip_input)
        layout.addWidget(QLabel("Relay UDP Port:"))
        layout.addWidget(self.port_input)
        layout.addWidget(QLabel("Buffer Size:"))
        layout.addWidget(self.buffer_input)
        layout.addWidget(QLabel("XArm API:"))
        layout.addWidget(self.xarm_input)
        layout.addWidget(QLabel("Dispenser S:"))
        layout.addWidget(self.disS)
        layout.addWidget(QLabel("Dispenser M:"))
        layout.addWidget(self.disM)
        layout.addWidget(QLabel("Shield:"))
        layout.addWidget(self.shield)
        layout.addWidget(QLabel("Bin:"))
        layout.addWidget(self.bin)

        # Control Buttons
        btn_layout = QHBoxLayout()
        self.trigger_btn = QPushButton("Trigger All Relays")
        self.detect_btn = QPushButton("Check Ports")
        self.save_btn = QPushButton("Save Settings")

        self.trigger_btn.clicked.connect(self.plc.trigger_all)
        self.detect_btn.clicked.connect(self.detect_ports)
        self.save_btn.clicked.connect(self.save_settings)

        btn_layout.addWidget(self.trigger_btn)
        btn_layout.addWidget(self.detect_btn)
        btn_layout.addWidget(self.save_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_settings(self) -> None:
        if self.env_path.exists():
            config = dotenv_values(self.env_path)
            self.ip_input.setText(config.get('RELAY_IP') or '192.168.1.130')
            self.port_input.setText(config.get('RELAY_UTP_PORT') or '5005')
            self.buffer_input.setText(config.get('BUFFER_SIZE') or '1024')
            self.xarm_input.setText(config.get('XARMAPI') or '192.168.1.191')
            self.disS.setText(config.get('DISPENSER_S') or 'all00000001')
            self.disM.setText(config.get('DISPENSER_M') or 'all00000010')
            self.bin.setText(config.get('BIN') or 'all00000100')
            self.shield.setText(config.get('SHIELD') or 'all00001000')

    def save_settings(self) -> None:
        env_content = f"""RELAY_IP={self.ip_input.text()}
RELAY_UTP_PORT={self.port_input.text()}
BUFFER_SIZE={self.buffer_input.text()}
XARMAPI={self.xarm_input.text()}
DISPENSER_S={self.disS.text()}
DISPENSER_M={self.disM.text()}
BIN={self.bin.text()}
SHIELD={self.shield.text()}"""
        
        try:
            with open(self.env_path, 'w') as f:
                f.write(env_content)
            QMessageBox.information(self, "Success", "Settings saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")

    def detect_ports(self) -> None:
        options = ["dispenserS", "dispenserM", "shield", "bin", "skip"]
        for i in range(8):
            state = f"all{format(1 << i, '08b')}"
            self.plc.relay(state)
            choice, ok = QInputDialog.getItem(
                self,
                "Port Configuration",
                f"Select device for port {i+1}:",
                options,
                0,
                False
            )
            
            if ok and choice != "skip":
                mapping = {
                    "dispenserS": self.disS,
                    "dispenserM": self.disM,
                    "shield": self.shield,
                    "bin": self.bin
                }
                if choice in mapping:
                    mapping[choice].setText(state)
                print(f"Configuring port {i+1} as {choice}")
            elif not ok:
                break