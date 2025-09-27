import serial, os
import time, random
from datetime import datetime, timezone
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from tagData import TagData, AnchorPosition, TagPosition

class SerialReader(QThread):
    tag_data = pyqtSignal(TagData)

    def __init__(self, PORT, BAUDRATE, ENABLE_LOGGING):
        super().__init__()
        self.PORT = PORT
        self.BAUDRATE = BAUDRATE
        self.ENABLE_LOGGING = ENABLE_LOGGING

    def run(self):
        # Create listener on serial COM port
        tag = serial.Serial(self.PORT, self.BAUDRATE, timeout=1)

        # Wait for the device to connect
        time.sleep(2)

        # Activate the location data logging with two enters and the lec command
        tag.write(b'\r')
        time.sleep(0.1)
        tag.write(b'\r')
        time.sleep(0.5)
        tag.write(b'lec\r')

        # Read the logging data and emit it or save to CSV
        self.running = True
        i = 0
        
        # log data to CSV
        if self.ENABLE_LOGGING:
            cwd = os.getcwd()
            f = open(f"{cwd}\log-{time.time()}.csv", "a")

        print(f"Running... {self.PORT} - {self.BAUDRATE} - {self.ENABLE_LOGGING}")

        try:
            while self.running:
                # Read the bytes from serial and convert to string
                line = tag.readline().decode(errors='ignore').strip()
                if not line:
                    continue

                if line.startswith("DIST") == False:
                    continue

                now = datetime.now(timezone.utc)
                iso_timestamp = now.isoformat(timespec='microseconds')

                # log data to CSV
                if self.ENABLE_LOGGING:
                    f.write(f"{iso_timestamp},{line}\n")

                # Send the tag data signal
                data = line.split(',')
                print(f"{iso_timestamp},{line}")

                i = i + 1
                row = f"{iso_timestamp},{line}\n"
                
                self.send_tag_data(row.split(','))
                time.sleep(0.1)
        finally:
            tag.close()
            print(f"Closing serial connection on {self.PORT}...")

    def stop(self):
        self.running = False

    def send_tag_data(self, row):
        t = TagData()
        t.TimeStamp = row[0]

        # AN0,4818,0.65,2.49,2.10,1.93
        t.AnchorPositions = []
        t.AnchorPositions.append(AnchorPosition(row[4], float(row[5]), float(row[6]), float(row[7]), float(row[8])))
        t.AnchorPositions.append(AnchorPosition(row[10], float(row[11]), float(row[12]), float(row[13]), float(row[14])))
        t.AnchorPositions.append(AnchorPosition(row[16], float(row[17]), float(row[18]), float(row[19]), float(row[20])))

        # POS,1.83,3.33,2.16,47
        if row[2] == "4": # Check number of anchors in position calculation (3 or 4)
            t.AnchorPositions.append(AnchorPosition(row[22], float(row[23]), float(row[24]), float(row[25]), float(row[26])))
            t.TagPosition = TagPosition(float(row[28]), float(row[29]), float(row[30]), int(row[31]))
        else:
            t.TagPosition = TagPosition(float(row[22]), float(row[23]), float(row[24]), int(row[25]))

        self.tag_data.emit(t)