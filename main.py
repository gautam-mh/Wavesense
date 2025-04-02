import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
from mouse_controller import MouseController
from gesture_handler import GestureHandler

class AirMouseGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Air Mouse Controller (WiFi)")
        self.root.geometry("400x400")

        self.controller = MouseController()
        self.setup_logging()
        self.controller.set_calibration_callback(self.update_calibration_progress)
        self.create_widgets()

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('AirMouse.GUI')

    def create_widgets(self):
        frame = ttk.Frame(self.root, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # IP Address input
        ttk.Label(frame, text="ESP32 IP Address:").grid(row=0, column=0, padx=5, pady=5)
        self.ip_var = tk.StringVar(value="192.168.4.1")  # Default IP
        ttk.Entry(frame, textvariable=self.ip_var, width=15).grid(row=0, column=1, padx=5, pady=5)

        # Sensitivity control
        ttk.Label(frame, text="Sensitivity:").grid(row=1, column=0, padx=5, pady=5)
        self.sensitivity_scale = ttk.Scale(frame, from_=0.1, to=2.0, orient='horizontal')
        self.sensitivity_scale.set(1.0)
        self.sensitivity_scale.grid(row=1, column=1, padx=5, pady=5, sticky='ew')

        # Smoothing control
        ttk.Label(frame, text="Smoothing:").grid(row=2, column=0, padx=5, pady=5)
        self.smoothing_scale = ttk.Scale(frame, from_=0, to=0.9, orient='horizontal')
        self.smoothing_scale.set(0.5)
        self.smoothing_scale.grid(row=2, column=1, padx=5, pady=5, sticky='ew')

        # Progress bar for calibration
        self.progress_var = tk.IntVar()
        self.progress_bar = ttk.Progressbar(
            frame,
            orient='horizontal',
            length=200,
            mode='determinate',
            variable=self.progress_var
        )
        self.progress_bar.grid(row=3, column=1, padx=5, pady=5, sticky='ew')

        # Calibration button
        self.calibrate_button = ttk.Button(
            frame,
            text="Calibrate",
            command=self.calibrate_sensor
        )
        self.calibrate_button.grid(row=3, column=0, padx=5, pady=5)
        self.calibrate_button['state'] = 'disabled'

        self.calibrate_tilt_button = ttk.Button(
            frame,
            text="Calibrate Tilt",
            command=self.calibrate_tilt
        )
        self.calibrate_tilt_button.grid(row=3, column=2, padx=5, pady=5)
        self.calibrate_tilt_button['state'] = 'disabled'

        # Connect button
        self.connect_button = ttk.Button(
            frame,
            text="Connect",
            command=self.toggle_connection
        )
        self.connect_button.grid(row=4, column=0, columnspan=2, pady=10)

        # Status label
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(
            frame,
            textvariable=self.status_var
        ).grid(row=5, column=0, columnspan=2)

        # Calibration instructions
        instruction_text = (
            "Calibration Instructions:\n"
            "1. Place the sensor on a flat surface\n"
            "2. Keep it completely still\n"
            "3. Click Calibrate and wait for 1 second\n"
            "4. Progress bar will show calibration status\n"
            "5. Done when progress reaches 100%"
        )
        ttk.Label(
            frame,
            text=instruction_text,
            justify=tk.LEFT
        ).grid(row=6, column=0, columnspan=2, pady=10)

        # Calibration time label
        self.calibration_time = ttk.Label(
            frame,
            text="Calibration time: 1 second"
        )
        self.calibration_time.grid(row=7, column=0, columnspan=2, pady=5)

        mode_frame = ttk.LabelFrame(frame, text="Control Mode", padding="5")
        mode_frame.grid(row=8, column=0, columnspan=2, pady=10, sticky='ew')

        ttk.Button(
            mode_frame,
            text="Cursor Mode",
            command=self.set_cursor_mode
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            mode_frame,
            text="Gesture Mode",
            command=self.set_gesture_mode
        ).pack(side=tk.LEFT, padx=5)

    def set_cursor_mode(self):
        """Switch to cursor control mode"""
        if self.controller.wifi_handler.is_connected():
            self.controller.wifi_handler.write(b"CURSOR_MODE\n")
            self.status_var.set("Cursor Mode Active")

    def set_gesture_mode(self):
        """Switch to gesture control mode"""
        if self.controller.wifi_handler.is_connected():
            self.controller.wifi_handler.write(b"GESTURE_MODE\n")
            self.status_var.set("Gesture Mode Active")

    def update_calibration_progress(self, progress):
        """Update the calibration progress bar"""
        self.progress_var.set(progress)
        if progress == 100:
            self.status_var.set("Calibration Complete")
            self.calibrate_button['state'] = 'normal'
        else:
            self.status_var.set(f"Calibrating: {progress}%")
        self.root.update_idletasks()

    def calibrate_sensor(self):
        """Handle sensor calibration"""
        self.status_var.set("Calibrating...")
        self.calibrate_button['state'] = 'disabled'
        self.progress_var.set(0)

        def calibrate_thread():
            if self.controller.calibrate():
                self.status_var.set("Calibration Complete")
            else:
                self.status_var.set("Calibration Failed")
            self.calibrate_button['state'] = 'normal'

        threading.Thread(target=calibrate_thread, daemon=True).start()

    def calibrate_tilt(self):
        if not self.controller.wifi_handler.is_connected():
            self.status_var.set("Not connected to device")
            return

        self.status_var.set("Starting tilt calibration...")
        self.controller.wifi_handler.write(b"CALIBRATE_TILT\n")

    def toggle_connection(self):
        if self.connect_button['text'] == "Connect":
            self.start_controller()
        else:
            self.stop_controller()

    def start_controller(self):
        ip_address = self.ip_var.get()
        if not ip_address:
            self.status_var.set("Please enter an IP address!")
            return

        self.status_var.set(f"Connecting to {ip_address}...")
        if self.controller.connect(ip_address):
            self.connect_button['text'] = "Disconnect"
            self.status_var.set(f"Connected to {ip_address}")
            self.calibrate_button['state'] = 'normal'
            self.calibrate_tilt_button['state'] = 'normal'  # Enable tilt calibration

            # Start settings update loop
            self.update_settings()
        else:
            self.status_var.set("Connection failed!")

    def stop_controller(self):
        self.controller.disconnect()
        self.connect_button['text'] = "Connect"
        self.status_var.set("Disconnected")
        self.calibrate_button['state'] = 'disabled'
        self.calibrate_tilt_button['state'] = 'disabled'  # Disable tilt calibration

    def update_settings(self):
        """Update controller settings from GUI controls"""
        if self.controller.wifi_handler.is_connected():
            self.controller.set_cursor_speed(self.sensitivity_scale.get())
            self.controller.set_smoothing_factor(self.smoothing_scale.get())
            self.root.after(100, self.update_settings)
    
    def log(self, message):
        """Log a message and update status"""
        self.logger.info(message)
        self.status_var.set(message)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = AirMouseGUI()
    app.run()