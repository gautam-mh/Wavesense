import socket
import logging
import time
import threading

class WiFiHandler:
    def __init__(self):
        self.socket = None
        self.client = None
        self.logger = logging.getLogger('AirMouse.WiFi')
        self.connected = False
        self.buffer = ""
        self.read_thread = None
        self.running = False
        self.data_callback = None
        self._lock = threading.Lock()  # Thread safety lock

    def connect(self, ip_address, port=80):
        """Connect to ESP32 via WiFi"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Set timeout and keepalive
            self.socket.settimeout(5.0)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

            self.socket.connect((ip_address, port))
            self.connected = True
            self.logger.info(f"Connected to {ip_address}:{port}")

            # Start read thread
            self.running = True
            self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.read_thread.start()

            return True
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            return False

    def disconnect(self):
        """Disconnect from ESP32"""
        self.running = False
        if self.read_thread:
            self.read_thread.join(timeout=1.0)

        if self.socket:
            try:
                self.socket.close()
                self.logger.info("Disconnected")
            except Exception as e:
                self.logger.error(f"Disconnect error: {e}")

        self.connected = False
        return True

    def write(self, data):
        """Write data to ESP32"""
        if not self.connected:
            return False

        try:
            if isinstance(data, str):
                data = data.encode('utf-8')

            with self._lock:  # Thread-safe write
                self.socket.sendall(data)
            return True
        except Exception as e:
            self.logger.error(f"Write error: {e}")
            self.connected = False
            return False

    def _read_loop(self):
        """Background thread to read data"""
        while self.running and self.connected:
            try:
                data = self.socket.recv(1024)
                if not data:
                    self.logger.warning("Connection closed by ESP32")
                    self.connected = False
                    break

                # Improved decoding with error handling
                try:
                    text = data.decode('utf-8').replace('\r', '')
                except UnicodeDecodeError:
                    self.logger.warning("Invalid UTF-8 data received")
                    continue

                lines = text.split('\n')

                # Handle incomplete lines from previous reads
                if self.buffer:
                    lines[0] = self.buffer + lines[0]
                    self.buffer = ""

                # Process complete lines
                for i in range(len(lines) - 1):
                    line = lines[i].strip()
                    if line and self.data_callback:
                        self.data_callback(line)

                # Save incomplete last line
                if lines[-1]:
                    self.buffer = lines[-1]

            except socket.timeout:
                continue
            except Exception as e:
                self.logger.error(f"Read error: {e}")
                self.connected = False
                break

            time.sleep(0.01)

    def debug_raw_data(self, duration=10):
        """Log raw incoming data for debugging"""
        start = time.time()
        while time.time() - start < duration and self.connected:
            try:
                with self._lock:
                    data = self.socket.recv(1024)
                    print(f"RAW: {data}")  # Check if CURSOR,.* messages appear
            except socket.timeout:
                print("No data received for 1s")
            except Exception as e:
                print(f"Debug error: {e}")
                break
            time.sleep(0.1)

    def set_data_callback(self, callback):
        """Set callback for received data"""
        self.data_callback = callback

    def is_connected(self):
        """Check if connected to ESP32"""
        return self.connected
    
    def debug_raw_data(self, duration=10):
        """Log raw incoming data for debugging"""
        start = time.time()
        while time.time() - start < duration:
            try:
                data = self.socket.recv(1024)
                print(f"RAW: {data}")  # Check if CURSOR,.* messages appear
            except socket.timeout:
                print("No data received for 1s")
            time.sleep(0.1)