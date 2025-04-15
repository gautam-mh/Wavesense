import tkinter as tk
from tkinter import ttk
import logging
import os
from wifi_handler import WiFiHandler
from mouse_controller import MouseController
from gesture_handler import GestureHandler
import threading
import time
from tkinter import simpledialog
import pyautogui  # For gesture actions

class AirMouseGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Air Mouse Controller (WiFi)")
        self.root.geometry("500x600")

        # Setup logging
        self.setup_logging()

        # Initialize components
        self.wifi_handler = WiFiHandler()
        self.mouse_controller = MouseController()
        self.gesture_handler = GestureHandler()

        # Set callbacks
        self.wifi_handler.set_data_callback(self.mouse_controller.process_data)
        self.gesture_handler.register_callback("GESTURE", self.handle_gesture)

        # Set gesture callback in mouse controller
        self.mouse_controller.set_gesture_callback(self.gesture_handler.process_data)

        # Create GUI
        self.create_widgets()

        # Center window
        self.center_window()

        # Update gesture callbacks
        self.setup_gesture_callbacks()

    def setup_gestures():
        gesture_handler = GestureHandler()

        # Example bindings - modify these
        gesture_handler.register_callback("UP", lambda: print("Volume up"))
        gesture_handler.register_callback("DOWN", lambda: print("Volume down"))
        gesture_handler.register_callback("CIRCLE", lambda: print("App switcher"))
        gesture_handler.register_callback("SHAKE", lambda: print("Undo action"))

        return gesture_handler
    
    def setup_gesture_callbacks(self):
        """Bind actions to all gesture types"""
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
        """Setup logging configuration"""
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

    def create_widgets(self):
        """Create GUI widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Connection frame
        connection_frame = self.create_connection_frame(main_frame)
        connection_frame.pack(fill=tk.X, pady=10)

        # Mode buttons
        mode_frame = ttk.LabelFrame(main_frame, text="Operation Mode", padding=10)
        mode_frame.pack(fill=tk.X, pady=10)

        ttk.Button(
            mode_frame,
            text="Cursor Mode",
            command=self.set_cursor_mode
        ).pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.X)

        ttk.Button(
            mode_frame,
            text="Gesture Mode",
            command=self.set_gesture_mode
        ).pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.X)

        ttk.Button(
            mode_frame,
            text="Idle Mode",
            command=self.set_idle_mode
        ).pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.X)

        # Cursor settings
        cursor_frame = self.create_cursor_settings_frame(main_frame)
        cursor_frame.pack(fill=tk.X, pady=10)

        # Gesture frame
        gesture_frame = self.create_gesture_frame(main_frame)
        gesture_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Log frame
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.log_text = tk.Text(log_frame, height=10, width=50)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Add a custom handler to redirect logs to the text widget
        text_handler = TextHandler(self.log_text)
        text_handler.setLevel(logging.INFO)
        logging.getLogger().addHandler(text_handler)
    
    def create_connection_frame(self, parent):
        """Create the connection frame"""
        frame = ttk.LabelFrame(parent, text="Connection", padding=10)

        ttk.Label(frame, text="ESP32 IP:").grid(row=0, column=0, padx=5, pady=5)

        self.ip_var = tk.StringVar(value="192.168.4.1")
        ttk.Entry(frame, textvariable=self.ip_var, width=15).grid(row=0, column=1, padx=5, pady=5)

        self.connect_button = ttk.Button(
            frame,
            text="Connect",
            command=self.toggle_connection
        )
        self.connect_button.grid(row=0, column=2, padx=5, pady=5)

        self.status_var = tk.StringVar(value="Disconnected")
        ttk.Label(frame, textvariable=self.status_var).grid(row=0, column=3, padx=5, pady=5)

        return frame

    def create_cursor_settings_frame(self, parent):
        """Create the cursor settings frame"""
        frame = ttk.LabelFrame(parent, text="Cursor Settings", padding=10)

        # Speed slider
        ttk.Label(frame, text="Speed:").grid(row=0, column=0, padx=5, pady=5)
        self.speed_var = tk.DoubleVar(value=5.0)
        speed_slider = ttk.Scale(
            frame,
            from_=1.0,
            to=10.0,
            variable=self.speed_var,
            orient=tk.HORIZONTAL,
            length=200,
            command=self.update_cursor_speed
        )
        speed_slider.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(frame, textvariable=self.speed_var).grid(row=0, column=2, padx=5, pady=5)

        # Smoothing slider
        ttk.Label(frame, text="Smoothing:").grid(row=1, column=0, padx=5, pady=5)
        self.smoothing_var = tk.DoubleVar(value=0.5)
        smoothing_slider = ttk.Scale(
            frame,
            from_=0.0,
            to=0.9,
            variable=self.smoothing_var,
            orient=tk.HORIZONTAL,
            length=200,
            command=self.update_cursor_smoothing
        )
        smoothing_slider.grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(frame, textvariable=self.smoothing_var).grid(row=1, column=2, padx=5, pady=5)

        # Calibration button
        ttk.Button(
            frame,
            text="Calibrate Sensor",
            command=self.calibrate_sensor
        ).grid(row=2, column=0, padx=5, pady=5)

        ttk.Button(
            frame,
            text="Calibrate Tilt",
            command=self.calibrate_tilt
        ).grid(row=2, column=1, padx=5, pady=5)

        self.calibration_var = tk.StringVar(value="Not calibrated")
        ttk.Label(frame, textvariable=self.calibration_var).grid(row=2, column=2, padx=5, pady=5)

        return frame

    def set_cursor_mode(self):
        """Switch to cursor mode"""
        if self.wifi_handler.is_connected():
            self.wifi_handler.write("CURSOR_MODE\n")
            self.logger.info("Switched to cursor mode")

    def set_gesture_mode(self):
        """Switch to gesture mode"""
        if self.wifi_handler.is_connected():
            self.wifi_handler.write("GESTURE_MODE\n")
            self.logger.info("Switched to gesture mode")
    
    def set_idle_mode(self):
        """Switch to idle mode"""
        if self.wifi_handler.is_connected():
            self.wifi_handler.write("IDLE_MODE\n")
            self.logger.info("Switched to idle mode")

    def create_gesture_frame(self, parent):
        """Create enhanced gesture frame"""
        frame = ttk.LabelFrame(parent, text="Gesture Control", padding=10)

        # Gesture visualization
        self.gesture_icons = {
            "UP": "↑",
            "DOWN": "↓",
            "LEFT": "←",
            "RIGHT": "→",
            "CIRCLE": "○",
            "SHAKE": "✖"
        }

        self.gesture_display = ttk.Label(
            frame,
            text="○",  # Default circle icon
            font=('Arial', 24),
            width=5
        )
        self.gesture_display.grid(row=0, column=0, columnspan=2, pady=10)

        # Status label
        self.recognized_gesture = tk.StringVar(value="Perform a gesture")
        ttk.Label(
            frame,
            textvariable=self.recognized_gesture,
            font=('Arial', 10)
        ).grid(row=1, column=0, columnspan=2)

        return frame

    def record_multiple_samples(self):
        """Record multiple samples of the current gesture"""
        gesture_name = self.gesture_name.get()
        if not gesture_name:
            self.gesture_status.set("Please enter a gesture name")
            return

        # Ask user how many samples to record
        num_samples = simpledialog.askinteger(
            "Samples",
            "How many samples to record?",
            initialvalue=5,
            minvalue=1,
            maxvalue=20
        )

        if not num_samples:
            return  # User cancelled

        # Disable buttons during recording
        self.record_button['state'] = 'disabled'
        self.record_multiple_btn['state'] = 'disabled'

        # Start recording in a separate thread
        threading.Thread(
            target=self.record_multiple_gestures_thread,
            args=(gesture_name, num_samples)
        ).start()

    def record_multiple_gestures_thread(self, gesture_name, num_samples):
        """Thread to record multiple samples of the same gesture"""
        # Switch to gesture mode
        self.wifi_handler.write("GESTURE_MODE\n")

        for i in range(num_samples):
            # Update UI
            self.gesture_status.set(f"Prepare for sample {i+1}/{num_samples}...")
            self.log(f"Recording sample {i+1}/{num_samples} for gesture '{gesture_name}'")

            # Wait for user to prepare
            time.sleep(2)

            # Start recording
            self.gesture_status.set(f"RECORDING NOW - Perform gesture {i+1}/{num_samples}!")
            self.log("RECORDING NOW - Perform the gesture!")
            self.gesture_handler.start_recording(f"{gesture_name}_{i+1}")

            # Record for 3 seconds
            time.sleep(3)

            # Stop recording
            samples = self.gesture_handler.stop_recording()

            if samples > 10:  # Ensure we have enough data points
                self.log(f"Sample {i+1} recorded successfully ({samples} samples)")
            else:
                self.log(f"Sample {i+1} failed - not enough data")
                i -= 1  # Try again

            # Wait between recordings
            time.sleep(1)

        # Update UI
        self.gesture_status.set(f"Recorded {num_samples} samples for '{gesture_name}'")
        self.log(f"Completed recording {num_samples} samples for gesture '{gesture_name}'")

        # Update the listbox
        self.update_gesture_list()

        # Switch back to idle mode
        self.wifi_handler.write("IDLE_MODE\n")

        # Re-enable buttons
        self.root.after(0, lambda: self.record_button.configure(state='normal'))
        self.root.after(0, lambda: self.record_multiple_btn.configure(state='normal'))
    
    def toggle_recording(self):
        """Start or stop recording a gesture"""
        if self.record_button['text'] == "Start Recording":
            gesture_name = self.gesture_name.get()
            if not gesture_name:
                self.gesture_status.set("Please enter a gesture name")
                return

            # Switch to gesture mode
            self.wifi_handler.write("GESTURE_MODE\n")

            # Start recording
            self.gesture_handler.start_recording(gesture_name)
            self.gesture_status.set(f"Recording gesture: {gesture_name}...")
            self.record_button['text'] = "Stop Recording"

            # Schedule a function to update the UI during recording
            self.root.after(100, self.update_recording_status)
        else:
            # Stop recording
            samples = self.gesture_handler.stop_recording()
            self.gesture_status.set(f"Recorded {samples} samples")
            self.record_button['text'] = "Start Recording"

            # Update the listbox
            self.update_gesture_list()

            # Switch back to idle mode
            self.wifi_handler.write("IDLE_MODE\n")

    def update_recording_status(self):
        """Update the UI during recording"""
        if self.record_button['text'] == "Stop Recording":
            samples = self.gesture_handler.get_current_samples()
            self.gesture_status.set(f"Recording... ({samples} samples)")
            self.root.after(100, self.update_recording_status)

    def update_gesture_list(self):
        """Update the list of recorded gestures"""
        self.gesture_listbox.delete(0, tk.END)
        for gesture in self.gesture_handler.get_gestures():
            self.gesture_listbox.insert(tk.END, gesture)

    def update_cursor_speed(self, *args):
        """Update cursor speed"""
        speed = self.speed_var.get()
        self.mouse_controller.set_cursor_speed(speed)
        self.logger.info(f"Updated cursor speed: {speed}")
    
    def update_cursor_smoothing(self, *args):
        """Update cursor smoothing"""
        smoothing = self.smoothing_var.get()
        self.mouse_controller.set_smoothing(smoothing)
        self.logger.info(f"Updated cursor smoothing: {smoothing}")
    
    def center_window(self):
        """Center the window on the screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def train_gesture_model(self):
        """Train the gesture recognition model"""
        self.gesture_status.set("Training model...")
        success = self.gesture_handler.train_model()
        if success:
            self.gesture_status.set("Model trained successfully")
        else:
            self.gesture_status.set("Failed to train model")

    def handle_gesture(self, gesture):
        """Handle all recognized gestures"""
        self.recognized_gesture.set(gesture)
        self.logger.info(f"Gesture detected: {gesture}")

        # Map gestures to actions
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
        """Switch between applications (circle gesture)"""
        try:
            import pyautogui
            pyautogui.hotkey('alt', 'tab')
            self.logger.info("Switched application")
        except Exception as e:
            self.logger.error(f"Error switching apps: {e}")
    
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
        """Calibrate the sensor"""
        if self.wifi_handler.is_connected():
            self.wifi_handler.write("CALIBRATE\n")
            self.calibration_var.set("Calibrating...")
            self.logger.info("Started sensor calibration")

    def calibrate_tilt(self):
        """Calibrate tilt"""
        if self.wifi_handler.is_connected():
            self.wifi_handler.write("CALIBRATE_TILT\n")
            self.calibration_var.set("Calibrating tilt...")
            self.logger.info("Started tilt calibration")

    def toggle_connection(self):
        """Connect or disconnect from ESP32"""
        if self.connect_button['text'] == "Connect":
            ip = self.ip_var.get()
            if self.wifi_handler.connect(ip):
                self.status_var.set("Connected")
                self.connect_button['text'] = "Disconnect"
                self.logger.info(f"Connected to ESP32 at {ip}")
            else:
                self.status_var.set("Connection failed")
                self.logger.error(f"Failed to connect to ESP32 at {ip}")
        else:
            if self.wifi_handler.disconnect():
                self.status_var.set("Disconnected")
                self.connect_button['text'] = "Connect"
                self.logger.info("Disconnected from ESP32")
            else:
                self.logger.error("Failed to disconnect from ESP32")

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
        """Run the application"""
        self.root.mainloop()

class TextHandler(logging.Handler):
    """Handler to redirect log messages to a tkinter Text widget"""
    def __init__(self, text_widget):
        logging.Handler.__init__(self)
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text_widget.configure(state='normal')
            self.text_widget.insert(tk.END, msg + '\n')
            self.text_widget.see(tk.END)
            self.text_widget.configure(state='disabled')
        self.text_widget.after(0, append)

def main():
    app = AirMouseGUI()
    app.run()

if __name__ == "__main__":
    main()