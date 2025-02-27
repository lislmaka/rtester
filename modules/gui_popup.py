from PyQt5 import QtWidgets, QtCore, uic


# ------------------------------------------------------------------------------- #
# Popup окно для отображения информациии
# ------------------------------------------------------------------------------- #
class window_popup(QtWidgets.QDialog):
    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def __init__(self, popup_title, popup_type="info", popup_text=None, parent=None):
        super().__init__(parent=parent)
        uic.loadUi("./Ui/Popup.ui", self)
        self.setWindowTitle(popup_title)
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

        self.l_popup_text.setText(popup_text)
        if popup_type == "info":
            self.btn_close.setVisible(False)

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def set_popup_text(self, popup_text):
        """ """
        self.l_popup_text.setText(popup_text)
