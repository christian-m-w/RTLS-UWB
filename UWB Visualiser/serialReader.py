import serial
import time
from datetime import datetime, timezone
from PyQt6.QtCore import QThread, pyqtSignal
from tagData import TagData
from utils.tagDataUtils import TagDataUtils

class SerialReader(QThread):
    tag_data = pyqtSignal(TagData, str)

    def __init__(self, PORT, BAUDRATE, ENABLE_LOGGING, LOGFILE_DIRECTORY):
        super().__init__()
        self.PORT = PORT
        self.BAUDRATE = BAUDRATE
        self.ENABLE_LOGGING = ENABLE_LOGGING
        self.LOGFILE_DIRECTORY = LOGFILE_DIRECTORY

    def run(self):
        # Create listener on serial COM port
        tag = serial.Serial(self.PORT, self.BAUDRATE, timeout=1)

        # Wait for the device to connect
        time.sleep(2)

        # Activate the location data logging with two enters and the lec command
        tag.write(b'\r')
        time.sleep(0.5)
        tag.write(b'\r')
        time.sleep(0.5)
        tag.write(b'lec\r')
        time.sleep(0.1)

        # Read the logging data and emit it or save to CSV
        self.running = True
        
        # log data to CSV - Filename format (YYYY-MM-DD-HH-MM-SS-ComPort.csv)
        if self.ENABLE_LOGGING:
            now = datetime.now(timezone.utc)
            f = open(f"{self.LOGFILE_DIRECTORY}\\{now.strftime("%Y-%m-%d-%H-%M-%S")}-{self.PORT[3]}.csv", "a")

        print(f"Running... {self.PORT} - {self.BAUDRATE} - {self.ENABLE_LOGGING}")

        self.start_time = time.time()
        try:
            while self.running:
                # Read the bytes from serial and convert to string
                line = tag.readline().decode(errors='ignore').strip()
                if not line:
                    continue
                
                # Ignore lines without telemetry
                if line.startswith("DIST") == False or "POS" not in line:
                    continue

                # parse serial data and add timestamp
                elapsed_ms = round(time.time() - self.start_time, 3)
                row = f"{elapsed_ms},{line}\n"
                tagData = TagDataUtils.serial_toTagData(self, row.split(','))

                # log parsed data to CSV
                if self.ENABLE_LOGGING:
                    f.write(f"{TagDataUtils.tagData_ToCSV(self, tagData)}\n")

                # Send the tag data signal
                self.send_tag_data(tagData, self.PORT)
        finally:
            tag.close()
            print(f"Closing serial connection on {self.PORT}...")

    def stop(self):
        self.running = False

    def send_tag_data(self, td: TagData, com_port):
        self.tag_data.emit(td, com_port)