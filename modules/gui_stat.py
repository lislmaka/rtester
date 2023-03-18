from PyQt5 import QtWidgets, QtCore, uic


# ------------------------------------------------------------------------------- #
# Отдельное окно для отображения статистики
# ------------------------------------------------------------------------------- #
class window_stat(QtWidgets.QDialog):
    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def __init__(self, table_stat_model, parent=None):
        super().__init__(parent=parent)
        uic.loadUi("./Ui/Statistics.ui", self)
        self.setWindowTitle("Статистика")
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setWindowFlag(QtCore.Qt.WindowMinimizeButtonHint, True)
        self.setWindowFlag(QtCore.Qt.WindowMaximizeButtonHint, True)
        self.table_stat_model = table_stat_model
        self.tw_stat.setModel(self.table_stat_model)
        self.tw_stat.resizeColumnsToContents()