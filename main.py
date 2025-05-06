import sys
import logging
import os
import threading
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSlider, QTextEdit, QGroupBox, QGridLayout, QComboBox, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from wifi_handler import WiFiHandler
from mouse_controller import MouseController
from gesture_handler import GestureHandler
import pyautogui

class QTextEditLogger(logging.Handler, QObject):
    append_text = pyqtSignal(str)

    def __init__(self, text_edit):
        logging.Handler.__init__(self)
        QObject.__init__(self)
        self.text_edit = text_edit
        self.append_text.connect(self._append)

    def emit(self, record):
        msg = self.format(record)
        self.append_text.emit(msg)

    def _append(self, msg):
        self.text_edit.append(msg)
        self.text_edit.ensureCursorVisible()

class AirMouseGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Air Mouse Controller (WiFi)")
        self.setGeometry(100, 100, 500, 600)

        self.setup_logging()

        self.wifi_handler = WiFiHandler()
        self.mouse_controller = MouseController()
        self.gesture_handler = GestureHandler()

        self.wifi_handler.set_data_callback(self.mouse_controller.process_data)
        self.gesture_handler.register_callback("GESTURE", self.handle_gesture)
        self.mouse_controller.set_gesture_callback(self.gesture_handler.process_data)

        self.setup_gesture_callbacks()
        self.init_ui()

    def setup_gesture_callbacks(self):
        gestures = ["UP", "DOWN", "LEFT", "RIGHT", "CIRCLE", "SHAKE"]
        actions = {
            "UP": lambda: pyautogui.press('volumeup'),
            "DOWN": lambda: pyautogui.press('volumedown'),
            "LEFT": lambda: pyautogui.press('left'),
            "RIGHT": lambda: pyautogui.press('right'),
            "CIRCLE": lambda: pyautogui.hotkey('alt', 'tab'),
            "SHAKE": lambda: pyautogui.press('esc')
        }
        for gesture in gestures:
            self.gesture_handler.register_callback(gesture, actions[gesture])

    def setup_logging(self):
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, "air_mouse.log")),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('AirMouse.GUI')

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Connection Group
        conn_group = QGroupBox("Connection")
        conn_layout = QHBoxLayout()
        conn_group.setLayout(conn_layout)
        conn_layout.addWidget(QLabel("ESP32 IP:"))
        self.ip_input = QLineEdit("192.168.4.1")
        conn_layout.addWidget(self.ip_input)
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)
        conn_layout.addWidget(self.connect_btn)
        self.status_label = QLabel("Disconnected")
        conn_layout.addWidget(self.status_label)
        main_layout.addWidget(conn_group)

        # Operation Mode Group
        mode_group = QGroupBox("Operation Mode")
        mode_layout = QHBoxLayout()
        mode_group.setLayout(mode_layout)
        self.cursor_btn = QPushButton("Cursor Mode")
        self.cursor_btn.clicked.connect(self.set_cursor_mode)
        mode_layout.addWidget(self.cursor_btn)
        self.gesture_btn = QPushButton("Gesture Mode")
        self.gesture_btn.clicked.connect(self.set_gesture_mode)
        mode_layout.addWidget(self.gesture_btn)
        self.idle_btn = QPushButton("Idle Mode")
        self.idle_btn.clicked.connect(self.set_idle_mode)
        mode_layout.addWidget(self.idle_btn)
        main_layout.addWidget(mode_group)

        # Cursor Settings Group
        cursor_group = QGroupBox("Cursor Settings")
        cursor_layout = QGridLayout()
        cursor_group.setLayout(cursor_layout)
        cursor_layout.addWidget(QLabel("Speed:"), 0, 0)
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(1)
        self.speed_slider.setMaximum(10)
        self.speed_slider.setValue(5)
        self.speed_slider.valueChanged.connect(self.update_cursor_speed)
        cursor_layout.addWidget(self.speed_slider, 0, 1)
        self.speed_label = QLabel("5.0")
        cursor_layout.addWidget(self.speed_label, 0, 2)

        cursor_layout.addWidget(QLabel("Smoothing:"), 1, 0)
        self.smoothing_slider = QSlider(Qt.Horizontal)
        self.smoothing_slider.setMinimum(0)
        self.smoothing_slider.setMaximum(90)
        self.smoothing_slider.setValue(50)
        self.smoothing_slider.valueChanged.connect(self.update_cursor_smoothing)
        cursor_layout.addWidget(self.smoothing_slider, 1, 1)
        self.smoothing_label = QLabel("0.5")
        cursor_layout.addWidget(self.smoothing_label, 1, 2)

        self.calibrate_btn = QPushButton("Calibrate Sensor")
        self.calibrate_btn.clicked.connect(self.calibrate_sensor)
        cursor_layout.addWidget(self.calibrate_btn, 2, 0)
        self.calibrate_tilt_btn = QPushButton("Calibrate Tilt")
        self.calibrate_tilt_btn.clicked.connect(self.calibrate_tilt)
        cursor_layout.addWidget(self.calibrate_tilt_btn, 2, 1)
        self.calibration_label = QLabel("Not calibrated")
        cursor_layout.addWidget(self.calibration_label, 2, 2)
        main_layout.addWidget(cursor_group)

        # Gesture Control Group
        gesture_group = QGroupBox("Gesture Control")
        gesture_layout = QVBoxLayout()
        gesture_group.setLayout(gesture_layout)
        self.gesture_icon_label = QLabel("○")
        self.gesture_icon_label.setAlignment(Qt.AlignCenter)
        self.gesture_icon_label.setStyleSheet("font-size: 32px;")
        gesture_layout.addWidget(self.gesture_icon_label)
        self.gesture_status_label = QLabel("Perform a gesture")
        gesture_layout.addWidget(self.gesture_status_label)
        main_layout.addWidget(gesture_group)

        # Log Group
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout()
        log_group.setLayout(log_layout)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        main_layout.addWidget(log_group)

        # Logging handler
        text_handler = QTextEditLogger(self.log_text)
        text_handler.setLevel(logging.INFO)
        logging.getLogger().addHandler(text_handler)

        self.setLayout(main_layout)

    def set_cursor_mode(self):
        if self.wifi_handler.is_connected():
            self.wifi_handler.write("CURSOR_MODE\n")
            self.logger.info("Switched to cursor mode")

    def set_gesture_mode(self):
        if self.wifi_handler.is_connected():
            self.wifi_handler.write("GESTURE_MODE\n")
            self.logger.info("Switched to gesture mode")

    def set_idle_mode(self):
        if self.wifi_handler.is_connected():
            self.wifi_handler.write("IDLE_MODE\n")
            self.logger.info("Switched to idle mode")

    def update_cursor_speed(self):
        speed = self.speed_slider.value()
        self.speed_label.setText(f"{speed:.1f}")
        self.mouse_controller.set_cursor_speed(speed)
        self.logger.info(f"Updated cursor speed: {speed}")

    def update_cursor_smoothing(self):
        smoothing = self.smoothing_slider.value() / 100.0
        self.smoothing_label.setText(f"{smoothing:.2f}")
        self.mouse_controller.set_smoothing(smoothing)
        self.logger.info(f"Updated cursor smoothing: {smoothing}")

    def calibrate_sensor(self):
        if self.wifi_handler.is_connected():
            self.wifi_handler.write("CALIBRATE\n")
            self.calibration_label.setText("Calibrating...")
            self.logger.info("Started sensor calibration")

    def calibrate_tilt(self):
        if self.wifi_handler.is_connected():
            self.wifi_handler.write("CALIBRATE_TILT\n")
            self.calibration_label.setText("Calibrating tilt...")
            self.logger.info("Started tilt calibration")

    def toggle_connection(self):
        if self.connect_btn.text() == "Connect":
            ip = self.ip_input.text()
            if self.wifi_handler.connect(ip):
                self.status_label.setText("Connected")
                self.connect_btn.setText("Disconnect")
                self.logger.info(f"Connected to ESP32 at {ip}")
            else:
                self.status_label.setText("Connection failed")
                self.logger.error(f"Failed to connect to ESP32 at {ip}")
        else:
            if self.wifi_handler.disconnect():
                self.status_label.setText("Disconnected")
                self.connect_btn.setText("Connect")
                self.logger.info("Disconnected from ESP32")
            else:
                self.logger.error("Failed to disconnect from ESP32")

    def handle_gesture(self, gesture):
        self.gesture_status_label.setText(gesture)
        self.logger.info(f"Gesture detected: {gesture}")
        icons = {
            "UP": "↑",
            "DOWN": "↓",
            "LEFT": "←",
            "RIGHT": "→",
            "CIRCLE": "○",
            "SHAKE": "✖"
        }
        self.gesture_icon_label.setText(icons.get(gesture, "○"))

        actions = {
            "UP": lambda: pyautogui.press('volumeup'),
            "DOWN": lambda: pyautogui.press('volumedown'),
            "LEFT": lambda: pyautogui.press('prevtrack'),
            "RIGHT": lambda: pyautogui.press('nexttrack'),
            "CIRCLE": self.switch_application,
            "SHAKE": lambda: pyautogui.hotkey('ctrl', 'z')
        }
        if gesture in actions:
            actions[gesture]()

    def switch_application(self):
        try:
            pyautogui.hotkey('alt', 'tab')
            self.logger.info("Switched application")
        except Exception as e:
            self.logger.error(f"Error switching apps: {e}")

def main():
    app = QApplication(sys.argv)
    gui = AirMouseGUI()
    gui.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()