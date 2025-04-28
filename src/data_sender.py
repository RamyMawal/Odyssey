from PyQt6.QtCore import QRunnable, QMutex
import serial

# Create a global mutex for serial port access
serial_mutex = QMutex()

class SendDataTask(QRunnable):
    def __init__(self, port, baudrate, x, y, rot, xt, yt):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.x = x
        self.y = y
        self.rot = rot
        self.xt = xt
        self.yt = yt

    def run(self):
        """Send data to the ESP via the serial port."""
        serial_mutex.lock()  # Lock the mutex before accessing the serial port
        try:
            with serial.Serial(self.port, self.baudrate, timeout=1) as ser:
                message = f"1,{self.x:.3f},{self.y:.3f},{self.rot:.3f},{self.xt:.3f},{self.yt:.3f}\n"
                ser.write(message.encode('utf-8'))
                print(f"Sent: {message.strip()}")
        except serial.SerialException as e:
            print(f"Serial error: {e}")
        finally:
            serial_mutex.unlock()  # Unlock the mutex after the operation