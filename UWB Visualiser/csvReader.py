import serial, os, csv
import time, random
from datetime import datetime, timezone
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from tagData import TagData, AnchorPosition, TagPosition

class CsvReader(QThread):
    tag_data = pyqtSignal(TagData)

    def __init__(self, CSV_FILE):
        super().__init__()
        self.CSV_FILE = CSV_FILE

    def run(self):
        # Read the logging data and emit it or save to CSV
        self.running = True
        i = 0
        
        # Load CSV file
        if not os.path.exists(self.CSV_FILE):
            print(f"File not found: {self.CSV_FILE}")
            return
        
        with open(self.CSV_FILE, newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if self.running is False:
                    continue
                
                try:
                    if row[1] != "DIST":
                        continue

                    # Send the tag data signal
                    self.send_tag_data(row)
                    
                    time.sleep(0.1)
                except ValueError as e:
                    print(f"Skipping row due to error: {e}")
                    continue

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