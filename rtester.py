import requests
#import random
#import math
import json
import sys
import csv
import os
import datetime
import time
import psutil
#import pyqtgraph as pg
from urllib.parse import urlparse
from user_agent import generate_user_agent
from PyQt5 import QtWidgets, QtCore, QtGui, uic

import modules.thread as thread
import modules.gui_popup as gui_popup
import modules.gui_stat as gui_stat
import modules.gui_logs as gui_logs
import modules.gui_author as gui_author
import modules.gui_about as gui_about
import modules.gui_request_settings as gui_request_settings
import modules.grafs as grafs
import modules.gui_confirm as gui_confirm
import modules.gui_toolbar as gui_toolbar


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

        self.app_settings = self.import_json_settings()
        self.app_tests = self.import_json_tests()

        self.setWindowTitle("{} {}".format(
            self.app_settings.get("program_name"),
            self.app_settings.get("program_version"))
        )

        self.timer_update_kpi = QtCore.QTimer(self)
        self.timer_update_kpi.timeout.connect(self.on_timer_update_kpi)
        self.timer_update_graf = QtCore.QTimer(self)
        self.timer_update_graf.timeout.connect(self.on_timer_update_graf)
        self.timer_cpu_collect_data = QtCore.QTimer(self)
        self.timer_cpu_collect_data.timeout.connect(
            self.on_timer_cpu_collect_data)
        self.timer_cpu_calculate_value = QtCore.QTimer(self)
        self.timer_cpu_calculate_value.timeout.connect(
            self.on_timer_cpu_calculate_value)

        #
        self.btn_requests_settings.clicked.connect(
            self.gui_event_requests_settings)
        self.btn_show_stat_in_new_window.clicked.connect(
            self.gui_event_show_stat_in_new_window)
        self.btn_show_requests_logs_in_new_window.clicked.connect(
            self.gui_event_show_requests_logs_in_new_window)
        self.btn_clear_stat_data.clicked.connect(
            self.gui_event_clear_stat_data)
        self.btn_clear_log_requests_data.clicked.connect(
            self.gui_event_clear_log_requests_data)
        self.btn_save_file_log_requests_data.clicked.connect(
            self.gui_event_save_file_log_requests_data)

        self.sb_theaders.valueChanged.connect(
            self.gui_event_change_active_theaders)
        self.sb_requests_per_theader.valueChanged.connect(
            self.gui_event_change_count_requests_by_active_theaders)
        self.sb_cycles_count.valueChanged.connect(
            self.gui_event_change_cycles_count)
        self.cb_request_method.currentTextChanged.connect(
            self.gui_event_change_request_method)
        self.cb_request_settings.currentTextChanged.connect(
            self.gui_event_change_use_request_settings)
        self.cb_request_result_type.currentTextChanged.connect(
            self.gui_event_cb_request_result_type)
        #
        self.grafs = grafs.grafs(parent=self)
        self.gui_toolbar = gui_toolbar.toolbar(parent=self)

        self.menu_action_about.triggered.connect(self.menu_about)
        self.menu_action_author.triggered.connect(self.menu_author)
        self.menu_action_start.triggered.connect(self.menu_start)
        self.menu_action_close.triggered.connect(self.menu_close_app)
        self.menu_action_stop.triggered.connect(self.menu_stop)
        self.menu_action_stop_all.triggered.connect(self.menu_stop_all)
        self.menu_action_toolbar_show.triggered.connect(self.menu_toolbar_show)
        self.menu_action_toolbar_hide.triggered.connect(self.menu_toolbar_hide)

        self.set_style_sheet()
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

        # self.grafs = grafs.grafs(main_window=self)
        # self.gui_toolbar = gui_toolbar.toolbar(main_window=self)

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def import_json_settings(self):
        """
        """
        with open('settings.txt', encoding='utf-8') as json_file:
            settings = json.load(json_file)
        return settings

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def import_json_tests(self):
        """
        """
        if os.path.isfile("tests.txt"):
            with open('tests.txt', encoding='utf-8') as json_file:
                settings = json.load(json_file)
            if settings:
                return settings
            else:
                self.add_logs_system(
                    message=("Файл {} присутствует но пустой либо "
                             "неправильного формата").format("tests.txt"))
                return False
        else:
            self.add_logs_system(
                message=("Нет файла {} с "
                         "настройками тестирования").format("tests.txt"))
            self.add_logs_system(
                message=("Для всех циклов будут "
                         "использоваться настроки поумолчанию"))
            return False

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def set_style_sheet(self):
        """
        """
        if os.path.isfile("style.css"):
            with open('style.css', encoding='utf-8') as file:
                css = file.read()
            QtWidgets.qApp.setStyleSheet(css)

    # --------------------------------------------------------------------------- #
    # Инициализация начальных значений
    # --------------------------------------------------------------------------- #
    def gui_initialization(self):
        """
        """
        # menu
        self.menu_action_stop.setDisabled(True)
        self.menu_action_stop_all.setDisabled(True)
        self.l_url_error.setVisible(False)

        # toolbar
        if self.toolbar.isVisible():
            self.menu_action_toolbar_show.setDisabled(True)
            self.menu_action_toolbar_hide.setDisabled(False)
        else:
            self.menu_action_toolbar_show.setDisabled(True)
            self.menu_action_toolbar_hide.setDisabled(False)

        self.t_start = datetime.datetime.now()

        self.process_started = False
        self.show_confirm_if_many_request_errors = True

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
            self.sb_theaders.value() * self.sb_requests_per_theader.value()
        )
        self.pb_requests_success.setValue(0)
        #
        self.pb_finished_theaders.setMaximum(self.sb_theaders.value())
        self.pb_finished_theaders.setValue(0)
        #

        self.l_kpi_theaders.setText(str(self.sb_theaders.value()))
        self.l_kpi_theaders_finished.setText(str(0))
        self.l_kpi_requests.setText(
            str(self.sb_theaders.value() * self.sb_requests_per_theader.value())
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
        self.timer_update_kpi.start(1000)
        self.timer_update_graf.start(self.sb_graf_timeout.value() * 1000)

        self.process_started = True

        self.w_main_settings.setDisabled(True)

        self.tb_btn_start_process.setDisabled(True)
        self.tb_btn_stop_process.setDisabled(False)
        self.tb_btn_close_app.setDisabled(True)

        # menu
        self.menu_action_start.setDisabled(True)
        self.menu_action_stop.setDisabled(False)
        self.menu_action_close.setDisabled(True)

        if self.sb_cycles_count.value() > 1:
            self.tb_btn_stop_all_process_action.setDisabled(False)
            self.menu_action_stop_all.setDisabled(False)
        else:
            self.tabWidget.setCurrentIndex(2)
            self.logs_system.clear()

        self.add_logs_system(
            message=("Запущен процесс "
                     "обработки сайта {}").format(
                         self.get_domain_name(self.cb_urls.currentText())),
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

        # menu
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

        self.timer_update_kpi.stop()
        self.timer_update_graf.stop()

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
            "Статус",
            "Дата",
            "Поток",
            "Цикл",
            "Запрос",
            "App CPU",
            "Theader CPU",
            "Загружено",
            "Http Status Code",
            "Url",
            "Метод",
            "Timeout",
            "Сообщение"])
        #
        # filter model
        self.table_log_requests_filter_model = QtCore.QSortFilterProxyModel()
        self.table_log_requests_filter_model.setSourceModel(
            self.table_log_requests_model)

        self.table_log_requests_filter_model.setFilterKeyColumn(5)

        if self.cb_request_result_type.currentIndex() == 1:
            self.table_log_requests_filter_model.setFilterFixedString("ОК")
        elif self.cb_request_result_type.currentIndex() == 2:
            self.table_log_requests_filter_model.setFilterFixedString("Ошибка")
        else:
            self.table_log_requests_filter_model.setFilterFixedString("")
        #
        self.tv_table_log_requests.setModel(
            self.table_log_requests_filter_model)
        self.tv_table_log_requests.resizeColumnsToContents()
        self.tv_table_log_requests.scrollToBottom()

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
            "Размер очереди",
            "Выполнено запросов",
            "Время работы",
            "Метод запроса",
            "Скачано данных",
            "Активных потоков",
            "Запросов в 1 сек"])
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
        task_bar_height = (desctop.screenGeometry().height()
                           - desctop.availableGeometry().height())
        x = (desctop.width() - self.frameSize().width()) // 2
        y = (desctop.height() - self.frameSize().height()) // 2 + task_bar_height
        self.move(x, y)

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def closeEvent(self, e):
        """
        """
        # FIXME Дописать процедуры завершения потоков
        if gui_confirm.window_confirm(
            bg_color="info").confirm_data(
                text="Закрыть программу?"):
            self.timer_cpu_collect_data.stop()
            self.timer_cpu_calculate_value.stop()
            e.accept()
        else:
            e.ignore()

    # --------------------------------------------------------------------------- #
    # Для блинных url показываем только домен
    # --------------------------------------------------------------------------- #
    def get_domain_name(self, url):
        """
        """
        parsed_uri = urlparse(url)
        result = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
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
            self.cpu_current_value = round(
                sum(self.cpu_current_values) / len(self.cpu_current_values), 2)
            if len(self.cpu_current_values) > 2:
                if cpu_past_value > self.cpu_current_value:
                    self.cpu_current_trend = "&darr;"
                elif cpu_past_value == self.cpu_current_value:
                    self.cpu_current_trend = "&rarr;"
                else:
                    self.cpu_current_trend = "&uarr;"

        self.cpu_current_values = list()
        self.l_kpi_cpu.setText("{} {}".format(
            self.cpu_current_value, self.cpu_current_trend))

        if self.cpu_current_value < self.sb_cpu_max.value():
            self.l_kpi_cpu.setProperty("class", "l_kpi_cpu_normal")
            self.l_kpi_cpu.setStyleSheet(QtWidgets.qApp.styleSheet())
            if self.process_started:
                self.add_logs_system(
                    message="Идет обработка",
                    status_bar=True,
                    logs_system=False)
            else:
                self.add_logs_system(
                    message="Программа готова к запуску",
                    status_bar=True,
                    logs_system=False)
        else:
            self.l_kpi_cpu.setProperty("class", "l_kpi_cpu_hight")
            self.l_kpi_cpu.setStyleSheet(QtWidgets.qApp.styleSheet())
            if self.process_started:
                self.add_logs_system(
                    message=("Система загружена на {}% (Limit {}%). "
                             "Запуск потоков и заданий приостановлен").format(
                        self.cpu_current_value,
                        self.sb_cpu_max.value()),
                    status_bar=True)
            else:
                self.add_logs_system(
                    message="Система загружена на {}% (Limit {}%)".format(
                        self.cpu_current_value, self.sb_cpu_max.value()),
                    status_bar=True)

    # --------------------------------------------------------------------------- #
    # Запускается по таймеру в минимальном промежутке времени
    # --------------------------------------------------------------------------- #
    def on_timer_cpu_collect_data(self):
        """
        """
        self.cpu_current_values.append(psutil.cpu_percent())

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def on_timer_update_kpi(self):
        """
        """
        self.gui_update_kpi()
        self.check_requests_errors()

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def on_timer_update_graf(self):
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
        if gui_confirm.window_confirm(bg_color="info").confirm_data():
            self.gui_initialization_stat_table()

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_event_clear_log_requests_data(self):
        """
        """
        if gui_confirm.window_confirm(bg_color="info").confirm_data():
            self.gui_initialization_log_table()

    # --------------------------------------------------------------------------- #
    # Сохрание лога запросов в файл
    # Ненравиться мне данный способ. Почму нельзя сразу сохранить свю модел без перебора ?
    # TODO Почитать как сохранять модель в файл
    # --------------------------------------------------------------------------- #
    def gui_event_save_file_log_requests_data(self):
        """
        """
        path = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Save File', '', 'CSV(*.csv)')[0]
        if path:
            model = self.table_log_requests_model
            headers = [model.headerData(i, QtCore.Qt.Horizontal)
                       for i in range(model.columnCount())]

            with open(path, 'w', encoding='utf-8') as csv_file:
                writer = csv.writer(
                    csv_file,
                    delimiter=";",
                    quotechar='|',
                    quoting=csv.QUOTE_MINIMAL)
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
        win = gui_stat.window_stat(
            parent=self,
            table_stat_model=self.table_stat_model)
        win.show()

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_event_show_requests_logs_in_new_window(self):
        """
        """
        win = gui_logs.window_logs(
            parent=self,
            table_model=self.table_log_requests_model)
        win.show()

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_event_requests_settings(self):
        """
        """
        win = gui_request_settings.window_request_settings(
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
        gui_author.menu_author(
            parent=self, app_settings=self.app_settings).show()
        # win = gui_author.menu_author(parent=self, app_settings=self.app_settings)
        # win.show()

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
        gui_about.menu_about(self).show()
        # win = gui_about.menu_about(self).show()
        # win.show()

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def menu_toolbar_show(self):
        """
        """
        self.menu_action_toolbar_show.setDisabled(True)
        self.menu_action_toolbar_hide.setDisabled(False)
        self.toolbar.show()

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def menu_toolbar_hide(self):
        """
        """
        self.menu_action_toolbar_show.setDisabled(False)
        self.menu_action_toolbar_hide.setDisabled(True)
        self.toolbar.hide()

    # --------------------------------------------------------------------------- #
    # Запущенные потоки / Активные потоки / Запросы в 1 сек.
    # --------------------------------------------------------------------------- #
    def graphic_main(self):
        """
        """
        self.grafs.graphic_main()

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def graphic_memory(self):
        """
        """
        self.grafs.graphic_memory()

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def graphic_cpu(self):
        """
        """
        self.grafs.graphic_cpu()

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def graphic_speed(self):
        """
        """
        self.grafs.graphic_speed()

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def graphic_requests(self):
        """
        """
        self.grafs.graphic_requests()

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
        self.table_log_requests_filter_model.setFilterKeyColumn(0)
        if self.cb_request_result_type.currentIndex() == 1:
            self.table_log_requests_filter_model.setFilterFixedString("ОК")
        elif self.cb_request_result_type.currentIndex() == 2:
            self.table_log_requests_filter_model.setFilterFixedString("Ошибка")
        else:
            self.table_log_requests_filter_model.setFilterFixedString("")

        self.tv_table_log_requests.setModel(
            self.table_log_requests_filter_model)
        self.tv_table_log_requests.scrollToBottom()
        self.tv_table_log_requests.resizeColumnsToContents()

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_event_change_request_method(self):
        """
        """
        if (self.cb_request_method.currentText() == "get"
                or self.cb_request_method.currentText() == "post"):
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
            str((self.sb_theaders.value() *
                 self.sb_requests_per_theader.value()))
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
            self.l_cycles_count.setText(
                "{} / {}".format(self.sb_cycles_count.value(), 0))
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
            str((self.sb_theaders.value() *
                 self.sb_requests_per_theader.value()))
        )

    # --------------------------------------------------------------------------- #
    # Generate User-Agent
    # --------------------------------------------------------------------------- #
    def gen_new_user_agent(self):
        """
        Generate User-Agent
        """
        return generate_user_agent(os=('win', 'mac', 'linux'), device_type=('desktop',))

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def on_theader_log_message(self, params):
        """
        """
        info_msg = QtGui.QStandardItem()
        if params["status_code"] and int(params["status_code"]) in [200, 301, 302]:
            info_msg.setText("ОК")
            info_msg.setBackground(QtGui.QColor(85, 255, 127))
        else:
            info_msg.setText("Ошибка")
            info_msg.setBackground(QtGui.QColor(255, 85, 127))

        self.table_log_requests_model.appendRow([
            info_msg,
            QtGui.QStandardItem(str(self.cur_date_time())),
            QtGui.QStandardItem(str(params["theader_id"])),
            QtGui.QStandardItem(str(params["cycle_count"] + 1)),
            QtGui.QStandardItem(str(params["count_of_iteration"])),
            QtGui.QStandardItem(str(self.cpu_current_value)),
            QtGui.QStandardItem(str(params["cpu_theader"])),
            QtGui.QStandardItem(str(params["download_size"])),
            QtGui.QStandardItem(str(params["status_code"])),
            #info_msg,  # QtGui.QStandardItem(str(message_type)),
            QtGui.QStandardItem(str(params["url"])),
            QtGui.QStandardItem(str(params["request_method"])),
            QtGui.QStandardItem(str(params["request_timeout"])),
            QtGui.QStandardItem(str(params["message"])),
        ])
        self.tv_table_log_requests.scrollToBottom()

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
        self.pg_theaders_widget_layout_parent = QtWidgets.QVBoxLayout(
            self.pg_theaders_widget_parent)

        self.pg_theaders_widget = QtWidgets.QWidget()
        self.pg_theaders_widget_layout = QtWidgets.QVBoxLayout(
            self.pg_theaders_widget)
        self.pg_theaders_widget_layout_parent.addWidget(
            self.pg_theaders_widget)
        spacer_theaders = QtWidgets.QSpacerItem(
            20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.pg_theaders_widget_layout_parent.addItem(spacer_theaders)
        self.sa_prorgess_bars.setWidget(self.pg_theaders_widget_parent)
        QtWidgets.qApp.processEvents()

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def check_requests_errors(self):
        """
        """
        if (int(self.l_kpi_requests_connection_error.text()) >=
                self.sb_requests_max_errors.value()):
            self.add_logs_system(
                message="Превышено максимальное кол-во ошибочных завпросов")

            if self.show_confirm_if_many_request_errors:
                self.confirm_if_many_requests_errors()

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def confirm_if_many_requests_errors(self):
        """
        """
        self.show_confirm_if_many_request_errors = False
        if gui_confirm.window_confirm(bg_color="danger").confirm_data(
                text="Большое кол-во запросов с ошибками. Остановить программу?"):
            self.gui_event_stop_theaders()

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def check_url_http_status_code(self, url):
        """
        """
        headers = {
            'User-Agent': self.gen_new_user_agent(),
        }
        try:
            response = requests.head(
                url=url,
                headers=headers,
                timeout=self.sb_request_timeout.value())
            if response.status_code in [200, 301, 302]:
                return True
            else:
                return False
        except Exception as err:
            return False

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

        popup = gui_popup.window_popup(
            popup_title="Проверка настроек",
            popup_type="info",
            popup_text="Проверяю настроки программы. Ожидайте...",
            parent=self)
        popup.show()
        QtWidgets.qApp.processEvents()

        if not self.cb_urls.currentText():
            self.l_url_error.setVisible(True)
            self.l_url_error.setProperty("class", "l_url_error")
            self.l_url_error.setStyleSheet(QtWidgets.qApp.styleSheet())
            self.l_url_error.setText("Укажите URL сайта")
            self.add_logs_system(message="Укажите URL сайта", status_bar=True)
            self.tb_btn_start_process.setDisabled(False)
            self.tb_btn_close_app.setDisabled(False)
            self.tabWidget.setCurrentIndex(0)
            popup.hide()
            return False

        if (self.cb_urls.currentText()
                and not self.check_url_http_status_code(
                    url=self.cb_urls.currentText())):
            self.l_url_error.setVisible(True)
            self.l_url_error.setProperty("class", "l_url_error")
            self.l_url_error.setStyleSheet(QtWidgets.qApp.styleSheet())
            self.l_url_error.setText("Сайт недоступен")

            self.add_logs_system(
                message="Сайт {} недоступен".format(
                    self.cb_urls.currentText()),
                status_bar=True)
            self.tb_btn_start_process.setDisabled(False)
            self.tb_btn_close_app.setDisabled(False)

            self.tb_btn_start_process.setText("Запустить")
            self.tabWidget.setCurrentIndex(0)
            popup.hide()
            return False
        else:
            self.add_logs_system(
                message="Проверка успешно пройдена", status_bar=True)
            self.tabWidget.setCurrentIndex(2)
            self.tb_btn_start_process.setDisabled(False)

        popup.hide()
        return True

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def add_requests_stat(self):
        """
        """
        self.tv_table_log_requests.setModel(
            self.table_log_requests_filter_model)
        self.tv_table_log_requests.scrollToBottom()
        self.tv_table_log_requests.resizeColumnsToContents()

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def add_statistics(self):
        """
        """
        average_requests_per_sec = round(
            (sum(self.graphic_active_requests_data)
             / len(self.graphic_active_requests_data)))
        average_active_theaders = round(
            (sum(self.graphic_active_theaders_data)
             / len(self.graphic_active_theaders_data)))

        self.table_stat_model.appendColumn([
            QtGui.QStandardItem(str(self.cb_urls.currentText())),
            QtGui.QStandardItem(str(self.sb_theaders.value())),
            QtGui.QStandardItem(str(self.sb_requests_per_theader.value())),
            QtGui.QStandardItem(
                str(self.sb_requests_per_theader.value() * self.sb_theaders.value())),
            QtGui.QStandardItem(str(self.sb_cpu_max.value())),
            QtGui.QStandardItem(str(self.sb_queue_size.value())),
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
    def count_stared_theaders(self):
        """
        """
        count = 0
        for theader_id in self.theaders_objs:
            if (self.theaders_objs[theader_id]["theader_status"] == "running" or
                    self.theaders_objs[theader_id]["theader_status"] == "pause"):
                count += 1

        return count

    # --------------------------------------------------------------------------- #
    # Динамически добавляем progres bar для нового theader и увеличиваем value при
    # каждом срабатывании события on_theader_iteration
    #
    # Не нравится мне фигня с удалением progres bar для завершенного потока pg.setVisible(False)
    # TODO Найти как правильно удалить widget с формы
    #
    # При генерации сигнала on_theader_iteration поток в обратную сторону получает значение
    # текущего CPU. Данный метод вроде как быстре чем пробегать по массиву потоков и устанавливать
    # и устанавливать значение текущего CPU
    # TODO Сделать еще раз тесты
    # --------------------------------------------------------------------------- #
    def on_theader_iteration(self, theader_id, iteration, cpu_value, theader_status):
        """
        """
        # Если PG существует
        pg = self.findChild(QtWidgets.QProgressBar, "pg_{}".format(theader_id))
        if pg:
            if theader_status == "stoped":
                self.theaders_objs["theader_" +
                                   str(theader_id)]["theader_status"] = "stoped"
                pg.setProperty("class", "tpb_stoped")
            if theader_status == "pause":
                self.theaders_objs["theader_" +
                                   str(theader_id)]["theader_status"] = "pause"
                pg.setProperty("class", "tpb_pause")
            if theader_status == "running":
                self.theaders_objs["theader_" +
                                   str(theader_id)]["theader_status"] = "running"
                pg.setProperty("class", "tpb_running")
                pg.setValue(iteration)
            pg.setFormat(' Поток #{}. Выполнено %v из %m ({} (CPU {}% / {}%))'.format(
                theader_id,
                theader_status,
                cpu_value,
                self.cpu_current_value
            ))
            if pg.value() >= self.sb_requests_per_theader.value():
                pg.setVisible(False)
            self.theaders_objs["theader_"+str(
                theader_id)]["theader_data"].cpu_current_value = self.cpu_current_value
        # Если PG не существует
        else:
            pg = QtWidgets.QProgressBar(
                self.pg_theaders_widget_parent,
                minimum=0,
                maximum=self.sb_requests_per_theader.value()
            )
            pg.setValue(1)
            pg.setObjectName("pg_{}".format(theader_id))
            pg.setFormat(' Поток #{}. Выполнено %v из %m (running (CPU {}% / {}%))'.format(
                theader_id,
                cpu_value,
                round(self.cpu_current_value)
            ))
            pg.setProperty("class", "tpb_running")
            self.pg_theaders_widget_layout.addWidget(pg)
        #
        pg.setStyleSheet(QtWidgets.qApp.styleSheet())

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
        self.mutex.unlock()

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_event_stop_all_theaders(self):
        """
        """
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

        for theader in self.theaders_objs:
            QtWidgets.qApp.processEvents()
            self.theaders_objs[theader]["theader_data"].stop_theader()

    # --------------------------------------------------------------------------- #
    # Событие потока - Поток запустился
    # TODO Переписать на использвание dict theaders_objs вместо переменных
    # --------------------------------------------------------------------------- #
    def on_theader_started(self, theader_id):
        """
        """
        self.theaders_objs["theader_" +
                           str(theader_id)]["theader_status"] = "running"

    # --------------------------------------------------------------------------- #
    # Событие потока - Поток окончил свою работу
    # TODO Переписать на использвание dict theaders_objs вместо переменных
    # --------------------------------------------------------------------------- #
    def on_theader_finished(self, theader_id):
        """
        """
        self.theaders_objs["theader_" +
                           str(theader_id)]["theader_status"] = "finished"

        if self.stop_theaders:
            self.add_logs_system(
                message="Останавливаю потоки...{}".format(
                    self.count_theaders_by_status(status="finished")),
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
        self.l_kpi_prg_running_time.setText(
            str(datetime.timedelta(seconds=self.get_process_time_in_seconds()))[:7])

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_kpi_estimated_time_update(self):
        """
        """
        if int(self.l_kpi_requests_per_seccond.text()):
            estimated_time_to_end_seconds = (
                (self.sb_theaders.value() *
                 self.sb_requests_per_theader.value()) /
                int(self.l_kpi_requests_per_seccond.text()))
            self.l_kpi_prg_running_time_forecast.setText(
                str(datetime.timedelta(seconds=estimated_time_to_end_seconds))[:7])
        else:
            self.l_kpi_prg_running_time_forecast.setText("???")

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_kpi_requests_per_second_update(self):
        """
        """
        requests_per_seconds = round(
            self.count_requests_success / self.get_process_time_in_seconds())
        self.l_kpi_requests_per_seccond.setText(str(requests_per_seconds))

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_kpi_finished_theaders_update(self):
        """
        """
        self.l_kpi_theaders_finished.setText(
            str(self.count_theaders_by_status(status="finished")))

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
        if self.graphic_active_theaders_data:
            self.l_kpi_theaders_active_avg.setText(str(round(
                (sum(self.graphic_active_theaders_data)
                 / len(self.graphic_active_theaders_data)))))
        else:
            self.l_kpi_theaders_active_avg.setText(str(0))

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_kpi_started_theaders_avg_update(self):
        """
        """
        if self.graphic_started_theaders_data:
            self.l_kpi_theaders_started_avg.setText(str(round(
                (sum(self.graphic_started_theaders_data)
                 / len(self.graphic_started_theaders_data)))))
        else:
            self.l_kpi_theaders_started_avg.setText(str(0))

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
        self.l_kpi_theaders_paused.setText(
            str(self.count_theaders_by_status(status="pause")))

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_kpi_download_size_update(self):
        """
        """
        if (self.cb_request_method.currentText() == "get"
                or self.cb_request_method.currentText() == "post"):
            self.l_kpi_download_size.setText(
                str("{}".format(round(self.download_size / 1048576))))
        if self.cb_request_method.currentText() == "head":
            self.l_kpi_download_size.setText(
                str("{}".format(round(self.download_size / 1024))))

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_kpi_requests_success_update(self):
        """
        """
        self.pb_requests_success.setValue(self.count_requests_success)
        self.l_kpi_requests_success.setText(str(self.count_requests_success))

        requests_success_persent = round(
            self.count_requests_success * 100 /
            (self.sb_theaders.value() *
             self.sb_requests_per_theader.value()), 2)
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
        requests_errors = (
            self.count_requests_4xx
            + self.count_requests_5xx
            + self.count_requests_connection_error)
        requests_errors_persent = round(
            requests_errors * 100
            / (self.sb_theaders.value()
               * self.sb_requests_per_theader.value()), 2)
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
        self.l_kpi_requests_connection_error.setText(
            str(self.count_requests_connection_error))

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def gui_kpi_calculate_speed_update(self):
        """
        """
        if (self.cb_request_method.currentText() == "get"
                or self.cb_request_method.currentText() == "post"):
            self.groupBox_26.setTitle("Скорость (Mb/s)")
            self.l_kpi_speed.setText("{}".format(
                round((self.download_size
                       / self.get_process_time_in_seconds())
                      / 1048576, 2)))
        if self.cb_request_method.currentText() == "head":
            self.groupBox_26.setTitle("Скорость (Kb/s)")
            self.l_kpi_speed.setText("{}".format(
                round((self.download_size
                       / self.get_process_time_in_seconds())
                      / 1, 2)))

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
        self.pb_finished_theaders.setValue(
            self.count_theaders_by_status(status="finished"))

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
        except Exception as err:
            self.add_logs_system(
                "Нет тестовых данных для текущего процесса {}".format(cycle_count + 1))
            self.add_logs_system(
                "Для текущего процесса будут использоваться данные по умолчанию")
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
            self.l_cycles_count.setText(
                "{} / {}".format(self.sb_cycles_count.value(), cycle_count + 1))
            if self.app_tests:
                self.sb_cpu_max.setValue(self.get_tests_value(
                    cycle_count, "cpu_limit", self.sb_cpu_max.value()))
                self.sb_theaders.setValue(self.get_tests_value(
                    cycle_count, "theaders", self.sb_theaders.value()))
                self.sb_requests_per_theader.setValue(self.get_tests_value(
                    cycle_count, "requests", self.sb_requests_per_theader.value()))
                self.sb_queue_size.setValue(self.get_tests_value(
                    cycle_count, "queue_size", self.sb_queue_size.value()))

    # --------------------------------------------------------------------------- #
    # Запуск потоков
    # --------------------------------------------------------------------------- #
    def gui_event_start_program(self):
        """
        """
        if self.check_url():
            for cycle_count in range(0, self.sb_cycles_count.value()):
                self.check_tests_settings(cycle_count)

                self.gui_initialization_theaders_progress_bars_canvas()
                self.gui_initialization()
                self.gui_start_process()

                theader_id = 1

                while theader_id <= self.sb_theaders.value():
                    QtWidgets.qApp.processEvents()
                    # Stop
                    if self.stop_theaders:
                        break
                    # Max theaders
                    if self.sb_queue_size.value():
                        if (self.count_stared_theaders() >=
                                self.sb_queue_size.value()):
                            continue
                    # CPU limit
                    if self.cpu_current_value > self.sb_cpu_max.value():
                        time.sleep(0.1)
                        continue
                    try:
                        theader = thread.single_requsts_theader(
                            parent=self,
                            theader_id=theader_id,
                            url=self.cb_urls.currentText(),
                            count_of_requests=self.sb_requests_per_theader.value(),
                            request_timeout=self.sb_request_timeout.value(),
                            request_method=self.cb_request_method.currentText(),
                            cycle_count=cycle_count,
                            cpu_max_value=self.sb_cpu_max.value(),
                            cpu_current_value=self.cpu_current_value)
                        # Можно поставить QtCore.Qt.QueuedConnection но это если я правильно понял частный случай
                        # TODO Почитать по QtCore.Qt.QueuedConnection
                        theader.on_request.connect(self.on_theader_request)
                        theader.on_log_message.connect(
                            self.on_theader_log_message)
                        theader.on_iteration.connect(self.on_theader_iteration)
                        theader.on_theader_finished.connect(
                            self.on_theader_finished)
                        theader.on_theader_started.connect(
                            self.on_theader_started)
                        theader.start()

                        self.theaders_objs["theader_"+str(theader_id)] = {
                            "theader_name": "theader_"+str(theader_id),
                            "theader_status": "running",
                            "theader_data": theader,
                        }

                    except Exception as err:
                        self.add_logs_system(
                            message="Немогу создать поток... {}".format(err))
                    finally:
                        theader_id += 1
                        # if self.sb_graf_timeout.value():
                        #     time.sleep(0.1)

                while True:
                    if self.count_theaders_by_status(status="finished") == len(self.theaders_objs):
                        break
                    QtWidgets.qApp.processEvents()

                self.add_statistics()
                self.add_requests_stat()
                self.gui_end_process()
                self.gui_update_kpi()

                if self.stop_all_process:
                    break
            #
            popup = gui_popup.window_popup(
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
