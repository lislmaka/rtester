from PyQt5 import QtWidgets, QtGui, QtCore


# ------------------------------------------------------------------------------- #
#
# ------------------------------------------------------------------------------- #
class toolbar(QtWidgets.QToolBar):
    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.parent = parent
        self.make_toolbar()

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def make_toolbar(self):
        """ """
        self.parent.tb_btn_start_process = QtWidgets.QPushButton("Запустить")
        self.parent.tb_btn_start_process.setIcon(QtGui.QIcon("Images/start.png"))
        self.parent.tb_btn_start_process.setIconSize(QtCore.QSize(24, 24))
        self.parent.tb_btn_start_process.clicked.connect(
            self.parent.gui_event_start_program
        )

        self.parent.tb_btn_stop_process = QtWidgets.QPushButton("Остановить")
        self.parent.tb_btn_stop_process.setIcon(QtGui.QIcon("Images/stop.png"))
        self.parent.tb_btn_stop_process.setIconSize(QtCore.QSize(24, 24))
        self.parent.tb_btn_stop_process.setDisabled(True)
        self.parent.tb_btn_stop_process.clicked.connect(
            self.parent.gui_event_stop_theaders
        )

        self.parent.tb_btn_stop_all_process = QtWidgets.QPushButton(
            "Остановить все процессы"
        )
        self.parent.tb_btn_stop_all_process.setIcon(QtGui.QIcon("Images/stop.png"))
        self.parent.tb_btn_stop_all_process.setIconSize(QtCore.QSize(24, 24))
        self.parent.tb_btn_stop_all_process.setDisabled(True)
        self.parent.tb_btn_stop_all_process.setVisible(False)
        self.parent.tb_btn_stop_all_process.clicked.connect(
            self.parent.gui_event_stop_all_theaders
        )

        self.parent.tb_btn_close_app = QtWidgets.QPushButton("Закрыть")
        self.parent.tb_btn_close_app.setIcon(QtGui.QIcon("Images/exit.png"))
        self.parent.tb_btn_close_app.setIconSize(QtCore.QSize(24, 24))
        self.parent.tb_btn_close_app.clicked.connect(self.parent.gui_event_close_app)

        self.parent.toolbar = self
        self.parent.toolbar.addWidget(self.parent.tb_btn_close_app)
        self.parent.toolbar.addWidget(self.parent.tb_btn_start_process)
        self.parent.toolbar.addWidget(self.parent.tb_btn_stop_process)
        self.parent.tb_btn_stop_all_process_action = self.parent.toolbar.addWidget(
            self.parent.tb_btn_stop_all_process
        )
        self.parent.addToolBar(self.parent.toolbar)
