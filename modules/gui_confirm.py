from PyQt5 import QtWidgets


# ------------------------------------------------------------------------------- #
#
# ------------------------------------------------------------------------------- #
class window_confirm(QtWidgets.QMessageBox):
    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def __init__(self, bg_color=None, parent=None):
        super().__init__(parent=parent)
        # self.confirm_data()
        self.bg_color = bg_color

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def confirm_data(
            self,
            text="Очистить все данные из таблицы?",
            title_text="Подтвердите действие",
            ok_text="Да",
            cancel_text="Нет"):
        """
        """
        if self.bg_color: 
            if self.bg_color == "danger":
                self.setStyleSheet("background-color: rgb(255, 85, 127);")

            if self.bg_color == "info":
                self.setStyleSheet("background-color: rgb(85, 170, 255);")

        self.setIcon(QtWidgets.QMessageBox.Information)
        self.setText(text)
        self.setWindowTitle(title_text)
        self.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)

        btn_ok = self.button(QtWidgets.QMessageBox.Ok)
        btn_ok.setText(ok_text)
        btn_cancel = self.button(QtWidgets.QMessageBox.Cancel)
        btn_cancel.setText(cancel_text)

        self.exec()
        if self.clickedButton() == btn_ok:
            return True
        else:
            return False
