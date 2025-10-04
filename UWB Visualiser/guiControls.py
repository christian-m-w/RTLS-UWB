import os
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QCheckBox, QProgressBar, QLineEdit
import serial.tools.list_ports
from functools import partial

class guiControls():
    def CreateControlsLayout(self):
        controlsLayout = QVBoxLayout()

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