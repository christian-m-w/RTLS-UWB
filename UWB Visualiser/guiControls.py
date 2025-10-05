import os
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QCheckBox, QProgressBar, QLineEdit, QColorDialog, QGroupBox
from PyQt6.QtCore import Qt
from PyQt6 import QtGui
import serial.tools.list_ports
from functools import partial

class guiControls():
    def CreateControlsLayout(self):
        controlsLayout = QVBoxLayout()

        # Floor plan configuration
        fp_groupBox = QGroupBox("Floorplan Configuration")
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
        for port in serial.tools.list_ports.comports():
            if port.description.startswith("USB Serial Device"):
                comPortLayout = QHBoxLayout()
                comPort = QLabel(self)
                comPort.setText(f"{port.name}")
                comPortLayout.addWidget(comPort)

                baudrate = QLineEdit(self)
                baudrate.setText("115200")
                baudrate.setObjectName(f"baudrate_{port.name}")
                comPortLayout.addWidget(baudrate)

                chk_logging = QCheckBox("Enable Logging")
                chk_logging.setChecked(True)
                chk_logging.setObjectName(f"chk_logging_{port.name}")
                comPortLayout.addWidget(chk_logging)

                btn_connect = QPushButton("Connect")
                btn_connect.clicked.connect(partial(self.start_serial_connection, port.name))
                btn_connect.setObjectName(f"btn_connect_{port.name}")
                comPortLayout.addWidget(btn_connect)

                btn_disconnect = QPushButton("Disconnect")
                btn_disconnect.clicked.connect(partial(self.stop_serial_connection, port.name))
                btn_disconnect.setObjectName(f"btn_disconnect_{port.name}")
                btn_disconnect.setHidden(True)
                comPortLayout.addWidget(btn_disconnect)

                controlsLayout.addLayout(comPortLayout)

        controlsLayout.addStretch()

        # Logging path settings
        csv_heading = QLabel("CSV Replay")
        controlsLayout.addWidget(csv_heading)
        c_list = ["red", "green","blue", "yellow", "orange", "purple", "cyan", "lime"]
        
        for index in range(1, 5):
            csvReplayLayout = QHBoxLayout()
            self.cmb_colour = QComboBox(self)
            for row, colour in enumerate(c_list):
                self.cmb_colour.addItem(colour)
                model = self.cmb_colour.model()
                model.setData(model.index(row, 0), QtGui.QColor(colour), Qt.ItemDataRole.BackgroundRole)
            self.cmb_colour.currentTextChanged.connect(partial(self.UpdateQWidgetColour, QComboBox, f"cmb_colour_{index}"))
            csvReplayLayout.addWidget(self.cmb_colour)
            self.cmb_colour.setObjectName(f"cmb_colour_{index}")
            self.cmb_colour.setStyleSheet(f"QWidget {{background-color: {c_list[0]};}}")

            self.cmb_csv = QComboBox(self)
            self.cmb_csv.setObjectName(f"cmb_csv_{index}")
            for f_name in os.listdir(f"{self.LOGFILE_DIRECTORY}"):
                if f_name.endswith(".csv"):
                    self.cmb_csv.addItem(f"{f_name}")
            csvReplayLayout.addWidget(self.cmb_csv)

            self.btn_replay = QPushButton("Replay")
            self.btn_replay.clicked.connect(partial(self.start_csv_replay, index))
            csvReplayLayout.addWidget(self.btn_replay)

            self.btn_stop = QPushButton("Stop")
            self.btn_stop.clicked.connect(partial(self.stop_csv_replay, index))
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

        self.lbl_anchors = QLabel("Anchor List:")
        controlsLayout.addWidget(self.lbl_anchors)

        controlsLayout.addStretch()
        return controlsLayout