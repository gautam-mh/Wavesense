# Wavesense: Wireless Gesture-Controlled Air Mouse 🚀

[![Python](https://img.shields.io/badge/python-3.7%2B-blue?logo=python)](https://www.python.org/) [![PlatformIO](https://img.shields.io/badge/PlatformIO-ESP32-orange?logo=platformio)](https://platformio.org/) [![License](https://img.shields.io/badge/license-MIT-green)](#license)

---

> **Turn your hand into a wireless air mouse!**
> 
> Wavesense transforms motion from an ESP32+MPU6050 into real-time mouse and gesture actions on your computer, with a beautiful PyQt5 GUI for configuration and feedback.

---

## ✨ Features

- 🖱️ Wireless air mouse (ESP32 + MPU6050 IMU)
- 🤚 Real-time gesture recognition & mapping
- 🖥️ PyQt5 GUI for configuration and live feedback
- 🔄 Customizable gesture-to-action mapping
- 🛠️ Sensor calibration tools
- ⚡ Modular, extensible Python backend
- 🔌 WiFi communication with ESP32

---

<details>
<summary><strong>📁 Directory Structure</strong> (click to expand)</summary>

```text
Wavesense/
│
├── main.py                # Main GUI application (PyQt5)
├── config.py              # Configuration and parameters
├── gesture_handler.py     # Gesture recognition logic
├── mouse_controller.py    # Mouse and gesture action handler
├── wifi_handler.py        # WiFi communication with ESP32
│
├── esp32_code/            # ESP32 firmware (PlatformIO project)
│   ├── src/
│   │   └── main.cpp
│   ├── include/
│   ├── lib/
│   └── test/
│
├── libraries/             # Arduino libraries for ESP32
│   ├── BluetoothSerial/
│   ├── MPU6050/
│   └── MPU6050_tockn/
│
└── README.md              # Project documentation (this file)
```
</details>

---

## ⚡ Quick Start

1. **Clone the repo:**

   ```bash
   git clone https://github.com/yourusername/wavesense.git
   cd wavesense
   ```

2. **Install Python dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the GUI:**

   ```bash
   python main.py
   ```

4. **Flash ESP32 firmware:**
   - Open `esp32_code/` in [PlatformIO](https://platformio.org/)
   - Build & upload to your ESP32

---

## 🛠️ Build & Run Instructions

### 1. Python Application (Desktop Side)

#### Prerequisites
- Python 3.7+
- pip (Python package manager)
- Windows, macOS, or Linux

#### Install All Dependencies

> **Tip:** All required packages are listed in `requirements.txt`.

```bash
pip install -r requirements.txt
```

#### Run the Application

```bash
python main.py
```

- The PyQt5 GUI will launch. Configure your ESP32's IP and connect!

#### Troubleshooting
- If you see missing package errors, ensure you are using the correct Python version and environment.
- For GUI issues, check PyQt5 installation: `pip show PyQt5`.

---

### 2. ESP32 Firmware (Sensor Side)

#### Prerequisites
- [PlatformIO](https://platformio.org/) (VSCode extension recommended)
- ESP32 development board

#### Build & Upload Firmware
1. Open the `esp32_code/` folder in VSCode with PlatformIO.
2. Connect your ESP32 via USB.
3. Click **Build** (checkmark icon) and then **Upload** (right arrow icon) in the PlatformIO toolbar.
4. Use the **Serial Monitor** to debug (magnifier icon).

#### Libraries
- All required Arduino libraries are included in `libraries/`.
- PlatformIO will auto-detect them, but you can add them via `platformio.ini` if needed.

---

## 🖼️ Screenshots & Demo

> _Add screenshots or GIFs of the GUI and device in action here!_

---

## 🧑‍💻 Configuration & Customization

- All parameters (sampling rate, gesture mappings, etc.) are in `config.py`.
- Edit `gesture_handler.py` to add or modify gesture logic.
- GUI options allow live calibration and mode switching.

---

## 📚 Usage Guide

1. **Power on** your ESP32 with the firmware loaded.
2. **Launch** the Python GUI (`main.py`).
3. **Enter** the ESP32's IP address and click **Connect**.
4. **Switch modes** (Cursor, Gesture, Idle) as needed.
5. **Calibrate** using the GUI for best results.

### Default Gestures
- `UP`, `DOWN`, `LEFT`, `RIGHT`: Media/navigation
- `CIRCLE`: Switch app
- `SHAKE`: Undo/cancel

_Customize gestures in `config.py` and `gesture_handler.py`._

---

## 🤝 Contributing

Contributions are welcome! To get started:

1. Fork this repo
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Commit your changes
4. Push and open a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for more.

---

## 📝 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## 🙏 Credits

- MPU6050 library by Electronic Cats
- BluetoothSerial library by Henry Abrahamsen
- PyQt5, pyautogui, and other open-source packages

---

## ❓ FAQ & Troubleshooting

- **Q:** _ESP32 not connecting to PC?_
  - **A:** Ensure both are on the same WiFi network. Check firewall settings.
- **Q:** _GUI not launching?_
  - **A:** Check PyQt5 installation and Python version.
- **Q:** _Firmware upload fails?_
  - **A:** Check USB cable, board selection, and PlatformIO drivers.
- **Q:** _How to debug ESP32?_
  - **A:** Use PlatformIO's Serial Monitor for real-time logs.

---

> _Made with ❤️ for makers, tinkerers, and accessibility enthusiasts!_ 