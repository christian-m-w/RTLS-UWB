import sys, json
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QHBoxLayout, QComboBox, QPushButton, QCheckBox, QProgressBar, QFileDialog
from PyQt6.QtCore import Qt, QTimer
from serialReader import SerialReader
import serial.tools.list_ports
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
    TAG_COLOURS = {}
    QTHREADS = {} 

    # Floor Plan Configuration
    FP_IMAGE_PATH = "./floorplans/default-floorplan.png"
    FP_ORIGIN_X_IN_PIXELS = 10
    FP_ORIGIN_Y_IN_PIXELS = 310
    FP_10M_IN_PIXELS = 1000
    
    # APPLICATION CONFIG
    LOGFILE_DIRECTORY = "./logs"
    CONFIG_DIRECTORY = "./configurations"
    PLOT_UPDATE_FREQUENCY_MS = 10
    ORIGIN_COLOUR = "red"
    ANCHOR_COLOUR = "red"
    COLOURS = ["lime", "cyan", "yellow", "orange", "mediumpurple","dodgerblue","tomato"]

    def reset_data(self):
        # Stop the visualisation and clear the tag/anchor data
        self.stop_timer()
        self.ANCHOR_LOCATIONS = set()
        self.TAGS = {}
        self.TAG_COLOURS = {}
        self.QTHREADS = {}
        self.redraw_plot()

    def search_com_ports(self):
        # Update the serial COM port dropdowns
        for index in range(1, 5):
            comPort = self.findChild(QComboBox, f"comPort_{index}")
            comPort.clear() # Removes all the items in the combobox
            for port in serial.tools.list_ports.comports():
                comPort.addItem(f"{port.name}")
    
    def LoadConfig(self):
        config_file = self.findChild(QComboBox, f"cmb_configFile").currentText()
        try:
            with open(f"{self.CONFIG_DIRECTORY}/{config_file}", 'r') as file:
                data = json.load(file)
                self.findChild(QLineEdit, f"fp_filePath").setText(data['FP_IMAGE_PATH'])
                self.findChild(QLineEdit, f"fpOriginX").setText(data['FP_ORIGIN_X_IN_PIXELS'])
                self.findChild(QLineEdit, f"fpOriginY").setText(data['FP_ORIGIN_Y_IN_PIXELS'])
                self.findChild(QLineEdit, f"fp10m").setText(data['FP_10M_IN_PIXELS'])
        except FileNotFoundError:
            print("File not found")
    
    def OpenFileDialog(self):
        fName, _ = QFileDialog.getOpenFileName(window, "Select File", "", "All Files (*)")
        if fName:
            self.findChild(QLineEdit, f"fp_filePath").setText(fName)

    def UpdateQWidgetColour(self, type, name):
        cmb = self.findChild(type, f"{name}")
        cmb_text = cmb.currentText()
        cmb.setStyleSheet(f"QWidget {{background-color: {cmb_text};}}")

    def update_fp(self):
        # Read floor plan configuration from GUI 
        self.FP_IMAGE_PATH = self.findChild(QLineEdit, f"fp_filePath").text()
        self.FP_ORIGIN_X_IN_PIXELS = int(self.findChild(QLineEdit, f"fpOriginX").text())
        self.FP_ORIGIN_Y_IN_PIXELS = int(self.findChild(QLineEdit, f"fpOriginY").text())
        self.FP_10M_IN_PIXELS = int(self.findChild(QLineEdit, f"fp10m").text())
        self.redraw_plot()

    def drawPlot(self):
        img = plt.imread(self.FP_IMAGE_PATH)
        height, width, channels = img.shape
        fp_offset_x = (self.FP_ORIGIN_X_IN_PIXELS * 10) / self.FP_10M_IN_PIXELS
        fp_offset_y = ((height-self.FP_ORIGIN_Y_IN_PIXELS) * 10) / self.FP_10M_IN_PIXELS
        self.plot.imshow(img, extent=(-fp_offset_x, ((width * 10) / self.FP_10M_IN_PIXELS)-fp_offset_x, -fp_offset_y, ((height * 10) / self.FP_10M_IN_PIXELS)-fp_offset_y), alpha=0.6, zorder=-1)
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
        self.QTHREADS.update({f"csv-{index}": CsvReader(f"{self.LOGFILE_DIRECTORY}/{fName}")})
        self.QTHREADS[f"csv-{index}"].tag_data.connect(self.on_tag_data)
        self.QTHREADS[f"csv-{index}"].start()

        comPort = fName[fName.rfind('-')+1:-4]
        self.findChild(QLabel, f"lbl_comPort_{index}").setText(f"COM{comPort}")
        tagColour = self.findChild(QComboBox, f"cmb_colour_{index}").currentText()
        self.TAG_COLOURS.update({f"COM{comPort}": tagColour})
        self.findChild(QPushButton, f"btn_replay_{index}").setEnabled(False)
        self.findChild(QPushButton, f"btn_stop_{index}").setEnabled(True)
    
    def stop_csv_replay(self, index):
        self.findChild(QPushButton, f"btn_replay_{index}").setEnabled(True)
        self.findChild(QPushButton, f"btn_stop_{index}").setEnabled(False)
    
        if f"csv-{index}" not in self.QTHREADS:
            return
        
        self.QTHREADS[f"csv-{index}"].stop()
        self.QTHREADS[f"csv-{index}"].wait()

    def start_serial_connection(self, index):
        self.start_timer()
        self.findChild(QPushButton, f"btn_connect_{index}").setHidden(True)
        self.findChild(QPushButton, f"btn_disconnect_{index}").setHidden(False)
        baudrate = self.findChild(QLineEdit, f"baudrate_{index}")
        baudrate.setEnabled(False)
        chk_logging = self.findChild(QCheckBox, f"chk_logging_{index}")
        chk_logging.setEnabled(False)

        # Create tag connection
        com_port = self.findChild(QComboBox, f"comPort_{index}")
        com_port.setEnabled(False)

        tagColour = self.findChild(QComboBox, f"cmb_comport_colour_{index}").currentText()
        self.TAG_COLOURS.update({f"{com_port.currentText()}": tagColour})

        self.QTHREADS.update({f"serial-{index}": SerialReader(com_port.currentText(), baudrate.text(), (chk_logging.checkState() == Qt.CheckState.Checked))})
        self.QTHREADS[f"serial-{index}"].tag_data.connect(self.on_tag_data)
        self.QTHREADS[f"serial-{index}"].start()

    def stop_serial_connection(self, index):
        if f"serial-{index}" not in self.QTHREADS:
            return
        
        self.QTHREADS[f"serial-{index}"].stop()
        self.findChild(QPushButton, f"btn_disconnect_{index}").setHidden(True)
        self.QTHREADS[f"serial-{index}"].wait()
        self.findChild(QPushButton, f"btn_connect_{index}").setHidden(False)
        self.findChild(QLineEdit, f"baudrate_{index}").setEnabled(True)
        self.findChild(QCheckBox, f"chk_logging_{index}").setEnabled(True)
        self.findChild(QComboBox, f"comPort_{index}").setEnabled(True)

    def on_tag_data(self, value: TagData, comPort):
        # Update the GUI Data
        self.TAGS[comPort] = value
        self.updateAnchors(value.AnchorPositions)
        
    def redraw_plot(self):
        # Clear Plot
        self.plot.cla()
        self.drawPlot()
    
        # Add plot graphics
        self.drawAnchors()
        for comPort in self.TAGS.keys():
            self.updateTagLocation(comPort, self.TAG_COLOURS[comPort])

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
            value = self.TAGS[comPort]
            index = list(self.TAGS.keys()).index(comPort)
            self.drawTag(comPort, value.TagPosition.X, value.TagPosition.Y, f"TAG-{comPort}", colour)
            self.findChild(QLabel, f"lbl_tag_{index+1}").setText(f"TAG_{comPort}: ({value.TagPosition.X}, {value.TagPosition.Y}, {value.TagPosition.Z})")
            self.findChild(QProgressBar, f"prgbar_{index+1}").setValue(value.TagPosition.QF)

    def drawTag(self, comPort, x, y, name, colour):
        self.drawTagLines(comPort, x, y)
        circle = plt.Circle((x, y), radius=0.05, color=colour, alpha=0.6)
        self.plot.add_patch(circle)
        self.plot.text(x, y, f"{name}", horizontalalignment="center", verticalalignment="bottom", fontsize=6, fontweight="bold", color="black")
        self.plot.text(x, y, f"({x}, {y})", horizontalalignment="center", verticalalignment="top", fontsize=8, color="gray")

    def drawAnchors(self):
        anchor_list_text = []
        numPerColumn = 3
        for a in self.ANCHOR_LOCATIONS:
            self.drawTriangle(a.X, a.Y, 0.1, self.ANCHOR_COLOUR)
            self.plot.text(a.X, a.Y, f"({a.AnchorID})", horizontalalignment="center", verticalalignment="bottom", fontsize=8, color="black")
            anchor_list_text.append(f"[{a.AnchorID}]({a.X}, {a.Y}, {a.Z})\n")
        self.lbl_anchors_col1.setText(''.join(anchor_list_text[:numPerColumn]))
        self.lbl_anchors_col2.setText(''.join(anchor_list_text[numPerColumn:numPerColumn*2]))
        self.lbl_anchors_col3.setText(''.join(anchor_list_text[numPerColumn*2:numPerColumn*3]))
        self.lbl_anchors_col4.setText(''.join(anchor_list_text[numPerColumn*3:]))


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
