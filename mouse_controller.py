import pyautogui
import logging
import time
from wifi_handler import WiFiHandler
from gesture_handler import GestureHandler

class MouseController:
    def __init__(self):
        self.logger = logging.getLogger('AirMouse.Controller')

        # Initialize all attributes
        self.cursor_speed = 5.0
        self.smoothing_factor = 0.9
        self.current_vx = 0.0
        self.current_vy = 0.0
        self.gesture_callback = None  # Initialize gesture_callback

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

        self.logger.info("MouseController initialized")
        print("MouseController initialized with speed:", self.cursor_speed)

    def set_smoothing(self, smoothing):
        """Set smoothing factor"""
        self.smoothing_factor = smoothing
        self.smoothing = smoothing  # Update both for consistency
        self.logger.info(f"Smoothing factor set to {smoothing}")

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
        """Process incoming data from ESP32 with improved gesture handling"""
        try:
            print(f"Received: {data}")  # Debug print

            # Handle cursor data
            if data.startswith("CURSOR,"):
                parts = data.split(',')
                if len(parts) == 3:
                    vx = float(parts[1])
                    vy = float(parts[2])
                    print(f"Moving cursor: {vx}, {vy}")  # Debug print
                    self.move_cursor(vx, vy)
                return

            # Handle gesture data with cooldown and priority
            if data.startswith("GESTURE,"):
                current_time = time.time()
                gesture = data.split(',')[1].strip()

                # Apply gesture-specific cooldowns
                min_cooldown = 0.3  # Base cooldown (300ms)

                # Longer cooldown for circles to prevent overlap
                if gesture == "CIRCLE":
                    min_cooldown = 0.8
                # Shorter cooldown for directional gestures
                elif gesture in ["LEFT", "RIGHT"]:
                    min_cooldown = 0.2

                # Check if we should process this gesture
                if (not hasattr(self, 'last_gesture') or
                    current_time - self.last_gesture_time > min_cooldown or
                    gesture != self.last_gesture):

                    self.last_gesture = gesture
                    self.last_gesture_time = current_time

                    # Handle different gesture types
                    if gesture == "CIRCLE":
                        print("Pure circle gesture detected")
                        pyautogui.press('right')  # Example: Next slide

                    elif gesture in ["LEFT", "RIGHT"]:
                        print(f"Tilt gesture: {gesture}")
                        distance = 30  # pixels to move
                        if gesture == "LEFT":
                            pyautogui.move(-distance, 0)
                        else:
                            pyautogui.move(distance, 0)

                    elif gesture == "SHAKE":
                        print("Shake gesture detected")
                        pyautogui.press('esc')  # Example: Exit mode

                    # Call external callback if set
                    if self.gesture_callback:
                        self.gesture_callback(data)
                return
            # Handle calibration progress
            if data.startswith("CALIBRATION_PROGRESS,"):
                progress = int(data.split(',')[1])
                print(f"Calibration progress: {progress}%")
                if self.calibration_callback:
                    self.calibration_callback(progress)
                return

            # Handle calibration completion
            if data == "CALIBRATION_COMPLETE":
                print("Calibration complete")
                self.is_calibrating = False
                if self.calibration_callback:
                    self.calibration_callback(100)  # 100% complete
                return

            # Handle tilt calibration progress
            if data.startswith("TILT_CALIBRATION_PROGRESS,"):
                progress = int(data.split(',')[1])
                print(f"Tilt calibration progress: {progress}%")
                if self.calibration_callback:
                    self.calibration_callback(progress)
                return

            # Handle tilt calibration completion
            if data == "TILT_CALIBRATION_COMPLETE":
                print("Tilt calibration complete")
                self.tilt_calibrating = False
                if self.calibration_callback:
                    self.calibration_callback(100)  # 100% complete
                return

            # Handle mode changes
            if data == "MODE_CURSOR":
                print("Switched to cursor mode")
                return

            if data == "MODE_GESTURE":
                print("Switched to gesture mode")
                return

            if data == "MODE_IDLE":
                print("Switched to idle mode")
                return

            # Handle initialization
            if data == "INIT_COMPLETE":
                print("ESP32 initialization complete")
                self.initialized = True
                return

            # Unknown data
            print(f"Unknown data: {data}")

        except Exception as e:
            self.logger.error(f"Data processing error: {e}")
            print(f"Error: {e}")

    def handle_gesture(self, gesture):
        """Handle pre-defined gestures"""
        try:
            import pyautogui

            if gesture == "UP":
                pyautogui.press('f5')
            elif gesture == "DOWN":
                pyautogui.press('esc')
            elif gesture == "LEFT":
                pyautogui.press('left')
            elif gesture == "RIGHT":
                pyautogui.press('right')
            elif gesture == "CIRCLE":
                pyautogui.hotkey('alt', 'tab')  # Switch applications
            elif gesture == "SHAKE":
                pyautogui.press('esc')  # Cancel/back action

            self.logger.info(f"Executed gesture: {gesture}")

        except Exception as e:
            self.logger.error(f"Gesture handling error: {e}")
    
    def move_cursor(self, vx, vy):
        """Move the cursor based on sensor data"""
        try:
            # Apply sensitivity
            vx *= self.cursor_speed
            vy *= self.cursor_speed

            if abs(vx) < 10.0: vx = 0
            if abs(vy) < 10.0: vy = 0
            

            # Apply smoothing
            self.current_vx = self.current_vx * self.smoothing_factor + vx * (1 - self.smoothing_factor)
            self.current_vy = self.current_vy * self.smoothing_factor + vy * (1 - self.smoothing_factor)

            if abs(self.current_vx) < 0.5:
                self.current_vx = 0
            if abs(self.current_vy) < 0.5:
                self.current_vy = 0

            # Only move if above threshold
            if abs(self.current_vx) > 0.1 or abs(self.current_vy) > 0.1:
                # Get current position
                current_x, current_y = pyautogui.position()

                # Calculate new position
                new_x = current_x + int(self.current_vx)
                new_y = current_y + int(self.current_vy)

                # Ensure cursor stays within screen boundaries
                new_x = max(0, min(new_x, self.screen_width - 1))
                new_y = max(0, min(new_y, self.screen_height - 1))

                # Move cursor
                pyautogui.moveTo(new_x, new_y)
                print(f"Moved cursor to: {new_x}, {new_y}")
        except Exception as e:
            self.logger.error(f"Error moving cursor: {e}")
            print(f"Cursor error: {e}")

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
        """Set cursor speed"""
        self.cursor_speed = speed
        self.logger.info(f"Cursor speed set to {speed}")

    def set_smoothing_factor(self, factor):
        """Set the smoothing factor"""
        self.smoothing_factor = max(0.0, min(0.95, factor))  # Clamp between 0 and 0.95
        self.smoothing = self.smoothing_factor  # Keep both in sync
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

    def set_gesture_callback(self, callback):
        """Set callback for gesture data"""
        self.gesture_callback = callback
        self.logger.info("Gesture callback set")