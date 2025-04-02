import pyautogui
import logging
import time
from wifi_handler import WiFiHandler
from gesture_handler import GestureHandler

class MouseController:
    def __init__(self):
        self.logger = logging.getLogger('AirMouse.Controller')
        self.wifi_handler = WiFiHandler()
        self.gesture_handler = GestureHandler()
        self.is_running = False
        self.is_calibrating = False
        self.initialized = False

        # Mouse control parameters
        self.sensitivity = 1.0
        self.smoothing = 0.5
        self.prev_x = 0
        self.prev_y = 0

        # Screen boundaries
        self.screen_width, self.screen_height = pyautogui.size()

        # Calibration callback
        self.calibration_callback = lambda x: None

        # Tilt calibration
        self.tilt_calibrating = False

        # Configure PyAutoGUI
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.001

    def connect(self, ip_address, port=80):
        """Connect to ESP32 via WiFi"""
        try:
            success = self.wifi_handler.connect(ip_address, port)
            if success:
                # Set data callback
                self.wifi_handler.set_data_callback(self.process_data)

                # Send init check command
                self.wifi_handler.write(b"INIT_CHECK\n")

                # Wait for initialization response
                timeout = time.time() + 5
                while time.time() < timeout and not self.initialized:
                    time.sleep(0.1)

                if not self.initialized:
                    self.logger.error("Device initialization timeout")
                    self.wifi_handler.disconnect()
                    return False

                return True
            return False
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            return False

    def disconnect(self):
        """Disconnect from ESP32"""
        self.initialized = False
        return self.wifi_handler.disconnect()

    def set_calibration_callback(self, callback):
        """Set the callback for calibration progress updates"""
        self.calibration_callback = callback

    def calibrate(self):
        """Calibrate the sensor"""
        try:
            if not self.initialized:
                self.logger.error("Device not initialized")
                return False

            self.is_calibrating = True
            self.logger.info("Starting calibration...")

            # Send calibration command
            self.wifi_handler.write(b"CALIBRATE\n")

            # Wait for calibration process (handled by process_data)
            calibration_timeout = time.time() + 10  # 10 seconds timeout
            while self.is_calibrating and time.time() < calibration_timeout:
                time.sleep(0.1)

            if time.time() >= calibration_timeout:
                self.logger.error("Calibration timeout")
                self.is_calibrating = False
                return False

            return True
        except Exception as e:
            self.logger.error(f"Calibration error: {e}")
            self.is_calibrating = False
            return False

    def calibrate_tilt(self):
        """Calibrate the tilt sensor"""
        try:
            if not self.initialized:
                self.logger.error("Device not initialized")
                return False

            self.tilt_calibrating = True
            self.logger.info("Starting tilt calibration...")

            # Send tilt calibration command
            self.wifi_handler.write(b"CALIBRATE_TILT\n")

            # Wait for calibration process (handled by process_data)
            calibration_timeout = time.time() + 10  # 10 seconds timeout
            while self.tilt_calibrating and time.time() < calibration_timeout:
                time.sleep(0.1)

            if time.time() >= calibration_timeout:
                self.logger.error("Tilt calibration timeout")
                self.tilt_calibrating = False
                return False

            return True
        except Exception as e:
            self.logger.error(f"Tilt calibration error: {e}")
            self.tilt_calibrating = False
            return False

    def process_data(self, data):
        """Process incoming data from ESP32"""
        try:
            # Debug output to help troubleshoot
            self.logger.debug(f"Received data: {data}")

            # Handle initialization
            if data == "INIT_COMPLETE":
                self.initialized = True
                self.logger.info("Device initialized successfully")
                return

            # Handle calibration data
            if "CALIBRATION_START" in data:
                self.logger.info("Calibration in progress...")
                if self.calibration_callback:
                    self.calibration_callback(0)
                return

            if "TILT_CALIBRATION_START" in data:
                self.logger.info("Tilt calibration in progress...")
                self.tilt_calibrating = True
                if self.calibration_callback:
                    self.calibration_callback(0)
                return

            if "CALIBRATION_PROGRESS" in data:
                try:
                    progress = int(data.split(',')[1])
                    if self.calibration_callback:
                        self.calibration_callback(progress)
                except:
                    self.logger.error(f"Invalid progress data: {data}")
                return

            if "CALIBRATION_COMPLETE" in data:
                self.logger.info("Calibration completed")
                self.is_calibrating = False
                if self.calibration_callback:
                    self.calibration_callback(100)
                return

            if "TILT_CALIBRATION_COMPLETE" in data:
                self.logger.info("Tilt calibration completed")
                self.tilt_calibrating = False
                if self.calibration_callback:
                    self.calibration_callback(100)
                return

            if "CALIBRATION_FAILED" in data:
                self.logger.error("Calibration failed")
                self.is_calibrating = False
                self.tilt_calibrating = False
                if self.calibration_callback:
                    self.calibration_callback(-1)  # Negative value indicates failure
                return

            # Handle mode change confirmations
            if data == "MODE_GESTURE":
                self.logger.info("Device switched to gesture mode")
                return

            if data == "MODE_CURSOR":
                self.logger.info("Device switched to cursor mode")
                return

            # Handle gesture data
            if data.startswith("GESTURE,"):
                gesture = data.split(',')[1].strip()
                self.logger.info(f"Received gesture: {gesture}")
                self.gesture_handler.process_gesture(gesture)
                return

            # Handle cursor data
            if data.startswith("CURSOR,"):
                parts = data.split(',')
                if len(parts) >= 3:  # Changed from == 3 to >= 3 for more flexibility
                    try:
                        vx = float(parts[1])
                        vy = float(parts[2])
                        self.move_cursor(vx, vy)
                    except ValueError:
                        self.logger.error(f"Invalid cursor data format: {data}")
                return

            # Handle cursor centered command
            if data == "CURSOR_CENTERED":
                self.center_cursor()
                return

        except Exception as e:
            self.logger.error(f"Data processing error: {e}")

    def move_cursor(self, vx, vy):
        """Move the cursor based on tilt angles"""
        try:
            # Apply smoothing
            vx = vx * (1 - self.smoothing) + self.prev_x * self.smoothing
            vy = vy * (1 - self.smoothing) + self.prev_y * self.smoothing

            # Store values for next smoothing
            self.prev_x = vx
            self.prev_y = vy

            # Apply movement threshold - lower threshold for tilt control
            if abs(vx) < 0.05 and abs(vy) < 0.05:
                return

            # Scale by sensitivity
            vx *= self.sensitivity
            vy *= self.sensitivity

            # Get current position
            current_x, current_y = pyautogui.position()

            # Calculate new position
            new_x = current_x + vx
            new_y = current_y + vy

            # Ensure cursor stays within screen bounds
            new_x = max(0, min(new_x, self.screen_width - 1))
            new_y = max(0, min(new_y, self.screen_height - 1))

            # Move cursor
            pyautogui.moveTo(new_x, new_y)

        except Exception as e:
            self.logger.error(f"Error moving cursor: {e}")

    def center_cursor(self):
        """Center the cursor on the screen"""
        try:
            pyautogui.moveTo(self.screen_width // 2, self.screen_height // 2)
            self.logger.info("Cursor centered")
        except Exception as e:
            self.logger.error(f"Error centering cursor: {e}")

    def set_initialized(self, value):
        """Set the initialized state"""
        self.initialized = value

    def set_cursor_speed(self, speed):
        """Set the cursor speed"""
        self.sensitivity = speed
        self.logger.info(f"Cursor speed set to: {speed}")

    def set_smoothing_factor(self, factor):
        """Set the smoothing factor"""
        self.smoothing = max(0.0, min(0.95, factor))  # Clamp between 0 and 0.95
        self.logger.info(f"Smoothing factor set to: {factor}")

    def set_cursor_mode(self):
        """Switch to cursor mode"""
        if not self.initialized:
            self.logger.error("Device not initialized")
            return False

        self.wifi_handler.write(b"CURSOR_MODE\n")
        return True

    def set_gesture_mode(self):
        """Switch to gesture mode"""
        if not self.initialized:
            self.logger.error("Device not initialized")
            return False

        self.wifi_handler.write(b"GESTURE_MODE\n")
        return True