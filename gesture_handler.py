import logging
from datetime import datetime

class GestureHandler:
    def __init__(self):
        self.logger = logging.getLogger('GestureHandler')
        self.callbacks = {}

    def register_callback(self, gesture_name, callback):
        """Register a callback function for a specific gesture"""
        self.callbacks[gesture_name] = callback
        self.logger.info(f"Registered callback for gesture: {gesture_name}")

    def process_data(self, data):
        """Process incoming gesture data"""
        try:
            if data.startswith("GESTURE,"):
                gesture = data.split(",")[1].strip()
                self.logger.info(f"Detected gesture: {gesture}")

                # Check if callback exists before executing
                if gesture in self.callbacks:
                    self.callbacks[gesture]()
                else:
                    self.logger.warning(f"No callback registered for gesture: {gesture}")

        except Exception as e:
            self.logger.error(f"Error processing gesture: {str(e)}")