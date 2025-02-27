import pyqtgraph as pg


# ------------------------------------------------------------------------------- #
#
# ------------------------------------------------------------------------------- #
class grafs:
    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def __init__(self, parent=None):
        self.parent = parent

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def graphic_main(self):
        """ """
        self.parent.graphics_view_main.clear()

        self.parent.graphics_view_main.showGrid(x=True, y=True)
        self.parent.graphics_view_main.setLabel(
            "left", "Потоки / Запросы", units="кол-во"
        )
        self.parent.graphics_view_main.setLabel("bottom", "Время", units="сек.")

        # Sterted Theaders
        self.parent.graphic_started_theaders_data.append(
            self.parent.count_theaders_by_status(status="running")
            + self.parent.count_theaders_by_status(status="pause")
        )

        self.parent.graphics_view_main.plot(
            y=self.parent.graphic_started_theaders_data,
            pen=pg.mkPen((0, 85, 255), width=2),
        )

        # Active Theaders
        self.parent.graphic_active_theaders_data.append(
            self.parent.count_theaders_by_status(status="running")
        )

        self.parent.graphics_view_main.plot(
            y=self.parent.graphic_active_theaders_data,
            pen=pg.mkPen((170, 0, 0), width=2),
        )

        # Requests per second
        self.parent.graphic_active_requests_data.append(
            int(self.parent.l_kpi_requests_per_seccond.text())
        )

        self.parent.graphics_view_main.plot(
            y=self.parent.graphic_active_requests_data,
            pen=pg.mkPen((170, 0, 255), width=2),
        )

        # Average data
        self.parent.label_average_started_theaders.setText(
            "{} / {}".format(
                self.parent.graphic_started_theaders_data[-1],
                round(
                    sum(self.parent.graphic_started_theaders_data)
                    / len(self.parent.graphic_started_theaders_data)
                ),
            )
        )

        self.parent.label_average_active_theaders.setText(
            "{} / {}".format(
                self.parent.graphic_active_theaders_data[-1],
                round(
                    sum(self.parent.graphic_active_theaders_data)
                    / len(self.parent.graphic_active_theaders_data)
                ),
            )
        )

        self.parent.label_average_requests_per_sec.setText(
            "{} / {}".format(
                self.parent.graphic_active_requests_data[-1],
                round(
                    sum(self.parent.graphic_active_requests_data)
                    / len(self.parent.graphic_active_requests_data)
                ),
            )
        )

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def graphic_memory(self):
        """ """
        self.parent.graphic_memory_data.append(float(self.parent.l_kpi_memory.text()))

        self.parent.graphics_view_memory.clear()
        self.parent.graphics_view_memory.plot(
            y=self.parent.graphic_memory_data, pen=pg.mkPen(width=2)
        )

        self.parent.graphics_view_memory.showGrid(x=True, y=True)
        self.parent.graphics_view_memory.setLabel("left", "Нагрузка", units="%")
        self.parent.graphics_view_memory.setLabel("bottom", "Время", units="сек.")

        #
        midle_line = pg.InfiniteLine(
            movable=False,
            angle=0,
            pen=pg.mkPen((0, 204, 102), width=1),
            label="Среднее={value}",
            labelOpts={
                "color": (255, 255, 255),
                "movable": True,
                "fill": (0, 204, 102, 100),
            },
        )

        midle_value = round(
            sum(self.parent.graphic_memory_data) / len(self.parent.graphic_memory_data)
        )
        midle_line.setPos([0, midle_value])
        self.parent.graphics_view_memory.addItem(midle_line)

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def graphic_cpu(self):
        """ """
        self.parent.graphic_cpu_data.append(self.parent.cpu_current_value)

        self.parent.graphics_view_cpu.clear()
        self.parent.graphics_view_cpu.plot(
            y=self.parent.graphic_cpu_data, pen=pg.mkPen(width=2)
        )

        self.parent.graphics_view_cpu.showGrid(x=True, y=True)
        self.parent.graphics_view_cpu.setLabel("left", "Нагрузка", units="%")
        self.parent.graphics_view_cpu.setLabel("bottom", "Время", units="сек.")

        #
        midle_line = pg.InfiniteLine(
            movable=False, angle=0, pen=pg.mkPen((0, 204, 102), width=1)
        )

        midle_value = round(
            sum(self.parent.graphic_cpu_data) / len(self.parent.graphic_cpu_data), 2
        )
        midle_line.setPos([0, midle_value])
        self.parent.graphics_view_cpu.addItem(midle_line)

        #
        midle_line = pg.InfiniteLine(
            movable=False,
            angle=0,
            pen=pg.mkPen((255, 0, 0), width=1),
            label="Предел={value}",
            labelOpts={
                "color": (255, 255, 255),
                "movable": True,
                "fill": (255, 0, 0, 100),
            },
        )

        midle_value = self.parent.sb_cpu_max.value()
        midle_line.setPos([0, midle_value])
        self.parent.graphics_view_cpu.addItem(midle_line)

        #
        cpu_average = round(
            sum(self.parent.graphic_cpu_data) / len(self.parent.graphic_cpu_data), 2
        )
        cpu_average_persent = round(
            cpu_average * 100 / self.parent.sb_cpu_max.value(), 2
        )
        self.parent.label_cpu_current.setText(str(self.parent.cpu_current_value))
        self.parent.label_average_cpu.setText(str(cpu_average))
        self.parent.label_average_cpu_persent.setText(str(cpu_average_persent))

        # cpu_average
        if cpu_average > self.parent.sb_cpu_max.value():
            self.parent.gb_average_cpu.setStyleSheet(
                "background-color: rgb(255, 112, 77); color: rgb(255, 255, 255);"
            )
        else:
            self.parent.gb_average_cpu.setStyleSheet(
                "background-color: rgb(0, 204, 102); color: rgb(255, 255, 255);"
            )
        # cpu_current_value
        if self.parent.cpu_current_value > self.parent.sb_cpu_max.value():
            self.parent.gb_cpu_current.setStyleSheet(
                "background-color: rgb(255, 112, 77); color: rgb(255, 255, 255);"
            )
        else:
            self.parent.gb_cpu_current.setStyleSheet(
                "background-color: rgb(0, 204, 102); color: rgb(255, 255, 255);"
            )
        # cpu_average_persent
        if cpu_average_persent >= 100:
            self.parent.gb_average_cpu_persent.setStyleSheet(
                "background-color: rgb(255, 112, 77); color: rgb(255, 255, 255);"
            )
        else:
            self.parent.gb_average_cpu_persent.setStyleSheet(
                "background-color: rgb(0, 204, 102); color: rgb(255, 255, 255);"
            )

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def graphic_speed(self):
        """ """
        self.parent.graphic_speed_data.append(float(self.parent.l_kpi_speed.text()))

        self.parent.graphics_view_speed.clear()
        self.parent.graphics_view_speed.plot(
            y=self.parent.graphic_speed_data, pen=pg.mkPen(width=2)
        )

        self.parent.graphics_view_speed.showGrid(x=True, y=True)
        self.parent.graphics_view_speed.setLabel("left", "Скорость", units="Mb/Kb/s")
        self.parent.graphics_view_speed.setLabel("bottom", "Время", units="сек.")

        midle_line = pg.InfiniteLine(
            movable=False,
            angle=0,
            pen=pg.mkPen((0, 204, 102), width=1),
            label="Среднее={value}",
            labelOpts={
                "color": (255, 255, 255),
                "movable": True,
                "fill": (0, 204, 102, 100),
            },
        )

        midle_value = round(
            sum(self.parent.graphic_speed_data) / len(self.parent.graphic_speed_data), 2
        )
        midle_line.setPos([0, midle_value])
        self.parent.graphics_view_speed.addItem(midle_line)

    # --------------------------------------------------------------------------- #
    #
    # --------------------------------------------------------------------------- #
    def graphic_requests(self):
        """ """
        persent_requests_success = round(
            (int(self.parent.l_kpi_requests_success.text()) * 100)
            / (
                self.parent.sb_requests_per_theader.value()
                * self.parent.sb_theaders.value()
            ),
            2,
        )
        self.parent.graphic_requests_success_data.append(persent_requests_success)

        persent_requests_4xx = round(
            (int(self.parent.l_kpi_requests_4xx.text()) * 100)
            / (
                self.parent.sb_requests_per_theader.value()
                * self.parent.sb_theaders.value()
            ),
            2,
        )
        self.parent.graphic_requests_4xx_data.append(persent_requests_4xx)

        persent_requests_5xx = round(
            (int(self.parent.l_kpi_requests_5xx.text()) * 100)
            / (
                self.parent.sb_requests_per_theader.value()
                * self.parent.sb_theaders.value()
            ),
            2,
        )
        self.parent.graphic_requests_5xx_data.append(persent_requests_5xx)

        persent_requests_connection_err = round(
            (int(self.parent.l_kpi_requests_connection_error.text()) * 100)
            / (
                self.parent.sb_requests_per_theader.value()
                * self.parent.sb_theaders.value()
            ),
            2,
        )
        self.parent.graphic_requests_connection_err_data.append(
            persent_requests_connection_err
        )

        all_errors = (
            int(self.parent.l_kpi_requests_4xx.text())
            + int(self.parent.l_kpi_requests_5xx.text())
            + int(self.parent.l_kpi_requests_connection_error.text())
        )

        self.parent.graphics_view_requests.clear()
        self.parent.graphics_view_requests.showGrid(x=True, y=True)
        self.parent.graphics_view_requests.setLabel("left", "Запросы", units="%")
        self.parent.graphics_view_requests.setLabel("bottom", "Время", units="сек.")

        self.parent.graphics_view_requests.plot(
            y=self.parent.graphic_requests_success_data,
            pen=pg.mkPen((0, 204, 102), width=2),
        )

        self.parent.graphics_view_requests.plot(
            y=self.parent.graphic_requests_4xx_data,
            pen=pg.mkPen((255, 102, 102), width=2),
        )

        self.parent.graphics_view_requests.plot(
            y=self.parent.graphic_requests_5xx_data,
            pen=pg.mkPen((255, 112, 77), width=2),
        )

        self.parent.graphics_view_requests.plot(
            y=self.parent.graphic_requests_connection_err_data,
            pen=pg.mkPen((255, 51, 0), width=2),
        )

        #
        midle_line = pg.InfiniteLine(
            movable=False,
            angle=0,
            pen=pg.mkPen((0, 204, 102), width=1),
            label="Успешных={value}%",
            labelOpts={
                "color": (255, 255, 255),
                "movable": True,
                "fill": (0, 204, 102, 100),
            },
        )

        midle_value = persent_requests_success
        midle_line.setPos([0, midle_value])
        self.parent.graphics_view_requests.addItem(midle_line)

        #
        midle_line = pg.InfiniteLine(
            movable=False,
            angle=0,
            pen=pg.mkPen((255, 0, 0), width=1),
            label="С ошибками={value}%",
            labelOpts={
                "color": (255, 255, 255),
                "movable": True,
                "fill": (255, 0, 0, 100),
            },
        )

        midle_value = round(
            (all_errors * 100)
            / (
                self.parent.sb_requests_per_theader.value()
                * self.parent.sb_theaders.value()
            ),
            2,
        )
        midle_line.setPos([0, midle_value])
        self.parent.graphics_view_requests.addItem(midle_line)
