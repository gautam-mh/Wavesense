import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
from mouse_controller import MouseController
from serial_handler import SerialHandler
from gesture_handler import GestureHandler

class AirMouseGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Air Mouse Controller")
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

        # Port selection
        ttk.Label(frame, text="Select Port:").grid(row=0, column=0, padx=5, pady=5)
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(frame, textvariable=self.port_var)
        self.refresh_ports()
        self.port_combo.grid(row=0, column=1, padx=5, pady=5)

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

    def refresh_ports(self):
        ports = SerialHandler.list_ports()
        self.port_combo['values'] = ports
        if ports and not self.port_var.get():
            self.port_combo.set(ports[0])

    def set_cursor_mode(self):
        """Switch to cursor control mode"""
        if self.controller.serial_handler.is_connected():
            self.controller.serial_handler.write(b"CURSOR_MODE\n")
            self.status_var.set("Cursor Mode Active")

    def set_gesture_mode(self):
        """Switch to gesture control mode"""
        if self.controller.serial_handler.is_connected():
            self.controller.serial_handler.write(b"GESTURE_MODE\n")
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

    def toggle_connection(self):
        if self.connect_button['text'] == "Connect":
            self.start_controller()
        else:
            self.stop_controller()

    def start_controller(self):
        if not self.port_var.get():
            self.status_var.set("Please select a port!")
            return

        if self.controller.connect(self.port_var.get()):
            self.connect_button['text'] = "Disconnect"
            self.status_var.set("Connected")
            self.port_combo['state'] = 'disabled'
            self.calibrate_button['state'] = 'normal'

            # Start controller in separate thread
            threading.Thread(target=self.controller.start, daemon=True).start()

            # Start settings update loop
            self.update_settings()
        else:
            self.status_var.set("Connection failed!")

    def stop_controller(self):
        self.controller.stop()
        self.controller.disconnect()
        self.connect_button['text'] = "Connect"
        self.status_var.set("Disconnected")
        self.port_combo['state'] = 'normal'
        self.calibrate_button['state'] = 'disabled'

    def update_settings(self):
        """Update controller settings from GUI controls"""
        if self.controller.is_running:
            self.controller.sensitivity = self.sensitivity_scale.get()
            self.controller.smoothing = self.smoothing_scale.get()
            self.root.after(100, self.update_settings)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = AirMouseGUI()
    app.run()