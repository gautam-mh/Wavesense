import logging
import pyautogui
from datetime import datetime

class GestureHandler:
    def __init__(self):
        self.logger = logging.getLogger('AirMouse.Gesture')
        self.last_gesture = None
        self.last_gesture_time = datetime.now()
        self.gesture_cooldown = 0.5  # seconds

        # Configure gesture actions
        self.gesture_actions = {
            "UP": self.handle_up,
            "DOWN": self.handle_down,
            "LEFT": self.handle_left,
            "RIGHT": self.handle_right,
            "SLIGHT_DOWN": self.handle_slight_down
        }

        self.logger.info("Gesture handler initialized")

    def process_gesture(self, gesture):
        """Process a detected gesture"""
        current_time = datetime.now()
        time_diff = (current_time - self.last_gesture_time).total_seconds()

        if time_diff < self.gesture_cooldown:
            return

        self.logger.info(f"Processing gesture: {gesture}")
        self.last_gesture = gesture
        self.last_gesture_time = current_time

        # Execute the corresponding action
        action_handler = self.gesture_actions.get(gesture)
        if action_handler:
            action_handler()
        else:
            self.logger.warning(f"Unknown gesture: {gesture}")

    # Gesture action handlers
    def handle_up(self):
        """Handle UP gesture (gesture 2 in Arduino example)"""
        self.logger.info("Executing UP gesture")
        pyautogui.press('up')

    def handle_down(self):
        """Handle DOWN gesture (gesture 1 in Arduino example)"""
        self.logger.info("Executing DOWN gesture")
        pyautogui.press('down')

    def handle_left(self):
        """Handle LEFT gesture (gesture 3 in Arduino example)"""
        self.logger.info("Executing LEFT gesture")
        pyautogui.press('left')

    def handle_right(self):
        """Handle RIGHT gesture (gesture 4 in Arduino example)"""
        self.logger.info("Executing RIGHT gesture")
        pyautogui.press('right')

    def handle_slight_down(self):
        """Handle SLIGHT_DOWN gesture (gesture 5 in Arduino example)"""
        self.logger.info("Executing SLIGHT_DOWN gesture")
        pyautogui.press('return')  # Enter key