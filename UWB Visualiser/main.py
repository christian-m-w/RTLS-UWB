import sys, os, time
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QHBoxLayout, QVBoxLayout, QComboBox, QPushButton, QCheckBox, QProgressBar
from PyQt6.QtCore import Qt, QTimer
from serialReader import SerialReader
from csvReader import CsvReader
from tagData import TagData
from dataclasses import dataclass
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
import matplotlib.pyplot as plt
from guiControls import guiControls

@dataclass(frozen=True)
class AnchorLocation:
    AnchorID: str
    X: float
    Y: float
    Z: float

class RtlsUwbApplication(QWidget):
    REDRAW_TIMER = QTimer()
    ANCHOR_LOCATIONS = set()
    TAGS = {}
    QTHREADS = {} 

    # Floor Plan Configuration
    FP_IMAGE_PATH = "./UWB Visualiser/floorplan.png"
    FP_ORIGIN_X_IN_PIXELS = 39
    FP_ORIGIN_Y_IN_PIXELS = 912
    FP_10M_IN_PIXELS = 960
    
    # Logging Settings
    LOGFILE_DIRECTORY = "."

    # APPLICATION CONFIG
    PLOT_UPDATE_FREQUENCY_MS = 10
    ORIGIN_COLOUR = "red"
    ANCHOR_COLOUR = "red"

    def UpdateQWidgetColour(self, type, name):
       cmb = self.findChild(type, f"{name}")
       cmb_text = cmb.currentText()
       cmb.setStyleSheet(f"QWidget {{background-color: {cmb_text};}}")

    def update_fp(self):
        x = self.findChild(QLineEdit, f"fpOriginX").text()
        y = self.findChild(QLineEdit, f"fpOriginY").text()
        scale = self.findChild(QLineEdit, f"fp10m").text()
        self.FP_ORIGIN_X_IN_PIXELS = int(x)
        self.FP_ORIGIN_Y_IN_PIXELS = int(y)
        self.FP_10M_IN_PIXELS = int(scale)
        self.redraw_plot()

    def drawPlot(self):
        img = plt.imread(self.FP_IMAGE_PATH)
        height, width, channels = img.shape
        fp_offset_x = (self.FP_ORIGIN_X_IN_PIXELS * 10) / self.FP_10M_IN_PIXELS
        fp_offset_y = ((height-self.FP_ORIGIN_Y_IN_PIXELS) * 10) / self.FP_10M_IN_PIXELS
        self.plot.imshow(img, extent=(-fp_offset_x, (width * 10) / self.FP_10M_IN_PIXELS, -fp_offset_y, (height * 10) / self.FP_10M_IN_PIXELS), alpha=0.6, zorder=-1)
        self.plot.minorticks_on()
        self.plot.grid(True, "both")
        self.plot.set_xlabel("X (m)")
        self.plot.set_ylabel("Y (m)")
        self.plot.set_box_aspect(1)
        self.drawSquare(0, 0, 0.1, self.ORIGIN_COLOUR)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("RTLS UWB Visualiser")
        mainLayout = QHBoxLayout()
   
        # Create figure plot
        fig = plt.figure(figsize=(10,10))
        self.plot = fig.add_subplot()

        self.drawPlot()
        canvas = FigureCanvasQTAgg(fig)
        mainLayout.addWidget(canvas)

        # Add the GUI components
        controlsLayout = guiControls.CreateControlsLayout(self)
        mainLayout.addLayout(controlsLayout)
        self.setLayout(mainLayout)

    def start_timer(self):
        if self.REDRAW_TIMER.isActive():
            return
        self.REDRAW_TIMER.timeout.connect(self.redraw_plot)
        self.REDRAW_TIMER.start(self.PLOT_UPDATE_FREQUENCY_MS)
    
    def stop_timer(self):
        self.REDRAW_TIMER.stop()

    def start_csv_replay(self, index):
        self.start_timer()

        # Read CSV Log
        fName = self.findChild(QComboBox, f"cmb_csv_{index}").currentText()       
        self.QTHREADS.update({index: CsvReader(f"{self.LOGFILE_DIRECTORY}/{fName}")})
        self.QTHREADS[index].tag_data.connect(self.on_tag_data)
        self.QTHREADS[index].start()
    
    def stop_csv_replay(self, index):
        self.QTHREADS[index].stop()
        self.QTHREADS[index].wait()

    def start_serial_connection(self, com_port):
        self.findChild(QPushButton, f"btn_connect_{com_port}").setHidden(True)
        self.findChild(QPushButton, f"btn_disconnect_{com_port}").setHidden(False)
        baudrate = self.findChild(QLineEdit, f"baudrate_{com_port}")
        baudrate.setEnabled(False)
        chk_logging = self.findChild(QCheckBox, f"chk_logging_{com_port}")
        chk_logging.setEnabled(False)

        # Create tag connection
        self.worker_thread = SerialReader(com_port, baudrate.text(), (chk_logging.checkState() == Qt.CheckState.Checked))
        self.worker_thread.tag_data.connect(self.on_tag_data)
        self.worker_thread.start()

    def stop_serial_connection(self, com_port):
        self.worker_thread.stop()
        self.findChild(QPushButton, f"btn_disconnect_{com_port}").setHidden(True)

        self.worker_thread.wait()
        self.findChild(QPushButton, f"btn_connect_{com_port}").setHidden(False)
        self.findChild(QLineEdit, f"baudrate_{com_port}").setEnabled(True)
        self.findChild(QCheckBox, f"chk_logging_{com_port}").setEnabled(True)

    def on_tag_data(self, value: TagData, comPort):
        # Update the GUI Data
        self.TAGS[comPort] = value
        self.updateAnchors(value.AnchorPositions)
        self.lbl_tag.setText(f"Tag Position: ({value.TagPosition.X}, {value.TagPosition.Y}, {value.TagPosition.Z})")
        self.lbl_tag_qf.setText(f"Tag Quality Factor: {value.TagPosition.QF}%")
        self.prgbar.setValue(value.TagPosition.QF)
        
    def redraw_plot(self):
        # Clear Plot
        self.plot.cla()
        self.drawPlot()
    
        # Add plot graphics
        self.drawAnchors()

        for comPort in self.TAGS.keys():
            self.updateTagLocation(comPort, "blue")

        # Redraw Plot
        plt.draw()

    def updateAnchors(self, anchorPositions: TagData.AnchorPositions):
        # Update list of anchor locations
        for a in anchorPositions:
            self.ANCHOR_LOCATIONS.add(AnchorLocation(a.AnchorID, a.X, a.Y, a.Z))

    def closeEvent(self, event):
        # On window closing, disconnect all the tags
        for thread in self.QTHREADS.values():
            try:
                thread.stop()
                thread.wait()
            except ValueError as e:
                print(f"Skipping thread due to error: {e}")
                continue
        app.quit()

    def updateTagLocation(self, comPort, colour):
        if comPort in self.TAGS:
            self.drawTag(comPort, self.TAGS[comPort].TagPosition.X, self.TAGS[comPort].TagPosition.Y, f"TAG-{comPort}", colour)

    def drawTag(self, comPort, x, y, name, colour):
        self.drawTagLines(comPort, x, y)
        circle = plt.Circle((x, y), radius=0.05, color=colour, alpha=0.6)
        self.plot.add_patch(circle)
        self.plot.text(x, y, f"{name}", horizontalalignment="center", verticalalignment="bottom", fontsize=6, fontweight="bold", color="black")
        self.plot.text(x, y, f"({x}, {y})", horizontalalignment="center", verticalalignment="top", fontsize=8, color="gray")

    def drawAnchors(self):
        anchor_list_text = "Anchor List: \n"
        for a in self.ANCHOR_LOCATIONS:
            self.drawTriangle(a.X, a.Y, 0.1, self.ANCHOR_COLOUR)
            self.plot.text(a.X, a.Y, f"({a.AnchorID})", horizontalalignment="center", verticalalignment="bottom", fontsize=8, color="black")
            anchor_list_text += f"{a.AnchorID} - ({a.X}, {a.Y}, {a.Z})\n"
        self.lbl_anchors.setText(anchor_list_text)

    def drawTagLines(self, comPort, x, y):
        for a in self.TAGS[comPort].AnchorPositions:
            self.plot.plot([a.X, x], [a.Y, y], color="green", linestyle="--", linewidth=1, alpha=0.2)
            self.plot.text((a.X + x) / 2, (a.Y + y) / 2, f"{a.MetersFromTag}", fontsize=8, color="gray")

    def drawTriangle(self, x, y, size, colour: str):
        size = size / 2
        triangle = plt.Polygon([[x + size, y - size],[x, y + size],[x - size, y - size]], color=colour)
        self.plot.add_patch(triangle)

    def drawSquare(self, x, y, size, colour: str):
        offset = size / 2
        square = plt.Rectangle([x - offset, y - offset], size, size, color=colour)
        self.plot.add_patch(square)
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RtlsUwbApplication()
    window.show()
    sys.exit(app.exec())
