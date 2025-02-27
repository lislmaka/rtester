import requests
import json
import sys
import csv
import os
import datetime
import time
import webbrowser
import psutil
import pyqtgraph as pg
from urllib.parse import urlparse
from user_agent import generate_user_agent
from PyQt5 import QtWidgets, QtCore, QtGui, uic


# ------------------------------------------------------------------------------- #
# 
# ------------------------------------------------------------------------------- #
class WorkerSignals(QtCore.QObject):
    # --------------------------------------------------------------------------- #
    #  Определяем свои сигналы
    # --------------------------------------------------------------------------- #
    on_request = QtCore.pyqtSignal(str, int, int)
    on_iteration = QtCore.pyqtSignal(int, int, int, bool)
    on_log_message = QtCore.pyqtSignal(int, int, int, str, str, str, int, str, str)
    on_theader_finished = QtCore.pyqtSignal(int)
    on_theader_started = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal()


# ------------------------------------------------------------------------------- #
# Class single_requsts_theader
# ------------------------------------------------------------------------------- #
class single_requsts_theader(QtCore.QRunnable):
    # --------------------------------------------------------------------------- #
    #  Определяем свои сигналы
    # --------------------------------------------------------------------------- #
    # on_request = QtCore.pyqtSignal(str, int, int)
    # on_iteration = QtCore.pyqtSignal(int, int, int, bool)
    # on_log_message = QtCore.pyqtSignal(int, int, int, str, str, str, int, str, str)
    # on_theader_finished = QtCore.pyqtSignal(int)
    # on_theader_started = QtCore.pyqtSignal(int)

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def __init__(self,
                 theader_id,
                 url,
                 count_of_requests,
                 request_method,
                 request_timeout,
                 cycle_count,
                 cpu_max_value,
                 cpu_current_value,
                 parent=None):
        #super().__init__(parent=parent)
        super(single_requsts_theader, self).__init__()
        self.count_of_requests = count_of_requests
        self.url = url
        self.is_theader_stop = False
        self.theader_id = theader_id
        self.request_method = request_method
        self.request_timeout = request_timeout
        self.cycle_count = cycle_count
        self.cpu_max_value = cpu_max_value
        self.cpu_current_value = cpu_current_value
        self.signals = WorkerSignals()
        #self.signals.finished.connect(self.on_finished)

    # --------------------------------------------------------------------------- #
    # Generate User-Agent
    # --------------------------------------------------------------------------- #
    def gen_new_user_agent(self):
        """
        Generate User-Agent
        """
        return generate_user_agent(os=("win", "mac", "linux"), device_type=("desktop",))

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def stop_theader(self):
        """
        """
        self.is_theader_stop = True

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def on_finished(self):
        """
        """
        self.signals.on_theader_finished.emit(self.theader_id)

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def run(self):
        """
        """
        self.signals.on_theader_started.emit(self.theader_id)

        count_of_iteration = 1
        while count_of_iteration <= self.count_of_requests:
            #self.cpu_current_value = psutil.cpu_percent(0.1)
            #self.cpu_current_value = self.cpu_sys_value
            if self.is_theader_stop:
                self.signals.on_iteration.emit(self.theader_id,
                                       count_of_iteration,
                                       round(self.cpu_current_value),
                                       self.is_theader_stop)
                break
            if self.cpu_current_value > self.cpu_max_value:
                self.signals.on_iteration.emit(self.theader_id,
                                       count_of_iteration,
                                       round(self.cpu_current_value),
                                       self.is_theader_stop)
                # TODO Магия... Надо почитать более подробнее
                # задачи стартуют так быстро что если не делать задержку то не поток успевает получить флаг отстановки
                # при большом кол-ве потоков
                # Надо ждать иначе уйдет в бесконечный цикл
                time.sleep(0.1)
                continue
            else:
                count_of_iteration += 1

            headers = {
                "User-Agent": self.gen_new_user_agent(),
            }
            try:
                if self.request_method == "get":
                    response = requests.get(url=self.url,
                                            headers=headers,
                                            timeout=self.request_timeout)
                if self.request_method == "post":
                    response = requests.post(url=self.url,
                                             headers=headers,
                                             timeout=self.request_timeout)
                if self.request_method == "head":
                    response = requests.head(url=self.url,
                                             headers=headers,
                                             timeout=self.request_timeout)

                if response.status_code in [200, 301, 302]:
                    if self.request_method == "get":
                        download_size = len(response.content)
                    if self.request_method == "head":
                        download_size = len(response.headers)

                    self.signals.on_request.emit("request", response.status_code, download_size)
                    self.signals.on_log_message.emit(self.theader_id,
                                             count_of_iteration,
                                             self.cycle_count,
                                             str(response.status_code),
                                             self.url,
                                             self.request_method,
                                             self.request_timeout,
                                             "HTTP Status Code {}".format(response.status_code),
                                             "success")
                else:
                    self.signals.on_request.emit("request", response.status_code, 0)
                    self.signals.on_log_message.emit(self.theader_id,
                                             count_of_iteration,
                                             self.cycle_count,
                                             str(response.status_code),
                                             self.url,
                                             self.request_method,
                                             self.request_timeout,
                                             "HTTP Status Code {}".format(response.status_code),
                                             "error")
            except Exception as err:
                self.signals.on_request.emit("connection", 0, 0)
                self.signals.on_log_message.emit(self.theader_id,
                                         count_of_iteration,
                                         self.cycle_count,
                                         None,
                                         self.url,
                                         self.request_method,
                                         self.request_timeout,
                                         str(err),
                                         "error")
            finally:
                self.signals.on_iteration.emit(self.theader_id,
                                       count_of_iteration,
                                       round(self.cpu_current_value),
                                       self.is_theader_stop)
        self.signals.on_theader_finished.emit(self.theader_id)


# ------------------------------------------------------------------------------- #
#
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
        """
        """
        self.l_popup_text.setText(popup_text)


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
        """
        """
        if os.path.isfile(self.app_settings.get("request_headers")):
            with open(self.app_settings.get("request_headers"), "r", encoding="utf-8") as infile:
                file_text = infile.read()
            self.json_request_settings_headers.appendPlainText(file_text)

        #
        if os.path.isfile(self.app_settings.get("request_params")):
            with open(self.app_settings.get("request_params"), "r", encoding="utf-8") as infile:
                file_text = infile.read()
            self.json_request_settings_params.appendPlainText(file_text)

        #
        if os.path.isfile(self.app_settings.get("request_cookies")):
            with open(self.app_settings.get("request_cookies"), "r", encoding="utf-8") as infile:
                file_text = infile.read()
            self.json_request_settings_cookies.appendPlainText(file_text)

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def on_close(self):
        """
        """
        self.close()

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def on_save(self):
        """
        """
        pass


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

        self.table_filter_model.setFilterKeyColumn(5)

        if self.cb_request_result_type2.currentIndex() == 1:
            self.table_filter_model.setFilterFixedString("ОК")
        elif self.cb_request_result_type2.currentIndex() == 2:
            self.table_filter_model.setFilterFixedString("Ошибка")
        else:
            self.table_filter_model.setFilterFixedString("")            

        self.tv_table.setModel(self.table_filter_model)
        self.tv_table.scrollToBottom()
        self.tv_table.resizeColumnsToContents()


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
        self.btn_open_url.clicked.connect(lambda: webbrowser.open(self.app_settings.get("authon_github_url")))
        self.btn_open_whatsapp.clicked.connect(self.on_open_whatsapp)
        self.btn_copy_email.clicked.connect(self.on_copy_email)

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def on_copy_email(self):
        """
        """
        self.le_email.selectAll()
        self.le_email.copy()

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def on_open_whatsapp(self):
        """
        """
        clear_phone = "".join(c for c in self.whatsapp if c.isdigit())
        webbrowser.open("https://wa.me/{}".format(clear_phone))


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
        """
        """
        if os.path.isfile("license.md"):
            with open("license.md", "r", encoding="utf-8") as infile:
                file_text = infile.read()
            self.te_license_program.setMarkdown(file_text)
        else:
            self.te_license_program.setMarkdown("No license.md file avaliable in root folder")

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def show_about_message(self):
        """
        """
        if os.path.isfile("about.md"):
            with open("about.md", "r", encoding="utf-8") as infile:
                file_text = infile.read()
            self.te_about_program.setMarkdown(file_text)
        else:
            self.te_about_program.setMarkdown("No about.md file avaliable in root folder")


# ------------------------------------------------------------------------------- #
# Клас сновного окна программы
# ------------------------------------------------------------------------------- #
class main_gui(QtWidgets.QMainWindow):
    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    mutex = QtCore.QMutex()

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent=parent)
        #uic.loadUi("./Ui/Main.ui", self)
        uic.loadUi("./Ui/Main_dev.ui", self)

        self.threadpool = QtCore.QThreadPool()

        self.app_settings = self.import_json_settings()
        self.app_tests = self.import_json_tests()

        self.setWindowTitle("{} {}".format(
            self.app_settings.get("program_name"),
            self.app_settings.get("program_version"))
        )

        self.timer_time = QtCore.QTimer(self)
        self.timer_time.timeout.connect(self.on_timer_time)
        self.timer_graf = QtCore.QTimer(self)
        self.timer_graf.timeout.connect(self.on_timer_graf)
        self.timer_cpu_collect_data = QtCore.QTimer(self)
        self.timer_cpu_collect_data.timeout.connect(self.on_timer_cpu_collect_data)
        self.timer_cpu_calculate_value = QtCore.QTimer(self)
        self.timer_cpu_calculate_value.timeout.connect(self.on_timer_cpu_calculate_value)

        #
        self.btn_requests_settings.clicked.connect(self.gui_event_requests_settings)
        self.btn_show_stat_in_new_window.clicked.connect(self.gui_event_show_stat_in_new_window)
        self.btn_show_requests_logs_in_new_window.clicked.connect(self.gui_event_show_requests_logs_in_new_window)
        self.btn_clear_stat_data.clicked.connect(self.gui_event_clear_stat_data)
        self.btn_clear_log_requests_data.clicked.connect(self.gui_event_clear_log_requests_data)
        self.btn_save_file_log_requests_data.clicked.connect(self.gui_event_save_file_log_requests_data)

        self.sb_theaders.valueChanged.connect(self.gui_event_change_active_theaders)
        self.sb_requests.valueChanged.connect(self.gui_event_change_count_requests_by_active_theaders)
        self.sb_cycles_count.valueChanged.connect(self.gui_event_change_cycles_count)
        self.cb_request_method.currentTextChanged.connect(self.gui_event_change_request_method)
        self.cb_request_settings.currentTextChanged.connect(self.gui_event_change_use_request_settings)
        self.cb_request_result_type.currentTextChanged.connect(self.gui_event_cb_request_result_type)
        #
        self.menu_action_about.triggered.connect(self.menu_about)
        self.menu_action_author.triggered.connect(self.menu_author)
        self.menu_action_start.triggered.connect(self.menu_start)
        self.menu_action_close.triggered.connect(self.menu_close_app)
        self.menu_action_stop.triggered.connect(self.menu_stop)
        self.menu_action_stop_all.triggered.connect(self.menu_stop_all)

        self.gui_initialization_toolbar()
        self.gui_initialization_stat_table()
        self.gui_initialization_log_table()
        self.gui_initialization_urls()
        self.gui_initialization_cycles()
        self.gui_initialization_theaders_progress_bars_canvas()
        self.gui_initialization()

        # Запускаем таймер для сбора и отображения данных
        # 1. загрузка CPU
        # 2. использованию памяти
        self.cpu_current_value = 0
        self.cpu_current_trend = ""
        self.cpu_current_values = list()
        self.timer_cpu_collect_data.start(100)
        self.timer_cpu_calculate_value.start(1000)

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def import_json_settings(self):
        """
        """
        with open("settings.txt", encoding="utf-8") as json_file:
            settings = json.load(json_file)
        return settings

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def import_json_tests(self):
        """
        """
        if os.path.isfile("tests.txt"):
            with open("tests.txt", encoding="utf-8") as json_file:
                settings = json.load(json_file)
            if settings:
                return settings
            else:
                self.add_logs_system("Файл {} присутствует но пустой либо неправильного формата".format("tests.txt"))
                return False
        else:
            self.add_logs_system("Нет файла {} с настройками тестирования".format("tests.txt"))
            self.add_logs_system("Для всех циклов будут использоваться настроки поумолчанию")            
            return False

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_initialization_toolbar(self):
        """
        """
        self.tb_btn_start_process = QtWidgets.QPushButton("Запустить")
        self.tb_btn_start_process.setIcon(QtGui.QIcon("Images/start.png"))
        self.tb_btn_start_process.setIconSize(QtCore.QSize(24, 24))
        #self.tb_btn_start_process.setShortcut('Ctrl+A')
        self.tb_btn_start_process.clicked.connect(self.gui_event_start_program)

        self.tb_btn_stop_process = QtWidgets.QPushButton("Остановить")
        self.tb_btn_stop_process.setIcon(QtGui.QIcon("Images/stop.png"))
        self.tb_btn_stop_process.setIconSize(QtCore.QSize(24, 24))
        #self.tb_btn_stop_process.setShortcut('Ctrl+S')
        self.tb_btn_stop_process.setDisabled(True)
        self.tb_btn_stop_process.clicked.connect(self.gui_event_stop_theaders)

        self.tb_btn_stop_all_process = QtWidgets.QPushButton("Остановить все процессы")
        self.tb_btn_stop_all_process.setIcon(QtGui.QIcon("Images/stop.png"))
        self.tb_btn_stop_all_process.setIconSize(QtCore.QSize(24, 24))
        #self.tb_btn_stop_all_process.setShortcut('Ctrl+D')
        self.tb_btn_stop_all_process.setDisabled(True)
        self.tb_btn_stop_all_process.setVisible(False)
        self.tb_btn_stop_all_process.clicked.connect(self.gui_event_stop_all_theaders)

        self.tb_btn_close_app = QtWidgets.QPushButton("Закрыть")
        self.tb_btn_close_app.setIcon(QtGui.QIcon("Images/exit.png"))
        self.tb_btn_close_app.setIconSize(QtCore.QSize(24, 24))
        #self.tb_btn_close_app.setShortcut('Ctrl+X')
        self.tb_btn_close_app.clicked.connect(self.gui_event_close_app)

        self.toolbar = QtWidgets.QToolBar()
        self.toolbar.addWidget(self.tb_btn_close_app)
        self.toolbar.addWidget(self.tb_btn_start_process)
        self.toolbar.addWidget(self.tb_btn_stop_process)
        self.tb_btn_stop_all_process_action = self.toolbar.addWidget(self.tb_btn_stop_all_process)
        self.addToolBar(self.toolbar)

    # --------------------------------------------------------------------------- #
    # Инициализация начальных значений
    # --------------------------------------------------------------------------- #
    def gui_initialization(self):
        """
        """
        #menu
        self.menu_action_stop.setDisabled(True)
        self.menu_action_stop_all.setDisabled(True)
        self.l_url_error.setVisible(False)
        # self.create_theaders_progress_bars_canvas()
        self.t_start = datetime.datetime.now()

        self.process_started = False

        self.count_requests_success = 0
        self.count_requests_4xx = 0
        self.count_requests_5xx = 0
        self.count_requests_connection_error = 0
        self.download_size = 0
        self.process_work_time = 0
        self.theaders_objs = dict()
        self.stop_theaders = False
        self.stop_all_process = False

        self.graphic_started_theaders_data = list()
        self.graphic_active_theaders_data = list()
        self.graphic_active_requests_data = list()
        self.graphic_speed_data = list()
        self.graphic_cpu_data = list()
        self.graphic_memory_data = list()
        self.graphic_requests_success_data = list()
        self.graphic_requests_4xx_data = list()
        self.graphic_requests_5xx_data = list()
        self.graphic_requests_connection_err_data = list()

        self.progress_bar_active_theaders.setMaximum(self.sb_theaders.value())
        self.progress_bar_active_theaders.setValue(0)
        self.pb_requests_success.setMaximum(
            self.sb_theaders.value() * self.sb_requests.value()
        )
        self.pb_requests_success.setValue(0)
        #
        self.pb_finished_theaders.setMaximum(self.sb_theaders.value())
        self.pb_finished_theaders.setValue(0)
        #

        self.l_kpi_theaders.setText(str(self.sb_theaders.value()))
        self.l_kpi_theaders_finished.setText(str(0))
        self.l_kpi_requests.setText(
            str(self.sb_theaders.value() * self.sb_requests.value())
        )
        self.l_kpi_requests_success.setText(str(0))
        self.l_kpi_requests_4xx.setText(str(0))
        self.l_kpi_requests_5xx.setText(str(0))
        self.l_kpi_requests_connection_error.setText(str(0))
        self.l_kpi_requests_per_seccond.setText(str(0))
        self.l_kpi_download_size.setText(str(0))
        self.l_kpi_theaders_started.setText(str(0))

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_start_process(self):
        """
        """
        self.timer_time.start(1000)
        self.timer_graf.start(self.sb_graf_timeout.value() * 1000)

        self.process_started = True

        self.w_main_settings.setDisabled(True)

        self.tb_btn_start_process.setDisabled(True)
        self.tb_btn_stop_process.setDisabled(False)
        self.tb_btn_close_app.setDisabled(True)

        #menu
        self.menu_action_start.setDisabled(True)
        self.menu_action_stop.setDisabled(False)
        self.menu_action_close.setDisabled(True)
                

        if self.sb_cycles_count.value() > 1:
            self.tb_btn_stop_all_process_action.setDisabled(False)
            self.menu_action_stop_all.setDisabled(False)
        else:
            self.tabWidget.setCurrentIndex(2)
            # self.logs_all.clear()
            # self.logs_err.clear()
            self.logs_system.clear()

        self.add_logs_system(message="Запущен процесс обработки сайта {}".format(self.get_domain_name(self.cb_urls.currentText())),
                             status_bar=True)

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_end_process(self):
        """
        """
        self.process_started = False

        self.tb_btn_start_process.setDisabled(False)
        self.tb_btn_stop_process.setDisabled(True)
        self.tb_btn_close_app.setDisabled(False)

        #menu 
        self.menu_action_start.setDisabled(False)
        self.menu_action_stop.setDisabled(True)
        self.menu_action_close.setDisabled(False)

        if self.sb_cycles_count.value() > 1:
            self.tb_btn_stop_all_process_action.setDisabled(True)
            self.menu_action_stop_all.setDisabled(True)

        self.add_logs_system(
            message="Процесс для [{}]{} успешно завершен".format(
                self.cb_request_method.currentText(),
                self.get_domain_name(self.cb_urls.currentText())
            ),
            status_bar=True)

        self.tb_btn_start_process.setDisabled(False)
        self.tb_btn_start_process.setText("Запустить")

        self.w_main_settings.setDisabled(False)

        self.timer_time.stop()
        self.timer_graf.stop()

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_initialization_urls(self):
        """
        """
        self.cb_urls.addItems(self.app_settings.get("urls"))
        self.cb_urls.setEditable(True)

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_initialization_cycles(self):
        """
        """
        self.gb_cycles_count.setVisible(False)

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_initialization_log_table(self):
        """
        """
        self.table_log_requests_model = QtGui.QStandardItemModel()
        self.table_log_requests_model.setHorizontalHeaderLabels([
            "Дата",
            "Поток",
            "Цикл",
            "Запрос",
            "Http Status Code",
            "Статус",
            "Url",
            "Метод",
            "Timeout",
            "Сообщение"
        ])
        self.tv_table_log_requests.setModel(self.table_log_requests_model)
        self.tv_table_log_requests.resizeColumnsToContents()

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_initialization_stat_table(self):
        """
        """
        self.table_stat_model = QtGui.QStandardItemModel()
        self.table_stat_model.setVerticalHeaderLabels([
            "Url",
            "Кол-во потоков",
            "Запросов на 1 поток",
            "Общее кол-во запросов",
            "CPU limit",
            "Выполнено запросов",
            "Время работы",
            "Метод запроса",
            "Скачано данных",
            "Активных потоков",
            "Запросов в 1 сек"
        ])
        self.tw_table_stat.setModel(self.table_stat_model)
        self.tw_table_stat.resizeColumnsToContents()

    # --------------------------------------------------------------------------- #
    # Показывыет главное окно программы
    # Отображение по середине экрана
    # --------------------------------------------------------------------------- #
    def show_window(self):
        """
        """
        self.show()
        desctop = QtWidgets.QApplication.desktop()
        task_bar_height = desctop.screenGeometry().height() - desctop.availableGeometry().height()
        x = (desctop.width() - self.frameSize().width()) // 2
        y = (desctop.height() - self.frameSize().height()) // 2 + task_bar_height
        self.move(x, y)

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def closeEvent(self, e):
        """
        """
        msgBox = QtWidgets.QMessageBox()
        msgBox.setIcon(QtWidgets.QMessageBox.Information)
        msgBox.setText("Закрыть программу?")
        msgBox.setWindowTitle("Информация")
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)

        btn_ok = msgBox.button(QtWidgets.QMessageBox.Ok)
        btn_ok.setText("Закрыть програму")
        btn_cancel = msgBox.button(QtWidgets.QMessageBox.Cancel)
        btn_cancel.setText("Отмена")

        msgBox.exec()

        if msgBox.clickedButton() == btn_ok:
            self.timer_cpu_collect_data.stop()
            self.timer_cpu_calculate_value.stop()
            e.accept()
            # FIXME Дописать процедуры завершения потоков
            # if not self.all_theaders_is_finished:
            #     self.on_stop_theaders()
            #     e.accept()
        else:
            e.ignore()

    # --------------------------------------------------------------------------- #
    # Для блинных url показываем только домен
    # --------------------------------------------------------------------------- #
    def get_domain_name(self, url):
        """
        """
        parsed_uri = urlparse(url)
        result = "{uri.scheme}://{uri.netloc}/".format(uri=parsed_uri)
        return result

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def on_timer_cpu_calculate_value(self):
        """
        """
        cpu_past_value = self.cpu_current_value
        if self.cpu_current_values:
            #
            self.cpu_current_value = round(sum(self.cpu_current_values) / len(self.cpu_current_values), 2)
            if len(self.cpu_current_values) > 2:
                if cpu_past_value > self.cpu_current_value:
                    self.cpu_current_trend = "&darr;"
                elif cpu_past_value == self.cpu_current_value:
                    self.cpu_current_trend = "&rarr;"
                else:
                    self.cpu_current_trend = "&uarr;"

        self.cpu_current_values = list()
        self.l_kpi_cpu.setText("{} {}".format(self.cpu_current_value, self.cpu_current_trend))

        if self.cpu_current_value < self.sb_cpu_max.value():
            self.l_kpi_cpu.setStyleSheet(
                """
                color: rgb(0, 170, 127);
                """)
            if self.process_started:
                self.add_logs_system(message="Идет обработка", status_bar=True, logs_system=False)
            else:
                self.add_logs_system(message="Программа готова к запуску", status_bar=True, logs_system=False)
        else:
            self.l_kpi_cpu.setStyleSheet(
                """
                color: rgb(255, 0, 0);
                """)
            # if int(self.l_kpi_theaders_started.text()):
            if self.process_started:
                self.add_logs_system(
                    message="Система загружена на {}% (Limit {}%). Запуск потоков и заданий приостановлен".format(
                        self.cpu_current_value,
                        self.sb_cpu_max.value()),
                    status_bar=True)
            else:
                self.add_logs_system(
                    message="Система загружена на {}% (Limit {}%)".format(self.cpu_current_value, self.sb_cpu_max.value()),
                    status_bar=True)

    # --------------------------------------------------------------------------- #
    # Запускается по таймеру в минимальном промежутке времени
    #
    # --------------------------------------------------------------------------- #
    def on_timer_cpu_collect_data(self):
        """
        """
        self.cpu_current_values.append(psutil.cpu_percent())

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def on_timer_time(self):
        """
        """
        self.gui_update_kpi()

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def on_timer_graf(self):
        """
        """
        self.graphic_main()
        self.graphic_requests()
        self.graphic_speed()
        self.graphic_cpu()
        self.graphic_memory()

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def cur_date_time(self):
        """
        """
        return datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S")

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_event_clear_stat_data(self):
        """
        """
        msgBox = QtWidgets.QMessageBox()
        msgBox.setIcon(QtWidgets.QMessageBox.Information)
        msgBox.setText("Очистить все данные из таблицы?")
        msgBox.setWindowTitle("Информация")
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)

        btn_ok = msgBox.button(QtWidgets.QMessageBox.Ok)
        btn_ok.setText("Да")
        btn_cancel = msgBox.button(QtWidgets.QMessageBox.Cancel)
        btn_cancel.setText("Отмена")

        msgBox.exec()

        if msgBox.clickedButton() == btn_ok:
            self.gui_initialization_stat_table()

    # --------------------------------------------------------------------------- #
    # 
    # --------------------------------------------------------------------------- #
    def gui_event_clear_log_requests_data(self):
        """
        """
        msgBox = QtWidgets.QMessageBox()
        msgBox.setIcon(QtWidgets.QMessageBox.Information)
        msgBox.setText("Очистить все данные из таблицы?")
        msgBox.setWindowTitle("Информация")
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)

        btn_ok = msgBox.button(QtWidgets.QMessageBox.Ok)
        btn_ok.setText("Да")
        btn_cancel = msgBox.button(QtWidgets.QMessageBox.Cancel)
        btn_cancel.setText("Отмена")

        msgBox.exec()

        if msgBox.clickedButton() == btn_ok:
            self.gui_initialization_log_table()

    # --------------------------------------------------------------------------- #
    # Сохрание лога запросов в файл
    # Ненравиться мне данный способ. Почму нельзя сразу сохранить свю модел без перебора ?
    # TODO Почитать как сохранять модель в файл
    # --------------------------------------------------------------------------- #
    def gui_event_save_file_log_requests_data(self):
        """
        """
        path = QtWidgets.QFileDialog.getSaveFileName(self, "Save File", "", "CSV(*.csv)")[0]
        if path:
            model = self.table_log_requests_model
            # get headers
            # headers = list()
            # for i in range(model.columnCount()):
            #     headers.append(model.headerData(i, QtCore.Qt.Horizontal))

            headers = [model.headerData(i, QtCore.Qt.Horizontal) for i in range(model.columnCount())]

            with open(path, "w", encoding="utf-8") as csv_file:
                writer = csv.writer(csv_file, delimiter=";", quotechar="|", quoting=csv.QUOTE_MINIMAL)
                writer.writerow(headers)
                for row in range(model.rowCount()):
                    rowdata = []
                    for column in range(model.columnCount()):
                        item = model.item(row, column)
                        if item is not None:
                            rowdata.append(item.text())
                        else:
                            rowdata.append("")
                    writer.writerow(rowdata)

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_event_show_stat_in_new_window(self):
        """
        """
        win = window_stat(
            parent=self,
            table_stat_model=self.table_stat_model)
        win.show()

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_event_show_requests_logs_in_new_window(self):
        """
        """
        win = window_logs(
            parent=self,
            table_model=self.table_log_requests_model)
        win.show()

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_event_requests_settings(self):
        """
        """
        win = window_request_settings(
            parent=self,
            app_settings=self.app_settings)
        win.show()

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_event_close_app(self):
        """
        """
        # FIXME При использвании QtWidgets.qApp.quit() не срабатывает self.closeEvent()
        # QtWidgets.qApp.quit()
        self.close()

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def menu_author(self):
        """
        """
        win = menu_author(parent=self, app_settings=self.app_settings)
        win.show()

    # --------------------------------------------------------------------------- #
    # 
    # --------------------------------------------------------------------------- #
    def menu_start(self):
        """
        """
        self.gui_event_start_program()

    # --------------------------------------------------------------------------- #
    # 
    # --------------------------------------------------------------------------- #
    def menu_close_app(self):
        """
        """
        self.close()

    # --------------------------------------------------------------------------- #
    # 
    # --------------------------------------------------------------------------- #
    def menu_stop(self):
        """
        """
        self.gui_event_stop_theaders()   

    # --------------------------------------------------------------------------- #
    # 
    # --------------------------------------------------------------------------- #
    def menu_stop_all(self):
        """
        """
        self.gui_event_stop_all_theaders()     

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def menu_about(self):
        """
        """
        win = menu_about(self)
        win.show()

    # --------------------------------------------------------------------------- #
    # Запущенные потоки / Активные потоки / Запросы в 1 сек.
    # --------------------------------------------------------------------------- #
    def graphic_main(self):
        """
        """
        self.graphics_view_main.clear()

        self.graphics_view_main.showGrid(x=True, y=True)
        self.graphics_view_main.setLabel("left", "Потоки / Запросы", units="кол-во")
        self.graphics_view_main.setLabel("bottom", "Время", units="сек.")

        # Sterted Theaders
        self.graphic_started_theaders_data.append(
            self.count_theaders_by_status(status="running") +
            self.count_theaders_by_status(status="pause"))

        self.graphics_view_main.plot(
            y=self.graphic_started_theaders_data,
            pen=pg.mkPen((0, 85, 255), width=2))

        # Active Theaders
        self.graphic_active_theaders_data.append(self.count_theaders_by_status(status="running"))

        self.graphics_view_main.plot(
            y=self.graphic_active_theaders_data,
            pen=pg.mkPen((170, 0, 0), width=2))

        # Requests per second
        self.graphic_active_requests_data.append(int(self.l_kpi_requests_per_seccond.text()))

        self.graphics_view_main.plot(
            y=self.graphic_active_requests_data,
            pen=pg.mkPen((170, 0, 255), width=2))

        # Average data
        self.label_average_started_theaders.setText("{} / {}".format(
            self.graphic_started_theaders_data[-1],
            round(sum(self.graphic_started_theaders_data) / len(self.graphic_started_theaders_data))))

        self.label_average_active_theaders.setText("{} / {}".format(
            self.graphic_active_theaders_data[-1],
            round(sum(self.graphic_active_theaders_data) / len(self.graphic_active_theaders_data))))

        self.label_average_requests_per_sec.setText("{} / {}".format(
            self.graphic_active_requests_data[-1],
            round(sum(self.graphic_active_requests_data) / len(self.graphic_active_requests_data))))

        # self.label_average_active_theaders.setText(str(round(
        #     sum(self.graphic_active_theaders_data) / len(self.graphic_active_theaders_data))))
        # self.label_average_requests_per_sec.setText(str(round(
        #     sum(self.graphic_active_requests_data) / len(self.graphic_active_requests_data))))

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def graphic_memory(self):
        """
        """
        self.graphic_memory_data.append(float(self.l_kpi_memory.text()))

        self.graphics_view_memory.clear()
        self.graphics_view_memory.plot(
            y=self.graphic_memory_data,
            pen=pg.mkPen(width=2))

        self.graphics_view_memory.showGrid(x=True, y=True)
        self.graphics_view_memory.setLabel("left", "Нагрузка", units="%")
        self.graphics_view_memory.setLabel("bottom", "Время", units="сек.")

        #
        midle_line = pg.InfiniteLine(
            movable=False,
            angle=0,
            pen=pg.mkPen((0, 204, 102), width=1),
            label="Среднее={value}",
            labelOpts={"color": (255, 255, 255), "movable": True, "fill": (0, 204, 102, 100)})

        midle_value = round(sum(self.graphic_memory_data) / len(self.graphic_memory_data))
        midle_line.setPos([0, midle_value])
        self.graphics_view_memory.addItem(midle_line)

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def graphic_cpu(self):
        """
        """
        self.graphic_cpu_data.append(self.cpu_current_value)

        self.graphics_view_cpu.clear()
        self.graphics_view_cpu.plot(
            y=self.graphic_cpu_data,
            pen=pg.mkPen(width=2))

        self.graphics_view_cpu.showGrid(x=True, y=True)
        self.graphics_view_cpu.setLabel("left", "Нагрузка", units="%")
        self.graphics_view_cpu.setLabel("bottom", "Время", units="сек.")

        #
        midle_line = pg.InfiniteLine(
            movable=False,
            angle=0,
            pen=pg.mkPen((0, 204, 102), width=1))

        midle_value = round(sum(self.graphic_cpu_data) / len(self.graphic_cpu_data), 2)
        midle_line.setPos([0, midle_value])
        self.graphics_view_cpu.addItem(midle_line)

        #
        midle_line = pg.InfiniteLine(
            movable=False,
            angle=0,
            pen=pg.mkPen((255, 0, 0), width=1),
            label="Предел={value}",
            labelOpts={"color": (255, 255, 255), "movable": True, "fill": (255, 0, 0, 100)})

        midle_value = self.sb_cpu_max.value()
        midle_line.setPos([0, midle_value])
        self.graphics_view_cpu.addItem(midle_line)

        #
        cpu_average = round(sum(self.graphic_cpu_data) / len(self.graphic_cpu_data), 2)
        cpu_average_persent = round(cpu_average * 100 / self.sb_cpu_max.value(), 2)
        self.label_cpu_current.setText(str(self.cpu_current_value))
        self.label_average_cpu.setText(str(cpu_average))
        self.label_average_cpu_persent.setText(str(cpu_average_persent))

        # cpu_average
        if cpu_average > self.sb_cpu_max.value():
            self.gb_average_cpu.setStyleSheet("background-color: rgb(255, 112, 77); color: rgb(255, 255, 255);")
        else:
            self.gb_average_cpu.setStyleSheet("background-color: rgb(0, 204, 102); color: rgb(255, 255, 255);")
        # cpu_current_value
        if self.cpu_current_value > self.sb_cpu_max.value():
            self.gb_cpu_current.setStyleSheet("background-color: rgb(255, 112, 77); color: rgb(255, 255, 255);")
        else:
            self.gb_cpu_current.setStyleSheet("background-color: rgb(0, 204, 102); color: rgb(255, 255, 255);")
        # cpu_average_persent
        if cpu_average_persent >= 100:
            self.gb_average_cpu_persent.setStyleSheet("background-color: rgb(255, 112, 77); color: rgb(255, 255, 255);")
        else:
            self.gb_average_cpu_persent.setStyleSheet("background-color: rgb(0, 204, 102); color: rgb(255, 255, 255);")

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def graphic_speed(self):
        """
        """
        self.graphic_speed_data.append(float(self.l_kpi_speed.text()))

        self.graphics_view_speed.clear()
        self.graphics_view_speed.plot(
            y=self.graphic_speed_data,
            pen=pg.mkPen(width=2))

        self.graphics_view_speed.showGrid(x=True, y=True)
        self.graphics_view_speed.setLabel("left", "Скорость", units="Mb/Kb/s")
        self.graphics_view_speed.setLabel("bottom", "Время", units="сек.")

        midle_line = pg.InfiniteLine(
            movable=False,
            angle=0,
            pen=pg.mkPen((0, 204, 102), width=1),
            label="Среднее={value}",
            labelOpts={"color": (255, 255, 255), "movable": True, "fill": (0, 204, 102, 100)})

        midle_value = round(sum(self.graphic_speed_data) / len(self.graphic_speed_data), 2)
        midle_line.setPos([0, midle_value])
        self.graphics_view_speed.addItem(midle_line)

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def graphic_requests(self):
        """
        """
        persent_requests_success = round((int(self.l_kpi_requests_success.text()) * 100)
                                         / int(self.l_kpi_requests.text()), 2)
        self.graphic_requests_success_data.append(persent_requests_success)

        persent_requests_4xx = round((int(self.l_kpi_requests_4xx.text()) * 100)
                                     / int(self.l_kpi_requests.text()), 2)
        self.graphic_requests_4xx_data.append(persent_requests_4xx)

        persent_requests_5xx = round((int(self.l_kpi_requests_5xx.text()) * 100)
                                     / int(self.l_kpi_requests.text()), 2)
        self.graphic_requests_5xx_data.append(persent_requests_5xx)

        persent_requests_connection_err = round((int(self.l_kpi_requests_connection_error.text()) * 100)
                                                / int(self.l_kpi_requests.text()), 2)
        self.graphic_requests_connection_err_data.append(persent_requests_connection_err)

        all_errors = (int(self.l_kpi_requests_4xx.text()) +
                      int(self.l_kpi_requests_5xx.text()) +
                      int(self.l_kpi_requests_connection_error.text()))

        self.graphics_view_requests.clear()
        self.graphics_view_requests.showGrid(x=True, y=True)
        self.graphics_view_requests.setLabel("left", "Запросы", units="%")
        self.graphics_view_requests.setLabel("bottom", "Время", units="сек.")

        self.graphics_view_requests.plot(
            y=self.graphic_requests_success_data,
            pen=pg.mkPen((0, 204, 102), width=2))

        self.graphics_view_requests.plot(
            y=self.graphic_requests_4xx_data,
            pen=pg.mkPen((255, 102, 102), width=2))

        self.graphics_view_requests.plot(
            y=self.graphic_requests_5xx_data,
            pen=pg.mkPen((255, 112, 77), width=2))

        self.graphics_view_requests.plot(
            y=self.graphic_requests_connection_err_data,
            pen=pg.mkPen((255, 51, 0), width=2))

        #
        midle_line = pg.InfiniteLine(
            movable=False,
            angle=0,
            pen=pg.mkPen((0, 204, 102), width=1),
            label="Успешных={value}%",
            labelOpts={"color": (255, 255, 255), "movable": True, "fill": (0, 204, 102, 100)})

        midle_value = persent_requests_success
        midle_line.setPos([0, midle_value])
        self.graphics_view_requests.addItem(midle_line)

        #
        midle_line = pg.InfiniteLine(
            movable=False,
            angle=0,
            pen=pg.mkPen((255, 0, 0), width=1),
            label="С ошибками={value}%",
            labelOpts={"color": (255, 255, 255), "movable": True, "fill": (255, 0, 0, 100)})

        midle_value = round((all_errors * 100) / int(self.l_kpi_requests.text()), 2)
        midle_line.setPos([0, midle_value])
        self.graphics_view_requests.addItem(midle_line)

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_event_change_use_request_settings(self):
        """
        """
        if self.cb_request_settings.currentIndex() == 1:
            self.btn_requests_settings.setDisabled(False)
        else:
            self.btn_requests_settings.setDisabled(True)

    # --------------------------------------------------------------------------- #
    # 
    # --------------------------------------------------------------------------- #
    def gui_event_cb_request_result_type(self):
        """
        """
        self.table_log_requests_filter_model.setFilterKeyColumn(5)
        if self.cb_request_result_type.currentIndex() == 1:
            self.table_log_requests_filter_model.setFilterFixedString("ОК")
        elif self.cb_request_result_type.currentIndex() == 2:
            self.table_log_requests_filter_model.setFilterFixedString("Ошибка")
        else:
            self.table_log_requests_filter_model.setFilterFixedString("")

        self.tv_table_log_requests.setModel(self.table_log_requests_filter_model)
        self.tv_table_log_requests.scrollToBottom()
        self.tv_table_log_requests.resizeColumnsToContents()            

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_event_change_request_method(self):
        """
        """
        if self.cb_request_method.currentText() == "get" or self.cb_request_method.currentText() == "post":
            self.groupBox_8.setTitle("Загружено Mb")
            self.btn_requests_settings.setDisabled(True)
            self.cb_request_settings.setDisabled(False)

        if self.cb_request_method.currentText() == "head":
            self.groupBox_8.setTitle("Загружено Kb")
            self.btn_requests_settings.setDisabled(True)
            self.cb_request_settings.setDisabled(True)

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_event_change_active_theaders(self):
        """
        """
        self.l_kpi_theaders.setText(str(self.sb_theaders.value()))
        self.l_kpi_requests.setText(
            str(self.sb_theaders.value() * self.sb_requests.value())
        )

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_event_change_cycles_count(self):
        """
        """
        if self.sb_cycles_count.value() > 1:
            self.tb_btn_stop_all_process_action.setVisible(True)
            self.tb_btn_stop_all_process_action.setDisabled(True)
            self.gb_cycles_count.setVisible(True)
            self.l_cycles_count.setText("{} / {}".format(self.sb_cycles_count.value(), 0))
        else:
            self.gb_cycles_count.setVisible(False)
            self.tb_btn_stop_all_process_action.setVisible(False)
            self.tb_btn_stop_all_process_action.setDisabled(True)

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_event_change_count_requests_by_active_theaders(self):
        """
        """
        self.l_kpi_requests.setText(
            str(self.sb_theaders.value() * self.sb_requests.value())
        )

    # --------------------------------------------------------------------------- #
    # Generate User-Agent
    # --------------------------------------------------------------------------- #
    def gen_new_user_agent(self):
        """
        Generate User-Agent
        """
        return generate_user_agent(os=("win", "mac", "linux"), device_type=("desktop",))

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def on_theader_log_message2(self,
                               theaders_id,
                               iteration,
                               cycle_count,
                               status_code,
                               url,
                               request_method,
                               request_timeout,
                               message,
                               message_type):
        """
        """
        pass

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def on_theader_log_message(self,
                               theaders_id,
                               iteration,
                               cycle_count,
                               status_code,
                               url,
                               request_method,
                               request_timeout,
                               message,
                               message_type):
        """
        """
        self.mutex.lock()

        info_msg = QtGui.QStandardItem()
        if status_code and int(status_code) in [200, 301, 302]:
            info_msg.setText("ОК")
            info_msg.setBackground(QtGui.QColor(85, 255, 127))
        else:
            info_msg.setText("Ошибка")
            info_msg.setBackground(QtGui.QColor(255, 85, 127))

        self.table_log_requests_model.appendRow([
            QtGui.QStandardItem(str(self.cur_date_time())),
            QtGui.QStandardItem(str(theaders_id)),
            QtGui.QStandardItem(str(cycle_count + 1)),
            QtGui.QStandardItem(str(iteration)),
            QtGui.QStandardItem(str(status_code)),
            info_msg,  # QtGui.QStandardItem(str(message_type)),
            QtGui.QStandardItem(str(url)),
            QtGui.QStandardItem(str(request_method)),
            QtGui.QStandardItem(str(request_timeout)),
            QtGui.QStandardItem(str(message)),
        ])
        # filter model
        self.table_log_requests_filter_model = QtCore.QSortFilterProxyModel()
        self.table_log_requests_filter_model.setSourceModel(self.table_log_requests_model)

        self.table_log_requests_filter_model.setFilterKeyColumn(5)

        if self.cb_request_result_type.currentIndex() == 1:
            self.table_log_requests_filter_model.setFilterFixedString("ОК")
        elif self.cb_request_result_type.currentIndex() == 2:
            self.table_log_requests_filter_model.setFilterFixedString("Ошибка")
        else:
            self.table_log_requests_filter_model.setFilterFixedString("")            


        self.tv_table_log_requests.setModel(self.table_log_requests_filter_model)
        self.tv_table_log_requests.scrollToBottom()
        self.tv_table_log_requests.resizeColumnsToContents()

        self.mutex.unlock()

        # self.add_logs_requests(
        #     theader_id=theaders_id,
        #     status_code=status_code,
        #     message=message,
        #     message_type=message_type)

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    # def add_logs_requests(self, theader_id, status_code, message, message_type):
    #     """
    #     """
    #     self.logs_all.appendPlainText(
    #         "{} \t {} \t {} \t {} \t {}".format(
    #             self.cur_date_time(), theader_id, status_code, message_type, message.strip()
    #         )
    #     )
    #     if message_type == "error":
    #         self.logs_err.appendPlainText(
    #             "{} \t {} \t {}".format(
    #                 self.cur_date_time(), theader_id, message.strip()
    #             )
    #         )

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def add_logs_system(self, message, status_bar=False, logs_system=True):
        """
        """
        if logs_system:
            self.logs_system.appendPlainText(
                "{} \t {}".format(
                    self.cur_date_time(), message.strip()
                )
            )
        if status_bar:
            self.statusBar().showMessage(message)

    # --------------------------------------------------------------------------- #
    # Как же муторно создавать gui в ручную... :(
    # Создаем gui для динамического формирования theaders progres bars
    # --------------------------------------------------------------------------- #
    def gui_initialization_theaders_progress_bars_canvas(self):
        """
        """
        self.pg_theaders_widget_parent = QtWidgets.QWidget()
        self.pg_theaders_widget_layout_parent = QtWidgets.QVBoxLayout(self.pg_theaders_widget_parent)

        self.pg_theaders_widget = QtWidgets.QWidget()
        self.pg_theaders_widget_layout = QtWidgets.QVBoxLayout(self.pg_theaders_widget)
        self.pg_theaders_widget_layout_parent.addWidget(self.pg_theaders_widget)
        spacer_theaders = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.pg_theaders_widget_layout_parent.addItem(spacer_theaders)
        self.sa_prorgess_bars.setWidget(self.pg_theaders_widget_parent)
        QtWidgets.qApp.processEvents()

    # --------------------------------------------------------------------------- #
    # Смена IP
    # Работает только при использовании TOR
    # Пока не реализовал
    # TODO Реализовать смену IP через TOR
    # --------------------------------------------------------------------------- #
    def chech_if_need_new_curcle(self):
        """
        """
        if int(self.l_kpi_requests_connection_error.text()) >= self.sb_requests_max_errors.value():
            self.add_logs_system(message="Превышено максимальное кол-во ошибочных завпросов")

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def check_url_http_status_code(self, url):
        """
        """
        headers = {
            "User-Agent": self.gen_new_user_agent(),
        }
        try:
            response = requests.head(url=url, headers=headers, timeout=self.sb_request_timeout.value())
            if response.status_code in [200, 301, 302]:
                return True
            else:
                return False
        except Exception:
            return False

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def check_url_popup(self, is_show=True):
        """
        """
        msgBox = QtWidgets.QDialog()
        if is_show:
            msgBox.show()
        else:
            msgBox.hide()

    # --------------------------------------------------------------------------- #
    # Проверяем url сайта
    # 1. Введен ли url сайта (не пустое значени)
    # 2. Проверяем http status code (200, 301, 302) - иначе - ошибка
    # --------------------------------------------------------------------------- #

    def check_url(self):
        """
        """
        self.add_logs_system(message="Проверяю настройки", status_bar=True)
        self.tb_btn_start_process.setDisabled(True)
        self.tb_btn_close_app.setDisabled(True)

        self.l_url_error.setVisible(False)

        popup = window_popup(
            popup_title="Проверка настроек",
            popup_type="info",
            popup_text="Проверяю настроки программы. Ожидайте...",
            parent=self)
        popup.show()
        QtWidgets.qApp.processEvents()

        if not self.cb_urls.currentText():
            self.l_url_error.setVisible(True)
            self.l_url_error.setStyleSheet(
                """
                color: rgb(255, 255, 255); 
                background-color: rgb(255, 0, 0);
                padding: 0px 10px 0px 10px;
                border-radius: 3px;
                """
            )
            self.l_url_error.setText("Укажите URL сайта")
            self.add_logs_system(message="Укажите URL сайта", status_bar=True)
            self.tb_btn_start_process.setDisabled(False)
            self.tb_btn_close_app.setDisabled(False)
            self.tabWidget.setCurrentIndex(0)
            popup.hide()
            return False

        if self.cb_urls.currentText() and not self.check_url_http_status_code(url=self.cb_urls.currentText()):
            self.l_url_error.setVisible(True)
            self.l_url_error.setStyleSheet(
                """
                color: rgb(255, 255, 255); 
                background-color: rgb(255, 0, 0);
                padding: 0px 10px 0px 10px;
                border-radius: 3px;
                """
            )
            self.l_url_error.setText("Сайт недоступен")

            self.add_logs_system(
                message="Сайт {} недоступен".format(self.cb_urls.currentText()),
                status_bar=True)
            self.tb_btn_start_process.setDisabled(False)
            self.tb_btn_close_app.setDisabled(False)

            self.tb_btn_start_process.setText("Запустить")
            self.tabWidget.setCurrentIndex(0)
            popup.hide()
            return False
        else:
            self.add_logs_system(message="Проверка успешно пройдена", status_bar=True)
            self.tabWidget.setCurrentIndex(2)
            self.tb_btn_start_process.setDisabled(False)

        popup.hide()
        return True

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def add_statistics(self):
        """
        """
        average_requests_per_sec = round(sum(self.graphic_active_requests_data) / len(self.graphic_active_requests_data))
        average_active_theaders = round(sum(self.graphic_active_theaders_data) / len(self.graphic_active_theaders_data))

        self.table_stat_model.appendColumn([
            QtGui.QStandardItem(str(self.cb_urls.currentText())),
            QtGui.QStandardItem(str(self.sb_theaders.value())),
            QtGui.QStandardItem(str(self.sb_requests.value())),
            QtGui.QStandardItem(str(self.l_kpi_requests.text())),
            QtGui.QStandardItem(str(self.sb_cpu_max.value())),
            QtGui.QStandardItem(str(self.l_kpi_requests_success.text())),
            QtGui.QStandardItem(str(self.l_kpi_prg_running_time.text())),
            QtGui.QStandardItem(str(self.cb_request_method.currentText())),
            QtGui.QStandardItem(str(self.l_kpi_download_size.text())),
            QtGui.QStandardItem(str(average_active_theaders)),
            QtGui.QStandardItem(str(average_requests_per_sec)),
        ])
        self.tw_table_stat.setModel(self.table_stat_model)
        self.tw_table_stat.resizeColumnsToContents()

    # --------------------------------------------------------------------------- #
    # Подсчет кол-ва потоков которые находятся на паузе потому что превышен
    # лимит по нагрузке на CPU
    # --------------------------------------------------------------------------- #
    def count_theaders_by_status(self, status):
        """
        """
        count = 0
        for theader_id in self.theaders_objs:
            if self.theaders_objs[theader_id]["theader_status"] == status:
                count += 1

        return count

    # --------------------------------------------------------------------------- #
    # 
    # --------------------------------------------------------------------------- #
    def on_theader_iteration2(self, theader_id, iteration, cpu_value, theader_status):
        """
        """
        pass

    # --------------------------------------------------------------------------- #
    # Динамически добавляем progres bar для нового theader и увеличиваем value при
    # каждом срабатывании события on_theader_iteration
    #
    # Не нравится мне фигня с удалением progres bar для завершенного потока pg.setVisible(False)
    # TODO Найти как правильно удалить widget с формы
    # --------------------------------------------------------------------------- #
    def on_theader_iteration(self, theader_id, iteration, cpu_value, theader_status):
        """
        """
        # Если PG существует
        #self.mutex.lock()
        pg = self.findChild(QtWidgets.QProgressBar, "pg_{}".format(theader_id))
        if pg:
            if theader_status:
                self.theaders_objs["theader_"+str(theader_id)]["theader_status"] = "stoped"
                theader_status = "stoped"
                pg.setStyleSheet(
                    """
                    text-align: left;
                    background-color: rgb(255, 128, 128);
                    """
                )
            elif cpu_value > self.sb_cpu_max.value():
                self.theaders_objs["theader_"+str(theader_id)]["theader_status"] = "pause"
                theader_status = "pause"
                pg.setStyleSheet(
                    """
                    text-align: left;
                    background-color: rgb(255, 170, 127);
                    """
                )
            else:
                self.theaders_objs["theader_"+str(theader_id)]["theader_status"] = "running"
                pg.setValue(iteration)
                theader_status = "running"
                pg.setStyleSheet(
                    """
                    text-align: left;
                    background-color: rgb(173, 235, 173);
                    """
                )
            pg.setFormat(" Поток #{}. Выполнено запросов %v из %m ({} (CPU {}% / {}%))".format(
                theader_id,
                theader_status,
                cpu_value,
                round(self.cpu_current_value)
            ))
            if pg.value() == self.sb_requests.value():
                pg.setVisible(False)
            else:
                self.theaders_objs["theader_"+str(theader_id)]["theader_data"].cpu_current_value = self.cpu_current_value
        # Если PG не существует
        else:
            pg = QtWidgets.QProgressBar(
                self.pg_theaders_widget_parent,
                minimum=0,
                maximum=self.sb_requests.value()
            )
            pg.setValue(1)
            pg.setObjectName("pg_{}".format(theader_id))
            pg.setFormat(" Поток #{}. Выполнено запросов %v из %m (running (CPU {}% / {}%))".format(
                theader_id,
                cpu_value,
                round(self.cpu_current_value)
            ))
            pg.setStyleSheet(
                """
                text-align: left;
                background-color: rgb(173, 235, 173);
                """
            )
            self.pg_theaders_widget_layout.addWidget(pg)
        #QtWidgets.qApp.processEvents()
        #self.mutex.unlock()

    # --------------------------------------------------------------------------- #
    # Собитые потока - on_theader_request
    # --------------------------------------------------------------------------- #
    def on_theader_request(self, request_type, status_code, download_size):
        """
        """
        self.mutex.lock()
        if request_type == "request":
            if status_code in [200, 301, 302]:
                # Download size
                self.download_size += download_size
                # Count of success requests
                self.count_requests_success += 1
            if status_code >= 400 and status_code < 500:
                # Count of 4XX requests
                self.count_requests_4xx += 1
            if status_code >= 500:
                # Count of 5XX requests
                self.count_requests_5xx += 1
        if request_type == "connection":
            # Count of connection err requests
            self.count_requests_connection_error += 1
            self.chech_if_need_new_curcle()
        self.mutex.unlock()

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_event_stop_all_theaders(self):
        """
        """
        #self.stop_theaders = True
        self.stop_all_process = True

        self.gui_event_stop_theaders()

    # --------------------------------------------------------------------------- #
    # Принудительно останавлиаем потоки по событию
    # --------------------------------------------------------------------------- #
    def gui_event_stop_theaders(self):
        """
        """
        self.stop_theaders = True

        self.tb_btn_stop_process.setDisabled(True)
        if self.sb_cycles_count.value() > 1:
            self.tb_btn_stop_all_process_action.setDisabled(True)

        self.add_logs_system(message="Останавливаю потоки...", status_bar=True)

        # TODO Переписать цыкл
        for theader in self.theaders_objs:
            QtWidgets.qApp.processEvents()
            # th.stop_theader()
            self.theaders_objs[theader]["theader_data"].stop_theader()

    # --------------------------------------------------------------------------- #
    # Событие потока - Поток запустился
    # TODO Переписать на использвание dict theaders_objs вместо переменных
    # --------------------------------------------------------------------------- #
    def on_theader_started(self, theader_id):
        """
        """
        self.theaders_objs["theader_"+str(theader_id)]["theader_status"] = "running"

    # --------------------------------------------------------------------------- #
    # Событие потока - Поток окончил свою работу
    # TODO Переписать на использвание dict theaders_objs вместо переменных
    # --------------------------------------------------------------------------- #
    def on_theader_finished(self, theader_id):
        """
        """
        self.theaders_objs["theader_"+str(theader_id)]["theader_status"] = "finished"

        if self.stop_theaders:
            self.add_logs_system(
                message="Останавливаю потоки...{}".format(self.count_theaders_by_status(status="finished")),
                status_bar=True)

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def get_process_time_in_seconds(self):
        """
        """
        t_current = datetime.datetime.now()
        t_work = t_current - self.t_start

        return t_work.total_seconds()

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_kpi_time_update(self):
        """
        """
        self.l_kpi_prg_running_time.setText(str(datetime.timedelta(seconds=self.get_process_time_in_seconds()))[:7])

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_kpi_estimated_time_update(self):
        """
        """
        if int(self.l_kpi_requests_per_seccond.text()):
            estimated_time_to_end_seconds = ((self.sb_theaders.value() *
                                              self.sb_requests.value()) /
                                             int(self.l_kpi_requests_per_seccond.text()))
            self.l_kpi_prg_running_time_forecast.setText(str(datetime.timedelta(seconds=estimated_time_to_end_seconds))[:7])
        else:
            self.l_kpi_prg_running_time_forecast.setText("???")

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_kpi_requests_per_second_update(self):
        """
        """
        requests_per_seconds = round(self.count_requests_success / self.get_process_time_in_seconds())
        self.l_kpi_requests_per_seccond.setText(str(requests_per_seconds))

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_kpi_finished_theaders_update(self):
        """
        """
        self.l_kpi_theaders_finished.setText(str(self.count_theaders_by_status(status="finished")))

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_kpi_wait_to_start_theaders_update(self):
        """
        """
        self.l_kpi_theaders_waiting.setText(
            str(self.sb_theaders.value() -
                (self.count_theaders_by_status(status="running") +
                 self.count_theaders_by_status(status="pause") +
                 self.count_theaders_by_status(status="finished"))))

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_kpi_active_theaders_update(self):
        """
        """
        self.progress_bar_active_theaders.setMaximum(self.sb_theaders.value())
        self.progress_bar_active_theaders.setValue(
            self.count_theaders_by_status(status="running"))
        self.l_kpi_theaders_active.setText(
            str(self.count_theaders_by_status(status="running")))

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_kpi_active_theaders_avg_update(self):
        """
        """
        self.l_kpi_theaders_active_avg.setText(str(round(
            sum(self.graphic_active_theaders_data) / len(self.graphic_active_theaders_data))))

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_kpi_started_theaders_avg_update(self):
        """
        """
        self.l_kpi_theaders_started_avg.setText(str(round(
            sum(self.graphic_started_theaders_data) / len(self.graphic_started_theaders_data))))

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_kpi_started_theaders_update(self):
        """
        """
        self.l_kpi_theaders_started.setText(
            str(self.count_theaders_by_status(status="running") +
                self.count_theaders_by_status(status="pause")))

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_kpi_paused_theaders_update(self):
        """
        """
        self.l_kpi_theaders_paused.setText(str(self.count_theaders_by_status(status="pause")))

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_kpi_download_size_update(self):
        """
        """
        if self.cb_request_method.currentText() == "get" or self.cb_request_method.currentText() == "post":
            self.l_kpi_download_size.setText(str("{}".format(round(self.download_size / 1048576))))
        if self.cb_request_method.currentText() == "head":
            self.l_kpi_download_size.setText(str("{}".format(round(self.download_size / 1024))))

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_kpi_requests_success_update(self):
        """
        """
        self.pb_requests_success.setValue(self.count_requests_success)
        self.l_kpi_requests_success.setText(str(self.count_requests_success))

        requests_success_persent = round(self.count_requests_success * 100 /
                                         (self.sb_theaders.value() *
                                          self.sb_requests.value()), 2)
        self.l_requests_success.setText("{} / {}%".format(
            self.count_requests_success,
            requests_success_persent
        ))

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_kpi_requests_errors_update(self):
        """
        """
        requests_errors = (self.count_requests_4xx +
                           self.count_requests_5xx +
                           self.count_requests_connection_error)
        requests_errors_persent = round(requests_errors * 100 /
                                        (self.sb_theaders.value() *
                                         self.sb_requests.value()), 2)
        self.l_requests_errors.setText("{} / {}%".format(
            requests_errors,
            requests_errors_persent
        ))

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_kpi_requests_4xx_error_update(self):
        """
        """
        self.l_kpi_requests_4xx.setText(str(self.count_requests_4xx))

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_kpi_requests_5xx_error_update(self):
        """
        """
        self.l_kpi_requests_5xx.setText(str(self.count_requests_5xx))

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_kpi_requests_connection_error_update(self):
        """
        """
        self.l_kpi_requests_connection_error.setText(str(self.count_requests_connection_error))

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_kpi_calculate_speed_update(self):
        """
        """
        if self.cb_request_method.currentText() == "get" or self.cb_request_method.currentText() == "post":
            self.groupBox_26.setTitle("Скорость (Mb/s)")
            self.l_kpi_speed.setText("{}".format(round((self.download_size / self.get_process_time_in_seconds()) / 1048576, 2)))
        if self.cb_request_method.currentText() == "head":
            self.groupBox_26.setTitle("Скорость (Kb/s)")
            self.l_kpi_speed.setText("{}".format(round((self.download_size / self.get_process_time_in_seconds()) / 1, 2)))

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_kpi_cpu_update(self):
        """
        """
        if self.cpu_current_trend == "up":
            trend = "&uarr;"
        if self.cpu_current_trend == "down":
            trend = "&darr;"
        if self.cpu_current_trend == "line":
            trend = "&rarr;"
        self.l_kpi_cpu.setText("{} {}".format(self.cpu_current_value, trend))

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_kpi_memory_update(self):
        """
        """
        self.memory_current_value = psutil.virtual_memory().percent
        self.l_kpi_memory.setText("{}".format(self.memory_current_value))

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_kpi_prograss_bars_update(self):
        """
        """
        # self.pb_finished_theaders.setMaximum(self.sb_theaders.value())
        self.pb_finished_theaders.setValue(self.count_theaders_by_status(status="finished"))

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_update_kpi(self):
        """
        """
        self.gui_kpi_time_update()
        self.gui_kpi_requests_per_second_update()
        self.gui_kpi_estimated_time_update()
        self.gui_kpi_finished_theaders_update()
        self.gui_kpi_wait_to_start_theaders_update()
        self.gui_kpi_active_theaders_update()
        self.gui_kpi_active_theaders_avg_update()
        self.gui_kpi_started_theaders_avg_update()
        self.gui_kpi_started_theaders_update()
        self.gui_kpi_paused_theaders_update()
        self.gui_kpi_download_size_update()
        self.gui_kpi_requests_success_update()
        self.gui_kpi_requests_errors_update()
        self.gui_kpi_requests_4xx_error_update()
        self.gui_kpi_requests_5xx_error_update()
        self.gui_kpi_requests_connection_error_update()
        self.gui_kpi_calculate_speed_update()
        # self.gui_kpi_cpu_update()
        self.gui_kpi_memory_update()
        self.gui_kpi_prograss_bars_update()

        QtWidgets.qApp.processEvents()

    # --------------------------------------------------------------------------- #
    # 
    # --------------------------------------------------------------------------- #
    def get_tests_value(self, cycle_count, val, def_val):
        """
        """
        try:
          return self.app_tests[cycle_count].get(val, def_val)
        except Exception:
            self.add_logs_system("Нет тестовых данных для текущего процесса {}".format(cycle_count + 1))
            self.add_logs_system("Для текущего процесса будут использоваться данные по умолчанию")            
            return def_val  

    # --------------------------------------------------------------------------- #
    # Если кол-во циклов запуска программы больше 1 то пробуем получить
    # настроки программы из файла. Если файла нет то все циклы будут
    # запускать с настройками по умолчанию
    # --------------------------------------------------------------------------- #
    def check_tests_settings(self, cycle_count):
        """
        """
        if self.sb_cycles_count.value() > 1:
            self.l_cycles_count.setText("{} / {}".format(self.sb_cycles_count.value(), cycle_count + 1))
            if self.app_tests:
                self.sb_cpu_max.setValue(self.get_tests_value(cycle_count, "cpu_limit", self.sb_cpu_max.value()))
                self.sb_theaders.setValue(self.get_tests_value(cycle_count, "theaders", self.sb_theaders.value()))
                self.sb_requests.setValue(self.get_tests_value(cycle_count, "requests", self.sb_requests.value()))

    # --------------------------------------------------------------------------- #
    # Получать зачени CPU можно и напрямую из потоков но такой подход по
    # какой-то неведомой причине работает медленно и не стабильно
    # Почему не стабильно - потому что как-то коряво получает данные CPU
    # А вот почему медленно вообще не понятно. Поидее дергание потоков как в этом случае
    # полюбому должно влиять на скорость работы но эффект получается обратный
    # --------------------------------------------------------------------------- #
    def set_theaders_system_cpu(self):
        """
        """
        QtWidgets.qApp.processEvents()
        # for theader in self.theaders_objs:
        #     self.theaders_objs[theader]["theader_data"].cpu_current_value = self.cpu_current_value
        #     print("{} - {}".format(theader, self.cpu_current_value))
        #     QtWidgets.qApp.processEvents()

    # --------------------------------------------------------------------------- #
    # Запуск потоков
    # --------------------------------------------------------------------------- #
    def gui_event_start_program(self):
        """
        """
        if self.check_url():
            self.threadpool.setMaxThreadCount(self.sb_theaders.value())
            for cycle_count in range(0, self.sb_cycles_count.value()):
                self.check_tests_settings(cycle_count)

                self.gui_initialization_theaders_progress_bars_canvas()
                self.gui_initialization()
                self.gui_start_process()

                theader_id = 1
                while theader_id <= self.sb_theaders.value():
                    self.set_theaders_system_cpu()
                    if self.stop_theaders:
                        break
                    if self.cpu_current_value > self.sb_cpu_max.value():
                        time.sleep(0.1)
                        continue
                    try:
                        theader = single_requsts_theader(
                            parent=self,
                            theader_id=theader_id,
                            url=self.cb_urls.currentText(),
                            count_of_requests=self.sb_requests.value(),
                            request_timeout=self.sb_request_timeout.value(),
                            request_method=self.cb_request_method.currentText(),
                            cycle_count=cycle_count,
                            cpu_max_value=self.sb_cpu_max.value(),
                            cpu_current_value=self.cpu_current_value)
                        # , QtCore.Qt.QueuedConnection
                        theader.signals.on_request.connect(self.on_theader_request)
                        theader.signals.on_log_message.connect(self.on_theader_log_message)
                        theader.signals.on_iteration.connect(self.on_theader_iteration)
                        theader.signals.on_theader_finished.connect(self.on_theader_finished)
                        theader.signals.on_theader_started.connect(self.on_theader_started)
                        #theader.start()
                        self.threadpool.start(theader)

                        self.theaders_objs["theader_"+str(theader_id)] = {
                            "theader_name": "theader_"+str(theader_id),
                            "theader_status": "ranning",
                            "theader_data": theader,
                        }

                    except Exception as err:
                        self.add_logs_system(message="Немогу создать поток... {}".format(err))
                    finally:
                        theader_id += 1

                while True:
                    if self.count_theaders_by_status(status="finished") == len(self.theaders_objs):
                        break
                    self.set_theaders_system_cpu()

                self.add_statistics()
                self.gui_end_process()
                self.gui_update_kpi()

                if self.stop_all_process:
                    break
            #
            popup = window_popup(
                popup_title="Информация",
                popup_type="dialog",
                popup_text="Программа успешно завершила работу",
                parent=self)
            popup.show()


# ------------------------------------------------------------------------------- #
# Main func
# ------------------------------------------------------------------------------- #
if __name__ == "__main__":
    """
    """
    app = QtWidgets.QApplication(sys.argv)
    win = main_gui()
    win.show_window()
    sys.exit(app.exec_())
