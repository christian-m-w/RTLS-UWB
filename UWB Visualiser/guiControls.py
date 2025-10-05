import os
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QCheckBox, QProgressBar, QLineEdit, QColorDialog, QGroupBox
from PyQt6.QtCore import Qt
from PyQt6 import QtGui
import serial.tools.list_ports
from functools import partial

class guiControls():
    def CreateControlsLayout(self):
        controlsLayout = QVBoxLayout()

        btn_reset = QPushButton("Reset")
        btn_reset.clicked.connect(self.reset_data)
        controlsLayout.addWidget(btn_reset)

        # Floor plan configuration
        fp_groupBox = QGroupBox("Floorplan Configuration: ")
        fp_groupBoxLayout = QVBoxLayout()
        fp_groupBox.setLayout(fp_groupBoxLayout)

        # Floor plan offsets and scaling
        fpConfigLayout_X = QHBoxLayout()
        fpOriginX_label = QLabel("X Origin (pixels):")
        fpConfigLayout_X.addWidget(fpOriginX_label)
        fpOriginX = QLineEdit(self)
        fpOriginX.setObjectName("fpOriginX")
        fpOriginX.setText("39")
        fpConfigLayout_X.addWidget(fpOriginX)
        fp_groupBoxLayout.addLayout(fpConfigLayout_X)

        fpConfigLayout_Y = QHBoxLayout()
        fpOriginY_label = QLabel("Y Origin (pixels):")
        fpConfigLayout_Y.addWidget(fpOriginY_label)
        fpOriginY = QLineEdit(self)
        fpOriginY.setObjectName("fpOriginY")
        fpOriginY.setText("912")
        fpConfigLayout_Y.addWidget(fpOriginY)
        fp_groupBoxLayout.addLayout(fpConfigLayout_Y)
        
        fpConfigLayout_10m = QHBoxLayout()
        fpOrigin10m_label = QLabel("10m (pixels):")
        fpConfigLayout_10m.addWidget(fpOrigin10m_label)
        fp10m = QLineEdit(self)
        fp10m.setObjectName("fp10m")
        fp10m.setText("960")
        fpConfigLayout_10m.addWidget(fp10m)
        fp_groupBoxLayout.addLayout(fpConfigLayout_10m)

        btn_fpUpdate = QPushButton("Update")
        btn_fpUpdate.clicked.connect(self.update_fp)
        fp_groupBoxLayout.addWidget(btn_fpUpdate)

        controlsLayout.addWidget(fp_groupBox)

        # Add Serial connections
        serial_groupBox = QGroupBox("Serial Connections: ")
        serial_groupBoxLayout = QVBoxLayout()
        serial_groupBox.setLayout(serial_groupBoxLayout)

        for index in range(1, 5):
            comPortLayout = QHBoxLayout()
            comPort = QComboBox(self)
            comPort.setObjectName(f"comPort_{index}")
            for port in serial.tools.list_ports.comports():
                comPort.addItem(f"{port.name}")
            comPortLayout.addWidget(comPort)

            baudrate = QLineEdit(self)
            baudrate.setText("115200")
            baudrate.setObjectName(f"baudrate_{index}")
            comPortLayout.addWidget(baudrate)

            chk_logging = QCheckBox("Enable Logging")
            chk_logging.setChecked(True)
            chk_logging.setObjectName(f"chk_logging_{index}")
            comPortLayout.addWidget(chk_logging)

            btn_connect = QPushButton("Connect")
            btn_connect.clicked.connect(partial(self.start_serial_connection, index))
            btn_connect.setObjectName(f"btn_connect_{index}")
            comPortLayout.addWidget(btn_connect)

            btn_disconnect = QPushButton("Disconnect")
            btn_disconnect.clicked.connect(partial(self.stop_serial_connection, index))
            btn_disconnect.setObjectName(f"btn_disconnect_{index}")
            btn_disconnect.setHidden(True)
            comPortLayout.addWidget(btn_disconnect)

            serial_groupBoxLayout.addLayout(comPortLayout)
        
        controlsLayout.addWidget(serial_groupBox)
        controlsLayout.addStretch()

        # Logging path settings
        csv_heading = QLabel("CSV Replay")
        controlsLayout.addWidget(csv_heading)
       
        for index in range(1, 5):
            csvReplayLayout = QHBoxLayout()
            self.lbl_comPort = QLabel("")
            self.lbl_comPort.setObjectName(f"lbl_comPort_{index}")
            csvReplayLayout.addWidget(self.lbl_comPort)

            self.cmb_colour = QComboBox(self)
            for row, colour in enumerate(self.COLOURS):
                self.cmb_colour.addItem(colour)
                model = self.cmb_colour.model()
                model.setData(model.index(row, 0), QtGui.QColor(colour), Qt.ItemDataRole.BackgroundRole)
            self.cmb_colour.currentTextChanged.connect(partial(self.UpdateQWidgetColour, QComboBox, f"cmb_colour_{index}"))
            csvReplayLayout.addWidget(self.cmb_colour)
            self.cmb_colour.setObjectName(f"cmb_colour_{index}")
            self.cmb_colour.setStyleSheet(f"QWidget {{background-color: {self.COLOURS[0]};}}")

            self.cmb_csv = QComboBox(self)
            self.cmb_csv.setObjectName(f"cmb_csv_{index}")
            for f_name in os.listdir(f"{self.LOGFILE_DIRECTORY}"):
                if f_name.endswith(".csv"):
                    self.cmb_csv.addItem(f"{f_name}")
            csvReplayLayout.addWidget(self.cmb_csv)

            self.btn_replay = QPushButton("Replay")
            self.btn_replay.clicked.connect(partial(self.start_csv_replay, index))
            self.btn_replay.setObjectName(f"btn_replay_{index}")
            csvReplayLayout.addWidget(self.btn_replay)

            self.btn_stop = QPushButton("Stop")
            self.btn_stop.clicked.connect(partial(self.stop_csv_replay, index))
            self.btn_stop.setObjectName(f"btn_stop_{index}")
            self.btn_stop.setEnabled(False)
            csvReplayLayout.addWidget(self.btn_stop)
            controlsLayout.addLayout(csvReplayLayout)

        controlsLayout.addStretch()

        # Other telemetry
        self.lbl_tag = QLabel("Tag Position:")
        controlsLayout.addWidget(self.lbl_tag)
        self.lbl_tag_qf = QLabel("Tag Quality Factor:")
        controlsLayout.addWidget(self.lbl_tag_qf)

        self.prgbar = QProgressBar()
        self.prgbar.setMaximum(100)
        self.prgbar.setValue(0)
        controlsLayout.addWidget(self.prgbar)

        anchor_groupBox = QGroupBox("Anchor List: ")
        anchor_groupBoxLayout = QVBoxLayout()
        anchor_groupBox.setLayout(anchor_groupBoxLayout)
        self.lbl_anchors = QLabel("")
        anchor_groupBoxLayout.addWidget(self.lbl_anchors)
        controlsLayout.addWidget(anchor_groupBox)

        controlsLayout.addStretch()
        return controlsLayout