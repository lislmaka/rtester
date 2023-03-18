from PyQt5 import QtWidgets, QtCore, uic


# ------------------------------------------------------------------------------- #
# Отдельное окно для отображения logs
# ------------------------------------------------------------------------------- #
class window_logs(QtWidgets.QDialog):
    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def __init__(self, table_model, parent=None):
        super().__init__(parent=parent)
        uic.loadUi("./Ui/Logs.ui", self)
        self.setWindowTitle("Logs")
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setWindowFlag(QtCore.Qt.WindowMinimizeButtonHint, True)
        self.setWindowFlag(QtCore.Qt.WindowMaximizeButtonHint, True)
        self.table_model = table_model
        self.tv_table.setModel(self.table_model)
        self.tv_table.resizeColumnsToContents()
        self.cb_request_result_type2.currentTextChanged.connect(self.gui_event_cb_request_result_type)

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_event_cb_request_result_type(self):
        """
        """
        self.table_filter_model = QtCore.QSortFilterProxyModel()
        self.table_filter_model.setSourceModel(self.table_model)

        self.table_filter_model.setFilterKeyColumn(0)

        if self.cb_request_result_type2.currentIndex() == 1:
            self.table_filter_model.setFilterFixedString("ОК")
        elif self.cb_request_result_type2.currentIndex() == 2:
            self.table_filter_model.setFilterFixedString("Ошибка")
        else:
            self.table_filter_model.setFilterFixedString("")

        self.tv_table.setModel(self.table_filter_model)
        self.tv_table.scrollToBottom()
        self.tv_table.resizeColumnsToContents()