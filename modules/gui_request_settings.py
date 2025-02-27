from PyQt5 import QtWidgets, QtCore, uic
import os


# ------------------------------------------------------------------------------- #
#
# ------------------------------------------------------------------------------- #
class window_request_settings(QtWidgets.QDialog):
    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def __init__(self, app_settings, parent=None):
        super().__init__(parent=parent)
        uic.loadUi("./Ui/Request_settings.ui", self)
        self.app_settings = app_settings
        self.setWindowTitle("Параметры запроса")
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

        self.btn_close.clicked.connect(self.on_close)
        self.btn_save.clicked.connect(self.on_save)

        self.load_data()

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def load_data(self):
        """ """
        if os.path.isfile(self.app_settings.get("request_headers")):
            with open(
                self.app_settings.get("request_headers"), "r", encoding="utf-8"
            ) as infile:
                file_text = infile.read()
            self.json_request_settings_headers.appendPlainText(file_text)

        #
        if os.path.isfile(self.app_settings.get("request_params")):
            with open(
                self.app_settings.get("request_params"), "r", encoding="utf-8"
            ) as infile:
                file_text = infile.read()
            self.json_request_settings_params.appendPlainText(file_text)

        #
        if os.path.isfile(self.app_settings.get("request_cookies")):
            with open(
                self.app_settings.get("request_cookies"), "r", encoding="utf-8"
            ) as infile:
                file_text = infile.read()
            self.json_request_settings_cookies.appendPlainText(file_text)

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def on_close(self):
        """ """
        self.close()

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def on_save(self):
        """ """
        pass
