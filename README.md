
# 🤖 RoboCafe Control System

A Python-based GUI application to operate and calibrate an automated robotic coffee and ice-cream station. The system is built with PySide6 and designed for use with xArm robotic arms, coffee/ice-cream machines, cup dispensers, shields, and Vendista for client payments.

---

## 🚀 Features

- **Component Health Check**: Run diagnostics on all machines (robotic arm, dispensers, dumping mechanism, etc.).
- **Manual & Assisted Calibration**: Adjust arm positions via interactive GUI with drag-and-drop node editor and live coordinate control (XYZ + RPY).
- **Flow-Based Node Editor**: Design custom delivery paths using a visual flowchart system.
- **Recipe Editor**: Create and edit recipes that define arm actions and sequences.
- **Operator & Client Modes**: Seamlessly switch between technician/operator and client-facing interfaces.
- **Environment Settings Panel**: Easily update network settings and relay mappings through `.env`.
- **Logging & Error Handling**: Centralized logging with `loguru`, robust error management, and safe shutdown prompts.

---

## 🖥️ Screenshots

_(Insert screenshots of the schematic view, calibration controls, and client UI here)_

---

## 🧱 Project Structure

```

robotic-coffee-station/
├── app.py                       # App entry point
├── gui/                         # GUI layers
│   ├── operator/
│   │   ├── calibration.py       # Calibration system (schematic + node editor)
│   │   └── settings.py          # Network/device settings manager
├── hardware/
│   ├── arm/controller.py        # xArm SDK interface or mock
│   └── relays/plc.py            # PLC-based relay controller
├── utils/
│   ├── logger.py                # loguru setup
│   └── helpers.py               # pathfinder, helpers
├── data/
│   ├── calibration.json         # Flowchart connections
│   ├── components.json          # Schematic component coordinates
│   ├── nodes.json               # Node positions and calibration info
├── resources/
│   └── icons/                   # UI icons for devices
├── .env                         # Environment config (Vendista keys, IPs, ports)
├── pyproject.toml               # Poetry config
├── README.md

````

---

## ⚙️ Setup

### Requirements

- Python 3.10+
- Poetry
- xArm SDK (for real arm control)
- PySide6, loguru, python-dotenv

### Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/robotic-coffee-station
cd robotic-coffee-station

# Install dependencies
poetry install

# Create .env file
cp .env.example .env
# Edit .env to configure relay IPs, Vendista keys, etc.
````

### Run the App

```bash
poetry run python app.py
```

---

## 🔑 Environment Variables (.env)

```env
RELAY_IP=192.168.1.130
RELAY_UTP_PORT=5005
BUFFER_SIZE=1024
XARMAPI=192.168.1.191

DISPENSER_S=all00000001
DISPENSER_M=all00000010
BIN=all00000100
SHIELD=all00001000

VENDISTA_API_KEY=your-secure-key
```

---

## 🧪 Testing

To run tests (planned or future):

```bash
poetry run pytest tests/
```

---

## 🧰 Tech Stack

* **Python 3.10+**
* **PySide6** – GUI
* **loguru** – Logging
* **dotenv** – Environment variable handling
* **xArm SDK** – Robotic arm control
* **Poetry** – Dependency management
* **QGraphicsScene** – Custom node editor & schematic layout

---

## 📌 Status

This project is actively developed. Calibration logic and schematic interface are operational. Recipes, client interface, and Vendista integration are in progress.

---

## 📃 License

MIT License. See `LICENSE` file for details.

---

## 👤 Author

Developed by Nemkov M, 2025.

