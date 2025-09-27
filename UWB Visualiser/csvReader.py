import os, csv
import time
from PyQt6.QtCore import QThread, pyqtSignal
from tagData import TagData
from utils.tagDataUtils import TagDataUtils

class CsvReader(QThread):
    tag_data = pyqtSignal(TagData)

    def __init__(self, CSV_FILE):
        super().__init__()
        self.CSV_FILE = CSV_FILE

    def run(self):
        # Read the logging data and emit it or save to CSV
        self.running = True
        
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
                    # Send the tag data signal
                    tagData = TagDataUtils.csv_toTagData(self, row)
                    self.send_tag_data(tagData)
                    
                    time.sleep(0.1)
                except ValueError as e:
                    print(f"Skipping row due to error: {e}")
                    continue

    def stop(self):
        self.running = False

    def send_tag_data(self, td: TagData):
        self.tag_data.emit(td)