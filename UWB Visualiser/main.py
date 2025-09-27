import sys, os
import time
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QComboBox, QPushButton, QCheckBox, QProgressBar
from PyQt6.QtGui import QPainter, QPainterPath, QPen, QImage, QPixmap, QColor
from PyQt6.QtCore import QRectF, Qt
from PyQt6 import QtCore
from serialReader import SerialReader
from csvReader import CsvReader
from tagData import TagData
from dataclasses import dataclass
from collections import namedtuple
import serial.tools.list_ports

@dataclass(frozen=True)
class AnchorLocation:
    AnchorID: str
    X: float
    Y: float
    Z: float

class RtlsUwbApplication(QWidget):
    ANCHOR_LOCATIONS = set()
    TAG_DATA: TagData

    # Floor Plan Origin Offset
    FP_OFFSET_X = 40
    FP_OFFSET_Y = 26

    def __init__(self):
        super().__init__()

        # Setup the Application Window
        window_width = int(1920/1.5)
        window_height = int(1080/1.5)

        self.setWindowTitle("RTLS UWB Visualiser")
        self.resize(window_width, window_height)

        # Add the GUI components
        layout = QVBoxLayout()
        layout.setContentsMargins(int(window_width/2),0,0,0)
        self.setLayout(layout)

        self.comPort = QComboBox(self)
        for port in serial.tools.list_ports.comports():
            self.comPort.addItem(f"{port.name}")
        layout.addWidget(self.comPort)

        self.baudrate = QComboBox(self)
        self.baudrate.addItem("115200")
        layout.addWidget(self.baudrate)

        self.chk_logging = QCheckBox("Enable Logging")
        self.chk_logging.setChecked(True)
        layout.addWidget(self.chk_logging)
        
        self.btn_connect = QPushButton("Connect")
        self.btn_connect.clicked.connect(self.start_serial_connection)
        layout.addWidget(self.btn_connect)

        self.btn_disconnect = QPushButton("Disconnect")
        self.btn_disconnect.clicked.connect(self.stop_serial_connection)
        layout.addWidget(self.btn_disconnect)

        layout.addStretch()

        self.cmb_csv = QComboBox(self)
        for f_name in os.listdir("."):
            if f_name.endswith(".csv"):
                self.cmb_csv.addItem(f"{f_name}")
        layout.addWidget(self.cmb_csv)

        self.btn_replay = QPushButton("Replay")
        self.btn_replay.clicked.connect(self.start_csv_replay)
        layout.addWidget(self.btn_replay)

        self.btn_stop = QPushButton("Stop")
        self.btn_stop.clicked.connect(self.stop_csv_replay)
        layout.addWidget(self.btn_stop)

        layout.addStretch()

        self.lbl_tag = QLabel("Tag Position:")
        layout.addWidget(self.lbl_tag)
        self.lbl_tag_qf = QLabel("Tag Quality Factor:")
        layout.addWidget(self.lbl_tag_qf)

        self.prgbar = QProgressBar()
        self.prgbar.setMaximum(100)
        self.prgbar.setValue(0)
        layout.addWidget(self.prgbar)

        self.lbl_anchors = QLabel("Anchor List:")
        layout.addWidget(self.lbl_anchors)

        layout.addStretch()

    def start_csv_replay(self):      
        # Read CSV Log
        self.worker_thread = CsvReader(self.cmb_csv.currentText())
        
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
        self.update()

    def updateAnchors(self, anchorPositions: TagData.AnchorPositions):
        # Update list of anchor locations
        for a in anchorPositions:
            self.ANCHOR_LOCATIONS.add(AnchorLocation(a.AnchorID, a.X, a.Y, a.Z))

    def closeEvent(self, event):
        # On window closing, disconnect all the tags
        self.worker_thread.stop()
        self.worker_thread.wait()
        app.quit()

    def paintEvent(self, e):
        painter = QPainter()
        painter.begin(self)

        # Draw Grid and Anchors
        self.drawGrid(painter)
        self.drawAnchors(painter)

        # Show Tag on floorplan
        if hasattr(self, 'TAG_DATA'):
            disp_pos_x = self.TAG_DATA.TagPosition.X*80 + self.FP_OFFSET_X
            disp_pos_y = self.TAG_DATA.TagPosition.Y*73 + self.FP_OFFSET_Y
            self.drawTagLines(painter)
            self.drawTag(painter, int(disp_pos_x), int(disp_pos_y), 10)

        # Display GUI
        painter.end()

    def drawGrid(self, painter: QPainter):
        current_pen = painter.pen()
        
        # Create Floorplan
        pen = QPen()
        pen.setWidth(2)
        painter.setPen(pen)
        fp_width = int(window.width() / 2)
        fp_height = window.height() - 20
        floorplan = QPixmap("./floorplan.png")
        if floorplan.isNull() == False:
            fp_scale = (window.height() - 20) / floorplan.height()
            fp_width = int(floorplan.width() * fp_scale)
            fp_height = int(floorplan.height() * fp_scale)
            painter.drawPixmap(10, 10, fp_width, fp_height, floorplan)

        painter.drawRect(10, 10, fp_width, fp_height)
        painter.setPen(current_pen)

        # Flip Y-Axis
        painter.translate(0, self.height())
        painter.scale(1.0, -1.0)

        fp_grid_scale = 1.0

        # Draw gridlines
        pen = QPen()
        pen.setColor(QtCore.Qt.GlobalColor.lightGray)
        painter.setPen(pen)
        grid_size = int(35 * fp_grid_scale)
        for x in range(self.FP_OFFSET_X, fp_width, grid_size):
            painter.drawLine(x, self.FP_OFFSET_Y, x, fp_height)
        
        for y in range(fp_height - self.FP_OFFSET_Y, 0, -grid_size):
            painter.drawLine(self.FP_OFFSET_X, y, fp_width, y)

    def drawAnchors(self, painter: QPainter):
        pen = painter.pen()
        brush = painter.brush()

        painter.setPen(QtCore.Qt.GlobalColor.red)
        painter.setBrush(QtCore.Qt.GlobalColor.red)

        anchor_list_text = "Anchor List: \n"

        for a in self.ANCHOR_LOCATIONS:
            self.drawTriangle(painter, int(a.X*80), int(a.Y*73), 10)
            self.drawTextInv(painter, int(a.X*80-20), int(a.Y*73+8), f"({a.AnchorID})", QtCore.Qt.GlobalColor.gray)
            anchor_list_text += f"{a.AnchorID} - ({a.X}, {a.Y}, {a.Z})\n"

        self.lbl_anchors.setText(anchor_list_text)

        painter.setPen(pen)
        painter.setBrush(brush)

    def drawTag(self, painter: QPainter, x, y, size):
        pen = painter.pen()
        brush = painter.brush()
        painter.setPen(QtCore.Qt.GlobalColor.blue)
        painter.setBrush(QtCore.Qt.GlobalColor.blue)
        self.drawTriangle(painter, x, y, size)
        painter.setPen(pen)
        painter.setBrush(brush)

        painter.save()
        painter.scale(1, -1)
        painter.setPen(QtCore.Qt.GlobalColor.gray)
        painter.drawText(x-10, -(y-16), "TAG")
        painter.drawText(x-20, -(y-30), f"({self.TAG_DATA.TagPosition.X}, {self.TAG_DATA.TagPosition.Y})")
        painter.restore()

    def drawTagLines(self, painter: QPainter):
        pen = painter.pen()
        painter.setPen(QtCore.Qt.GlobalColor.green)
        
        # Add Anchor lines
        for a in self.TAG_DATA.AnchorPositions:
            painter.drawLine(int(a.X*80), int(a.Y*73), int(self.TAG_DATA.TagPosition.X*80 + self.FP_OFFSET_X), int(self.TAG_DATA.TagPosition.Y*73 + self.FP_OFFSET_Y))
            self.drawTextInv(painter, int((a.X*80 + self.TAG_DATA.TagPosition.X*80 + self.FP_OFFSET_X)/2)
                                , int((a.Y*73 + self.TAG_DATA.TagPosition.Y*73 + self.FP_OFFSET_Y)/2)
                                , f"{a.MetersFromTag}"
                                , QtCore.Qt.GlobalColor.darkGray)

        painter.setPen(pen)

    def drawTextInv(self, painter: QPainter, x, y, text, colour: QColor):
        painter.save()
        painter.scale(1, -1)
        painter.setPen(colour)
        painter.drawText(x, -y, text)
        painter.restore()
    
    def drawTriangle(self, painter: QPainter, x, y, size):
        path = QPainterPath()
        size = size / 2
        path.moveTo(x-size, y-size)
        path.lineTo(x+size, y-size)
        path.lineTo(x,y+size)
        path.lineTo(x-size,y-size)
        painter.drawPath(path)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RtlsUwbApplication()
    window.show()
    sys.exit(app.exec())
