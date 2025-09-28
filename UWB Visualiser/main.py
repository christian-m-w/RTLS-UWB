import sys, os
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QHBoxLayout, QVBoxLayout, QComboBox, QPushButton, QCheckBox, QProgressBar
from PyQt6.QtCore import Qt
from serialReader import SerialReader
from csvReader import CsvReader
from tagData import TagData
from dataclasses import dataclass
import serial.tools.list_ports
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
import matplotlib.pyplot as plt

@dataclass(frozen=True)
class AnchorLocation:
    AnchorID: str
    X: float
    Y: float
    Z: float

class RtlsUwbApplication(QWidget):
    ANCHOR_LOCATIONS = set()
    TAG_DATA: TagData

    # Floor Plan Configuration
    FP_IMAGE_PATH = "./UWB Visualiser/floorplan.png"
    FP_ORIGIN_X_IN_PIXELS = 39
    FP_ORIGIN_Y_IN_PIXELS = 912
    FP_10M_IN_PIXELS = 960

    # Logging Settings
    LOGFILE_DIRECTORY = "."

    def drawPlot(self):
        img = plt.imread(self.FP_IMAGE_PATH)
        height, width, channels = img.shape
        fp_offset_x = (self.FP_ORIGIN_X_IN_PIXELS * 10) / self.FP_10M_IN_PIXELS
        fp_offset_y = ((height-self.FP_ORIGIN_Y_IN_PIXELS) * 10) / self.FP_10M_IN_PIXELS
        self.plot.imshow(img, extent=(-fp_offset_x, (width * 10) / self.FP_10M_IN_PIXELS, -fp_offset_y, (height * 10) / self.FP_10M_IN_PIXELS), alpha=0.6, zorder=-1)
        self.plot.minorticks_on()
        self.plot.grid(True, "both")

    def __init__(self):
        super().__init__()
        self.setWindowTitle("RTLS UWB Visualiser")
        mainLayout = QHBoxLayout()
   
        # Create figure plot
        fig = plt.figure(figsize=(10,10))
        self.plot = fig.add_subplot()
        self.plot.set_xlabel("X (m)")
        self.plot.set_ylabel("Y (m)")
        self.plot.set_box_aspect(1)

        self.drawPlot()
        canvas = FigureCanvasQTAgg(fig)
        mainLayout.addWidget(canvas)

        # Add the GUI components
        controlsLayout = QVBoxLayout()
        mainLayout.addLayout(controlsLayout)
        self.setLayout(mainLayout)

        self.comPort = QComboBox(self)
        for port in serial.tools.list_ports.comports():
            self.comPort.addItem(f"{port.name}")
        controlsLayout.addWidget(self.comPort)

        self.baudrate = QComboBox(self)
        self.baudrate.addItem("115200")
        controlsLayout.addWidget(self.baudrate)

        self.chk_logging = QCheckBox("Enable Logging")
        self.chk_logging.setChecked(True)
        controlsLayout.addWidget(self.chk_logging)
        
        self.btn_connect = QPushButton("Connect")
        self.btn_connect.clicked.connect(self.start_serial_connection)
        controlsLayout.addWidget(self.btn_connect)

        self.btn_disconnect = QPushButton("Disconnect")
        self.btn_disconnect.clicked.connect(self.stop_serial_connection)
        controlsLayout.addWidget(self.btn_disconnect)

        controlsLayout.addStretch()

        self.cmb_csv = QComboBox(self)
        for f_name in os.listdir(f"{self.LOGFILE_DIRECTORY}"):
            if f_name.endswith(".csv"):
                self.cmb_csv.addItem(f"{f_name}")
        controlsLayout.addWidget(self.cmb_csv)

        self.btn_replay = QPushButton("Replay")
        self.btn_replay.clicked.connect(self.start_csv_replay)
        controlsLayout.addWidget(self.btn_replay)

        self.btn_stop = QPushButton("Stop")
        self.btn_stop.clicked.connect(self.stop_csv_replay)
        controlsLayout.addWidget(self.btn_stop)

        controlsLayout.addStretch()

        self.lbl_tag = QLabel("Tag Position:")
        controlsLayout.addWidget(self.lbl_tag)
        self.lbl_tag_qf = QLabel("Tag Quality Factor:")
        controlsLayout.addWidget(self.lbl_tag_qf)

        self.prgbar = QProgressBar()
        self.prgbar.setMaximum(100)
        self.prgbar.setValue(0)
        controlsLayout.addWidget(self.prgbar)

        self.lbl_anchors = QLabel("Anchor List:")
        controlsLayout.addWidget(self.lbl_anchors)

        controlsLayout.addStretch()

    def start_csv_replay(self):      
        # Read CSV Log
        self.worker_thread = CsvReader(f"{self.LOGFILE_DIRECTORY}/{self.cmb_csv.currentText()}")
        self.worker_thread.tag_data.connect(self.on_tag_data)
        self.worker_thread.start()
    
    def stop_csv_replay(self):
        self.worker_thread.stop()
        self.worker_thread.wait()

    def start_serial_connection(self):
        # Create tag connection
        self.worker_thread = SerialReader(
            self.comPort.currentText(), 
            self.baudrate.currentText(), 
            (self.chk_logging.checkState() == Qt.CheckState.Checked))
        
        self.worker_thread.tag_data.connect(self.on_tag_data)
        self.worker_thread.start()

    def stop_serial_connection(self):
        self.worker_thread.stop()
        self.worker_thread.wait()

    def on_tag_data(self, value: TagData):
        # Update the GUI Data
        self.TAG_DATA = value
        self.updateAnchors(value.AnchorPositions)
        self.lbl_tag.setText(f"Tag Position: ({value.TagPosition.X}, {value.TagPosition.Y}, {value.TagPosition.Z})")
        self.lbl_tag_qf.setText(f"Tag Quality Factor: {value.TagPosition.QF}%")
        self.prgbar.setValue(value.TagPosition.QF)
        
        # Clear Plot
        self.plot.cla()
        self.drawPlot()
        
        # Add plot graphics
        self.drawAnchors()
        self.updateTagLocation()

        # Redraw Plot
        plt.draw()

    def updateAnchors(self, anchorPositions: TagData.AnchorPositions):
        # Update list of anchor locations
        for a in anchorPositions:
            self.ANCHOR_LOCATIONS.add(AnchorLocation(a.AnchorID, a.X, a.Y, a.Z))

    def closeEvent(self, event):
        # On window closing, disconnect all the tags
        self.worker_thread.stop()
        self.worker_thread.wait()
        app.quit()

    def updateTagLocation(self):
        if hasattr(self, 'TAG_DATA'):
            disp_pos_x = self.TAG_DATA.TagPosition.X
            disp_pos_y = self.TAG_DATA.TagPosition.Y
            self.drawTagLines()
            circle = plt.Circle((disp_pos_x,disp_pos_y), radius=0.05, color="blue", alpha=0.6)
            self.plot.add_patch(circle)
            self.plot.text(disp_pos_x, disp_pos_y, "TAG", horizontalalignment="center", verticalalignment="bottom", fontsize=6, fontweight="bold", color="black")
            self.plot.text(disp_pos_x, disp_pos_y, f"({self.TAG_DATA.TagPosition.X}, {self.TAG_DATA.TagPosition.Y})", horizontalalignment="center", verticalalignment="top", fontsize=8, color="gray")

    def drawAnchors(self):
        anchor_list_text = "Anchor List: \n"
        for a in self.ANCHOR_LOCATIONS:
            self.drawTriangle(a.X, a.Y, 0.1, "red")
            self.plot.text(a.X, a.Y, f"({a.AnchorID})", horizontalalignment="center", verticalalignment="bottom", fontsize=8, color="black")
            anchor_list_text += f"{a.AnchorID} - ({a.X}, {a.Y}, {a.Z})\n"
        self.lbl_anchors.setText(anchor_list_text)

    def drawTagLines(self):
        for a in self.TAG_DATA.AnchorPositions:
            self.plot.plot([a.X, self.TAG_DATA.TagPosition.X], [a.Y, self.TAG_DATA.TagPosition.Y], color="green", linestyle="--", linewidth=1, alpha=0.2)
            self.plot.text((a.X + self.TAG_DATA.TagPosition.X) / 2, (a.Y + self.TAG_DATA.TagPosition.Y) / 2, f"{a.MetersFromTag}", fontsize=8, color="gray")

    def drawTriangle(self, x, y, size, colour: str):
        size = size / 2
        triangle = plt.Polygon([[x + size, y - size],[x, y + size],[x - size, y - size]], color=colour)
        self.plot.add_patch(triangle)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RtlsUwbApplication()
    window.show()
    sys.exit(app.exec())
