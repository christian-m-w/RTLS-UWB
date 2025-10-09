import os
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QCheckBox, QProgressBar, QLineEdit, QGroupBox
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

        fpLoadConfigLayout = QHBoxLayout()
        lbl_configFile = QLabel("Config File: ")
        fpLoadConfigLayout.addWidget(lbl_configFile)
        fp_groupBoxLayout.addLayout(fpLoadConfigLayout)
        cmb_configFile = QComboBox()
        cmb_configFile.setObjectName("cmb_configFile")
        for f_name in os.listdir(f"{self.CONFIG_DIRECTORY}"):
            if f_name.endswith(".json"):
                 cmb_configFile.addItem(f"{f_name}")
        fpLoadConfigLayout.addWidget(cmb_configFile)
        btn_loadConfig = QPushButton("Load Config")
        btn_loadConfig.clicked.connect(self.LoadConfig)
        fpLoadConfigLayout.addWidget(btn_loadConfig)

        fpFileConfigLayout = QHBoxLayout()
        lbl_fpfile = QLabel("Floor plan image:")
        fpFileConfigLayout.addWidget(lbl_fpfile)
        fp_filePath = QLineEdit()
        fp_filePath.setObjectName("fp_filePath")
        fp_filePath.setText(f"{self.FP_IMAGE_PATH}")
        fpFileConfigLayout.addWidget(fp_filePath)
        btn_browseFp = QPushButton("Browse")
        btn_browseFp.clicked.connect(self.OpenFileDialog)
        fpFileConfigLayout.addWidget(btn_browseFp)
        fp_groupBoxLayout.addLayout(fpFileConfigLayout)

        # Floor plan offsets and scaling
        fpConfigLayout = QHBoxLayout()
        fpOriginX_label = QLabel("X Origin (pixels):")
        fpConfigLayout.addWidget(fpOriginX_label)
        fpOriginX = QLineEdit(self)
        fpOriginX.setObjectName("fpOriginX")
        fpOriginX.setText(f"{self.FP_ORIGIN_X_IN_PIXELS}")
        fpConfigLayout.addWidget(fpOriginX)
        fp_groupBoxLayout.addLayout(fpConfigLayout)

        fpOriginY_label = QLabel("Y Origin (pixels):")
        fpConfigLayout.addWidget(fpOriginY_label)
        fpOriginY = QLineEdit(self)
        fpOriginY.setObjectName("fpOriginY")
        fpOriginY.setText(f"{self.FP_ORIGIN_Y_IN_PIXELS}")
        fpConfigLayout.addWidget(fpOriginY)

        fpOrigin10m_label = QLabel("10m (pixels):")
        fpConfigLayout.addWidget(fpOrigin10m_label)
        fp10m = QLineEdit(self)
        fp10m.setObjectName("fp10m")
        fp10m.setText(f"{self.FP_10M_IN_PIXELS}")
        fpConfigLayout.addWidget(fp10m)

        btn_fpUpdate = QPushButton("Update")
        btn_fpUpdate.clicked.connect(self.update_fp)
        fpConfigLayout.addWidget(btn_fpUpdate)
        controlsLayout.addWidget(fp_groupBox)

        # Add Serial connections
        serial_groupBox = QGroupBox("Serial Connections: ")
        serial_groupBoxLayout = QVBoxLayout()
        serial_groupBox.setLayout(serial_groupBoxLayout)

        for index in range(1, 5):
            comPortLayout = QHBoxLayout()
            self.cmb_comport_colour = QComboBox(self)
            for row, colour in enumerate(self.COLOURS):
                self.cmb_comport_colour.addItem(colour)
                model = self.cmb_comport_colour.model()
                model.setData(model.index(row, 0), QtGui.QColor(colour), Qt.ItemDataRole.BackgroundRole)
            self.cmb_comport_colour.setCurrentText(self.COLOURS[index-1])
            self.cmb_comport_colour.currentTextChanged.connect(partial(self.UpdateQWidgetColour, QComboBox, f"cmb_comport_colour_{index}"))
            comPortLayout.addWidget(self.cmb_comport_colour)
            self.cmb_comport_colour.setObjectName(f"cmb_comport_colour_{index}")
            self.cmb_comport_colour.setStyleSheet(f"QWidget {{background-color: {self.COLOURS[index-1]};}}")

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

        # Logging path settings
        csvReplayGroupBox = QGroupBox("CSV Replay: ")
        csvReplayGroupBoxLayout = QVBoxLayout()
        csvReplayGroupBox.setLayout(csvReplayGroupBoxLayout)
        controlsLayout.addWidget(csvReplayGroupBox)
       
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
            self.cmb_colour.setCurrentText(self.COLOURS[index-1])
            self.cmb_colour.currentTextChanged.connect(partial(self.UpdateQWidgetColour, QComboBox, f"cmb_colour_{index}"))
            csvReplayLayout.addWidget(self.cmb_colour)
            self.cmb_colour.setObjectName(f"cmb_colour_{index}")
            self.cmb_colour.setStyleSheet(f"QWidget {{background-color: {self.COLOURS[index-1]};}}")

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
            csvReplayGroupBoxLayout.addLayout(csvReplayLayout)

        # Other telemetry
        tag_position_groupBox = QGroupBox("Tag Positions: ")
        tag_position_groupBoxLayout = QVBoxLayout()
        tag_position_groupBox.setLayout(tag_position_groupBoxLayout)

        for index in range(1, 5):
            tagPosLayout = QHBoxLayout()
            self.lbl_tag = QLabel(f"Tag {index}:")
            self.lbl_tag.setObjectName(f"lbl_tag_{index}")
            self.lbl_tag.setMinimumWidth(200)
            tagPosLayout.addWidget(self.lbl_tag)
            self.lbl_tagQf = QLabel("Quality Factor: ")
            tagPosLayout.addWidget(self.lbl_tagQf)
            self.prgbar = QProgressBar()
            self.prgbar.setMaximum(100)
            self.prgbar.setValue(0)
            self.prgbar.setObjectName(f"prgbar_{index}")
            tagPosLayout.addWidget(self.prgbar)
            tag_position_groupBoxLayout.addLayout(tagPosLayout)
        controlsLayout.addWidget(tag_position_groupBox)

        anchor_groupBox = QGroupBox("Anchor List: ")
        anchor_groupBoxLayout = QHBoxLayout()
        anchor_groupBox.setLayout(anchor_groupBoxLayout)
        self.lbl_anchors_col1 = QLabel("")
        anchor_groupBoxLayout.addWidget(self.lbl_anchors_col1)
        self.lbl_anchors_col2 = QLabel("")
        anchor_groupBoxLayout.addWidget(self.lbl_anchors_col2)
        self.lbl_anchors_col3 = QLabel("")
        anchor_groupBoxLayout.addWidget(self.lbl_anchors_col3)
        self.lbl_anchors_col4 = QLabel("")
        anchor_groupBoxLayout.addWidget(self.lbl_anchors_col4)
        controlsLayout.addWidget(anchor_groupBox)

        controlsLayout.addStretch()
        return controlsLayout