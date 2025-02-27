from PyQt5 import QtWidgets, QtCore, uic
import os


# ------------------------------------------------------------------------------- #
# Раздел меню о программе
# Отображается содержимое файла about.md
# Возможно надобудет заменить на отображение github readme.md
# Из известных проблем то что компанент QTextEdit не отображает картинки markdawn
# ------------------------------------------------------------------------------- #
class menu_about(QtWidgets.QDialog):
    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        uic.loadUi("./Ui/Menu_about.ui", self)
        self.setWindowTitle("О программе")
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setFixedSize(self.size())
        self.show_about_message()
        self.show_license_message()

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def show_license_message(self):
        """ """
        if os.path.isfile("license.md"):
            with open("license.md", "r", encoding="utf-8") as infile:
                file_text = infile.read()
            self.te_license_program.setMarkdown(file_text)
        else:
            self.te_license_program.setMarkdown(
                "No license.md file avaliable in root folder"
            )

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def show_about_message(self):
        """ """
        if os.path.isfile("about.md"):
            with open("about.md", "r", encoding="utf-8") as infile:
                file_text = infile.read()
            self.te_about_program.setMarkdown(file_text)
        else:
            self.te_about_program.setMarkdown(
                "No about.md file avaliable in root folder"
            )
