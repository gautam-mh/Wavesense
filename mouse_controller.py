import pyautogui
import logging
import time
from serial_handler import SerialHandler
from gesture_handler import GestureHandler

class MouseController:
    def __init__(self):
        self.logger = logging.getLogger('AirMouse.Controller')
        self.serial_handler = SerialHandler()
        self.gesture_handler = GestureHandler()
        self.is_running = False
        self.is_calibrating = False
        self.initialized = False

        # Mouse control parameters
        self.sensitivity = 1.0
        self.smoothing = 0.5
        self.prev_x = 0
        self.prev_y = 0

        # Calibration callback
        self.calibration_callback = lambda x: None

        # Configure PyAutoGUI
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.001

        # Initialize state
        self.initialized = False

    def connect(self, port):
        """Connect to ESP32"""
        try:
            success = self.serial_handler.connect(port)
            if success:
                # Clear any initial data
                self.serial_handler.clear_buffer()

                # Send init check command
                self.serial_handler.write(b"INIT_CHECK\n")

                # Wait for initialization response
                timeout = time.time() + 5
                while time.time() < timeout:
                    data = self.serial_handler.read_line()
                    if data:
                        self.logger.info(f"Init data: {data}")
                        if "INIT_COMPLETE" in data:
                            self.initialized = True
                            self.logger.info("Device initialized successfully")
                            return True
                    time.sleep(0.1)

                self.logger.error("Device initialization timeout")
                self.serial_handler.disconnect()
                return False
            return False
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            return False

    def disconnect(self):
        """Disconnect from ESP32"""
        self.initialized = False
        return self.serial_handler.disconnect()

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

            # Clear any pending data
            self.serial_handler.clear_buffer()

            # Send calibration command
            self.serial_handler.serial.write(b"CALIBRATE\n")

            # Wait for calibration process
            calibration_timeout = time.time() + 5  # 5 seconds timeout
            while self.is_calibrating and time.time() < calibration_timeout:
                data = self.serial_handler.read_line()
                if data:
                    self.logger.debug(f"Calibration data: {data}")

                    if "CALIBRATION_START" in data:
                        self.logger.info("Calibration in progress...")
                    elif "CALIBRATION_PROGRESS" in data:
                        try:
                            progress = int(data.split(',')[1])
                            self.calibration_callback(progress)
                        except:
                            self.logger.error(f"Invalid progress data: {data}")
                    elif "CALIBRATION_COMPLETE" in data:
                        self.logger.info("Calibration completed")
                        self.is_calibrating = False
                        self.calibration_callback(100)
                        return True
                    elif "CALIBRATION_FAILED" in data:
                        self.logger.error("Calibration failed")
                        self.is_calibrating = False
                        return False

                time.sleep(0.01)

            if time.time() >= calibration_timeout:
                self.logger.error("Calibration timeout")
                self.is_calibrating = False
                return False

            return True
        except Exception as e:
            self.logger.error(f"Calibration error: {e}")
            self.is_calibrating = False
            return False

    def move_cursor(self, vx, vy):
        """Move the cursor based on gyroscope data"""
        try:
            # Apply smoothing
            vx = vx * (1 - self.smoothing) + self.prev_x * self.smoothing
            vy = vy * (1 - self.smoothing) + self.prev_y * self.smoothing

            # Store values for next smoothing
            self.prev_x = vx
            self.prev_y = vy

            # Apply movement threshold
            if abs(vx) < 0.05 and abs(vy) < 0.05:  # Reduced threshold for more sensitivity
                return

            # Scale by sensitivity
            vx *= self.sensitivity
            vy *= self.sensitivity

            # Get current position
            current_x, current_y = pyautogui.position()

            # Calculate new position
            new_x = current_x + vx
            new_y = current_y + vy

            # Move cursor
            pyautogui.moveTo(new_x, new_y)

        except Exception as e:
            self.logger.error(f"Error moving cursor: {e}")
    
    def process_data(self, data):
        """Process incoming data from ESP32"""
        try:
            if self.is_calibrating or not self.initialized:
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

            # Keep existing cursor control code
            if data.startswith("CURSOR,"):
                parts = data.split(',')
                if len(parts) == 3:
                    try:
                        vx = float(parts[1])
                        vy = float(parts[2])
                        self.move_cursor(vx, vy)
                    except ValueError:
                        self.logger.error("Invalid cursor data format")
                return

            # Keep other existing data handling code

        except Exception as e:
            self.logger.error(f"Data processing error: {e}")

    def start(self):
        """Start processing mouse data"""
        if not self.initialized:
            self.logger.error("Cannot start: Device not initialized")
            return

        self.is_running = True
        self.logger.info("Starting mouse control")

        while self.is_running:
            try:
                data = self.serial_handler.read_line()
                if data:
                    self.process_data(data)
            except Exception as e:
                self.logger.error(f"Read error: {e}")
            time.sleep(0.01)

    def stop(self):
        """Stop processing mouse data"""
        self.is_running = False
        self.logger.info("Stopping mouse control")