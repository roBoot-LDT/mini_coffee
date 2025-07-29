# src/mini_coffee/gui/operator/settings.py
# src/mini_coffee/gui/operator/settings.py
import os
from pathlib import Path
from dotenv import load_dotenv, dotenv_values # type: ignore
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QMessageBox, QInputDialog, QGroupBox, QScrollArea, QDialog, QComboBox
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from mini_coffee.hardware.relays import PLC
from mini_coffee.utils.logger import setup_logger

logger = setup_logger()

class SettingsWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.plc = PLC()
        self.env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
        self.init_ui()
        self.load_settings()
        self.setStyleSheet(self._get_stylesheet())
        self.setMinimumWidth(350)
        self.setMaximumWidth(700)

    def init_ui(self) -> None:
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        
        # Scroll area for settings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(20)
        scroll.setMaximumWidth(700)
        content.setMaximumWidth(700)

        # Titles
        self.ip_input = QLineEdit()
        self.port_input = QLineEdit()
        self.buffer_input = QLineEdit()
        self.xarm_input = QLineEdit()
        self.disS = QLineEdit()
        self.disM = QLineEdit()
        self.shield = QLineEdit()
        self.bin = QLineEdit()
        self.l_ice = QLineEdit()
        self.m_ice = QLineEdit()
        self.r_ice = QLineEdit()
        
        # Network Configuration Group
        network_group = QGroupBox("Network Configuration")
        network_layout = QVBoxLayout()
        network_layout.setSpacing(12)
        
        self._create_input_field(network_layout, "Relay IP:", self.ip_input)
        self._create_input_field(network_layout, "Relay UDP Port:", self.port_input)
        self._create_input_field(network_layout, "Buffer Size:", self.buffer_input)
        self._create_input_field(network_layout, "XArm API:", self.xarm_input)
        network_group.setLayout(network_layout)
        layout.addWidget(network_group)

        # Device Mapping Group
        device_group = QGroupBox("Device Mapping")
        device_layout = QVBoxLayout()
        device_layout.setSpacing(12)
        
        self._create_input_field(device_layout, "Dispenser S:", self.disS)
        self._create_input_field(device_layout, "Dispenser M:", self.disM)
        self._create_input_field(device_layout, "Shield:", self.shield)
        self._create_input_field(device_layout, "Bin:", self.bin)
        self._create_input_field(device_layout, "Left Ice:", self.l_ice)
        self._create_input_field(device_layout, "Middle Ice:", self.m_ice)
        self._create_input_field(device_layout, "Right Ice:", self.r_ice)
        device_group.setLayout(device_layout)
        layout.addWidget(device_group)

        # Control Buttons
        btn_layout_top = QHBoxLayout()
        btn_layout_bottom = QHBoxLayout()
        btn_layout_top.setSpacing(12)
        btn_layout_bottom.setSpacing(12)
        self.trigger_btn = QPushButton("🔌 Trigger All Relays")
        self.detect_btn = QPushButton("🔎 Detect Ports")
        self.save_btn = QPushButton("💾 Save Settings")

        self.trigger_btn.clicked.connect(self.plc.trigger_all)
        self.detect_btn.clicked.connect(self.detect_ports)
        self.save_btn.clicked.connect(self.save_settings)

        for btn in [self.trigger_btn, self.detect_btn, self.save_btn]:
            btn.setMinimumHeight(40)

        btn_layout_top.addWidget(self.trigger_btn)
        btn_layout_top.addWidget(self.detect_btn)
        btn_layout_bottom.addWidget(self.save_btn)
        layout.addLayout(btn_layout_top)
        layout.addLayout(btn_layout_bottom)

        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

    def _create_input_field(self, layout, label, widget):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel(label)
        lbl.setFixedWidth(120)
        widget.setMinimumHeight(35)
        widget.setMaximumWidth(250)
        row.addWidget(lbl)
        row.addWidget(widget)
        layout.addLayout(row)

    def _get_stylesheet(self):
        return """
            QWidget {
                background-color: #2d2d2d;
                color: #e0e0e0;
                font-size: 14px;
            }
            QGroupBox {
                border: 1px solid #3c3c3c;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #88c0d0;
            }
            QLineEdit {
                background-color: #383838;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', monospace;
            }
            QLineEdit:focus {
                border-color: #88c0d0;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 500;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QScrollArea {
                border: none;
            }
        """

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
            self.l_ice.setText(config.get('LEFT_ICE') or 'all00001000')
            self.m_ice.setText(config.get('MIDDLE_ICE') or 'all00001000')
            self.r_ice.setText(config.get('RIGHT_ICE') or 'all00001000')

    def save_settings(self) -> None:
        env_content = f"""RELAY_IP={self.ip_input.text()}
                        RELAY_UTP_PORT={self.port_input.text()}
                        BUFFER_SIZE={self.buffer_input.text()}
                        XARMAPI={self.xarm_input.text()}
                        DISPENSER_S={self.disS.text()}
                        DISPENSER_M={self.disM.text()}
                        BIN={self.bin.text()}
                        SHIELD={self.shield.text()}
                        ICE_LEFT={self.l_ice.text()}
                        ICE_MIDDLE={self.m_ice.text()}
                        ICE_RIGHT={self.r_ice.text()}"""
        
        try:
            with open(self.env_path, 'w') as f:
                f.write(env_content)
            QMessageBox.information(self, "Success", "Settings saved successfully!")
            logger.info("Settings saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")
            logger.error(f"Failed to save settings: {str(e)}")

    def detect_ports(self) -> None:
        options = ["Dispenser S", "Dispenser M", "Shield", "Bin", "Left Ice", "Middle Ice", "Right Ice"]
        mapping = {
            "Dispenser S": self.disS,
            "Dispenser M": self.disM,
            "Shield": self.shield,
            "Left Ice": self.l_ice,
            "Middle Ice": self.m_ice,
            "Right Ice": self.r_ice,
            "Bin": self.bin
        }
        
        # Track which devices have been assigned
        assigned_devices = set()
        
        # Create a dialog that will be reused for each port
        dialog = PortConfigDialog(options, self)
        
        for i in range(8):
            state = f"all{format(1 << i, '08b')}"
            self.plc.relay(state)
            
            # Update dialog for current port
            dialog.set_port_number(state)
            
            # Only show unassigned options
            dialog.set_options([opt for opt in options if opt not in assigned_devices])
            
            result = dialog.exec()
            choice = dialog.selected

            if result == 1 and choice is not None and choice != "skip":
                # Update input field and mark device as assigned
                mapping[choice].setText(state)
                assigned_devices.add(choice)
                logger.info(f"Port {state} configured for {choice} with state {state}")
                
                # Mark button as green for this device
                dialog.mark_button_green(choice)
                
                # If all devices are assigned, break early
                if len(assigned_devices) == len(options):
                    break
            elif result == 2 or choice == "skip":
                continue
            else:
                break



class PortConfigDialog(QDialog):
    def __init__(self, options, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Port Configuration")
        self.selected = None
        self.button_states = {opt: False for opt in options}
        self.buttons = {}
        self.current_port = ""

        layout = QVBoxLayout(self)
        
        # Port label
        self.port_label = QLabel()
        self.port_label.setStyleSheet("font-size: 22px;")
        self.port_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.port_label)
        
        # Device buttons container
        self.btn_container = QWidget()
        self.btn_layout = QHBoxLayout(self.btn_container)
        self.btn_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.btn_container)
        
        # Create buttons for all options
        icon_map = {
            "Dispenser S": "cup_S.png",
            "Dispenser M": "ice.png",
            "Shield": "shield.png",
            "Left Ice": "l_ice.png",
            "Right Ice": "r_ice.png",
            "Middle Ice": "m_ice.png",
            "Bin": "bin.png"
        }
        for opt in options:
            self._create_button(opt, icon_map.get(opt, ""))
        
        # Cancel and Skip buttons
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        skip_btn = QPushButton("Skip")
        cancel_btn.clicked.connect(self.reject)
        skip_btn.clicked.connect(self.skip)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(skip_btn)
        layout.addLayout(btn_layout)
    
    def _create_button(self, opt, icon_name):
        vbox = QVBoxLayout()
        vbox.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        
        btn = QPushButton()
        btn.setFixedSize(80, 80)
        btn.setObjectName(opt)
        btn.setEnabled(False)  # Disabled by default
        
        # Set icon if available
        icon_path = Path(__file__).parent.parent.parent.parent.parent / "resources" / "icons" / icon_name
        if icon_path.exists():
            btn.setIcon(QIcon(str(icon_path)))
            btn.setIconSize(QSize(70, 70))
            btn.clicked.connect(lambda _, o=opt: self.select_device(o))
        
        # Set initial style based on state
        self._update_button_style(btn, self.button_states[opt])
        
        label = QLabel(opt)
        label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        label.setStyleSheet("font-size: 13px; color: white; margin-top: 6px;")

        vbox.addWidget(btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        vbox.addWidget(label)
        self.btn_layout.addLayout(vbox)
        
        self.buttons[opt] = btn
    
    def _update_button_style(self, btn, is_selected):
        if is_selected:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    border-radius: 12px;
                    min-width: 80px;
                    min-height: 80px;
                    border: 2px solid #388E3C;
                }
            """)
        else:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    border-radius: 12px;
                    min-width: 80px;
                    min-height: 80px;
                    border: 2px solid #b71c1c;
                }
                QPushButton:hover {
                    background-color: #ff5252;
                }
            """)
    
    def set_port_number(self, port_number):
        self.current_port = port_number
        self.port_label.setText(f"Select device for port {port_number}:")
    
    def set_options(self, options):
        """Enable only the unassigned options"""
        for opt, btn in self.buttons.items():
            if opt in options:
                btn.setEnabled(True)
                self._update_button_style(btn, self.button_states[opt])
            else:
                btn.setEnabled(False)
    
    def mark_button_green(self, device):
        """Mark a device as selected (green)"""
        self.button_states[device] = True
        btn = self.buttons[device]
        self._update_button_style(btn, True)
        btn.setEnabled(False)
    
    def select_device(self, device):
        self.selected = device
        self.accept()
    
    def skip(self):
        self.selected = "skip"
        self.done(2)