import serial
import serial.tools.list_ports
import logging
import time

class SerialHandler:
    def __init__(self):
        self.serial = None
        self.logger = logging.getLogger('AirMouse.Serial')

    @staticmethod
    def list_ports():
        """List all available serial ports"""
        return [port.device for port in serial.tools.list_ports.comports()]

    def connect(self, port, baudrate=115200):
        """Connect to specified serial port"""
        try:
            self.serial = serial.Serial(port, baudrate)
            self.clear_buffer()  # Clear any startup messages
            return True
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            return False

    def disconnect(self):
        """Disconnect from serial port"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            return True
        return False

    def read_line(self):
        """Read a line from serial port"""
        if self.serial and self.serial.is_open:
            try:
                return self.serial.readline().decode().strip()
            except Exception as e:
                self.logger.error(f"Read error: {e}")
        return None

    def clear_buffer(self):
        """Clear the serial buffer"""
        if self.serial and self.serial.is_open:
            try:
                # Clear input buffer
                self.serial.reset_input_buffer()
                # Clear output buffer
                self.serial.reset_output_buffer()
                # Read any remaining data
                while self.serial.in_waiting:
                    self.serial.readline()
                time.sleep(0.1)  # Small delay to ensure buffer is cleared
            except Exception as e:
                self.logger.error(f"Buffer clear error: {e}")

    def write(self, data):
        """Write data to serial port"""
        if self.serial and self.serial.is_open:
            try:
                self.serial.write(data)
                return True
            except Exception as e:
                self.logger.error(f"Write error: {e}")
        return False

    def is_connected(self):
        """Check if serial port is connected"""
        return self.serial is not None and self.serial.is_open