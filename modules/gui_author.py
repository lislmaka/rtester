from PyQt5 import QtWidgets, QtCore, uic
import webbrowser


# ------------------------------------------------------------------------------- #
# Раздел меню об авторе
# ------------------------------------------------------------------------------- #
class menu_author(QtWidgets.QDialog):
    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def __init__(self, app_settings, parent=None):
        super().__init__(parent=parent)
        uic.loadUi("./Ui/Menu_author.ui", self)
        self.setWindowTitle("Об авторе")
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setFixedSize(self.size())

        self.app_settings = app_settings

        self.le_github_url.setText(self.app_settings.get("authon_github_url"))
        self.le_email.setText(self.app_settings.get("authon_email"))
        self.le_whatsapp.setText(self.app_settings.get("authon_whatsapp"))
        self.btn_open_url.clicked.connect(
            lambda: webbrowser.open(self.app_settings.get("authon_github_url"))
        )
        self.btn_open_whatsapp.clicked.connect(self.on_open_whatsapp)
        self.btn_copy_email.clicked.connect(self.on_copy_email)

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def on_copy_email(self):
        """ """
        self.le_email.selectAll()
        self.le_email.copy()

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def on_open_whatsapp(self):
        """ """
        clear_phone = "".join(c for c in self.whatsapp if c.isdigit())
        webbrowser.open("https://wa.me/{}".format(clear_phone))
