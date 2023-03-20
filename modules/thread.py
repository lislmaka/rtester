import requests
import time
from user_agent import generate_user_agent
from PyQt5 import QtCore


# ------------------------------------------------------------------------------- #
# Class single_requsts_theader
# ------------------------------------------------------------------------------- #
class single_requsts_theader(QtCore.QThread):
    # --------------------------------------------------------------------------- #
    #  Определяем свои сигналы
    # TODO Посмотреть как указать произвольное кол-ва параметров любого типа
    # --------------------------------------------------------------------------- #
    on_request = QtCore.pyqtSignal(str, int, int)
    on_iteration = QtCore.pyqtSignal(int, int, float, str)
    # on_log_message = QtCore.pyqtSignal(
    #     int, int, int, str, str, str, int, str, str)
    on_log_message = QtCore.pyqtSignal(dict)
    on_theader_finished = QtCore.pyqtSignal(int)
    on_theader_started = QtCore.pyqtSignal(int)

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
        super().__init__(parent=parent)
        self.count_of_requests = count_of_requests
        self.url = url
        self.is_theader_stop = False
        self.theader_id = theader_id
        self.request_method = request_method
        self.request_timeout = request_timeout
        self.cycle_count = cycle_count
        self.cpu_max_value = cpu_max_value
        self.cpu_current_value = cpu_current_value
        self.finished.connect(self.on_finished)

        self.param = {
            # "theader_id": "",
            # "count_of_iteration": "",
            # "cycle_count": "",
            # "status_code": "",
            # "url": "",
            # "cpu_theader": "",
            # "request_method": "",
            # "request_timeout": "",
            # "message": "",
        }

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
        self.on_theader_finished.emit(self.theader_id)

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def run(self):
        """
        """
        self.on_theader_started.emit(self.theader_id)

        count_of_iteration = 1
        while count_of_iteration <= self.count_of_requests:
            #self.cpu_current_value = psutil.cpu_percent(0.1)
            #self.cpu_current_value = self.cpu_sys_value
            if self.is_theader_stop:
                self.on_iteration.emit(
                    self.theader_id,
                    count_of_iteration,
                    self.cpu_current_value,
                    "stoped")
                break
            if self.cpu_current_value > self.cpu_max_value:
                self.on_iteration.emit(
                    self.theader_id,
                    count_of_iteration,
                    self.cpu_current_value,
                    "pause")
                # TODO Магия... Надо почитать более подробнее
                # задачи стартуют так быстро что если не делать задержку то не поток успевает получить флаг отстановки
                # при большом кол-ве потоков
                # Надо ждать иначе уйдет в бесконечный цикл
                time.sleep(0.1)
                continue

            count_of_iteration += 1

            headers = {
                'User-Agent': self.gen_new_user_agent(),
            }
            try:
                if self.request_method == "get":
                    response = requests.get(
                        url=self.url,
                        headers=headers,
                        timeout=self.request_timeout)
                if self.request_method == "post":
                    response = requests.post(
                        url=self.url,
                        headers=headers,
                        timeout=self.request_timeout)
                if self.request_method == "head":
                    response = requests.head(
                        url=self.url,
                        headers=headers,
                        timeout=self.request_timeout)

                if response.status_code in [200, 301, 302]:
                    if self.request_method == "get":
                        download_size = len(response.content)
                    if self.request_method == "head":
                        download_size = len(response.headers)

                    self.on_request.emit(
                        "request", response.status_code, download_size)
                else:
                    self.on_request.emit("request", response.status_code, 0)

                self.param["status_code"] = response.status_code
                self.param["message"] = "HTTP Status Code {}".format(
                    response.status_code)
            except Exception as err:
                self.on_request.emit("connection", 0, 0)
                self.param["status_code"] = None
                self.param["message"] = str(err)
                self.param["download_size"] = 0
            finally:
                self.param["theader_id"] = self.theader_id
                self.param["count_of_iteration"] = count_of_iteration
                self.param["cycle_count"] = self.cycle_count
                self.param["url"] = self.url
                self.param["request_method"] = self.request_method
                self.param["request_timeout"] = self.request_timeout
                self.param["cpu_theader"] = self.cpu_current_value
                self.param["download_size"] = download_size

                self.on_log_message.emit(self.param)
                self.on_iteration.emit(
                    self.theader_id,
                    count_of_iteration,
                    self.cpu_current_value,
                    "running")
        # self.on_theader_finished.emit(self.theader_id)
