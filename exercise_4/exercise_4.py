from PyQt5.QtWidgets import (
    QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsTextItem, QVBoxLayout, QWidget, QFrame, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QApplication
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QPen, QColor
import random
from collections import deque
import sys


class HanoiTowerQt(QMainWindow):
    def __init__(self, student_id):
        super().__init__()
        self.student_id = student_id
        self.spindles = [[] for _ in range(8)]  # 8 шпинделей
        self.colors = {}  # Словарь для хранения цветов дисков
        self.initialize_spindles()  # Инициализация начального состояния
        self.initial_spindles = [list(spindle) for spindle in self.spindles]
        self.moves = []  # Список всех ходов

        # Связи между шпинделями (граф для поиска пути)
        self.connections = {
            0: [1, 2],
            1: [0, 2],
            2: [1, 3],
            3: [2, 4],
            4: [3, 5],
            5: [4, 6],
            6: [5, 7],
            7: [5, 6]
        }

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Ханойские башни")
        self.setGeometry(100, 100, 1280, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Визуализация графики
        self.view = QGraphicsView()
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        layout.addWidget(self.view)

        # Панель управления
        control_panel = QFrame()
        control_layout = QHBoxLayout(control_panel)

        self.btn_start = QPushButton("Начало")
        self.btn_start.clicked.connect(lambda: self.show_iteration(0))
        control_layout.addWidget(self.btn_start)

        self.btn_end = QPushButton("Окончание")
        self.btn_end.clicked.connect(self.generate_and_show_end)
        control_layout.addWidget(self.btn_end)

        self.percent_entries = []
        self.percent_buttons = []
        # Поля ввода процентов и кнопки для промежуточных итераций
        for i in range(4):
            entry = QLineEdit()
            entry.setFixedWidth(50)
            entry.setText(self.student_id[i * 2:i * 2 + 2])
            control_layout.addWidget(entry)
            self.percent_entries.append(entry)

            btn = QPushButton(f"Итерация {i + 1}")
            btn.clicked.connect(lambda checked, idx=i: self.on_percent_click(idx))
            control_layout.addWidget(btn)
            self.percent_buttons.append(btn)

        layout.addWidget(control_panel)

        self.label_iteration = QLabel("Итерация 0")
        layout.addWidget(self.label_iteration)

        self.draw_spindles()

    def initialize_spindles(self):
        # Распределяем диски по шпинделям на основе student_id
        for i in range(8):
            spindle_num = 8 - i
            num_disks = int(self.student_id[i])
            for n in range(num_disks, 0, -1):
                diameter = spindle_num * 10 + n
                self.spindles[i].append(diameter)
                self.colors[diameter] = "#{:06x}".format(random.randint(0, 0xFFFFFF))

    def draw_spindles(self):
        # Отрисовка состояния всех шпинделей
        self.scene.clear()
        spindle_x = 100
        spindle_y_base = 500
        disk_height = 12
        spindle_spacing = 150

        for i in range(8):
            x = spindle_x + i * spindle_spacing
            self.scene.addLine(x, 100, x, spindle_y_base, QPen(Qt.black, 2))

            # Номер шпинделя
            text = QGraphicsTextItem(str(8 - i))
            text.setPos(x - 10, spindle_y_base + 20)
            self.scene.addItem(text)

            # Отрисовка дисков
            disks = self.spindles[i]
            y = spindle_y_base
            for diameter in reversed(disks):
                width = diameter * 2
                y -= disk_height
                rect = QGraphicsRectItem(x - width / 2, y, width, disk_height)
                rect.setBrush(QBrush(QColor(self.colors[diameter])))
                rect.setPen(QPen(Qt.black))
                self.scene.addItem(rect)

                text = QGraphicsTextItem(str(diameter))
                text.setPos(x - 10, y + disk_height / 2 - 10)
                self.scene.addItem(text)

    def can_place_disk(self, peg, disk, state):
        # Проверка: можно ли положить диск на шпиндель
        return not state[peg] or state[peg][-1] > disk

    def find_path(self, start, end):
        # Поиск пути между шпинделями в графе
        queue = deque([(start, [start])])
        visited = set([start])
        while queue:
            current, path = queue.popleft()
            if current == end:
                return path
            for neighbor in self.connections[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        return []

    def generate_moves(self):
        # Генерация всех шагов перемещения
        moves = []
        state = [list(spindle) for spindle in self.initial_spindles]
        target_peg = 7
        all_disks = [disk for spindle in state for disk in spindle]
        all_disks.sort(reverse=True)  # От большего к меньшему
        max_moves = 10000
        move_count = 0

        for disk in all_disks:
            current_peg = next((i for i, spindle in enumerate(state) if disk in spindle), None)
            if current_peg is None or current_peg == target_peg:
                continue

            path = self.find_path(current_peg, target_peg)
            for i in range(len(path) - 1):
                from_peg = path[i]
                to_peg = path[i + 1]

                # Освобождаем диск сверху, если он не на вершине
                while state[from_peg] and state[from_peg][-1] != disk:
                    top_disk = state[from_peg][-1]
                    for temp_peg in self.connections[from_peg]:
                        if temp_peg != to_peg and self.can_place_disk(temp_peg, top_disk, state):
                            state[temp_peg].append(state[from_peg].pop())
                            moves.append((from_peg, temp_peg))
                            move_count += 1
                            break
                    else:
                        for temp_peg in range(8):
                            if temp_peg != from_peg and temp_peg != to_peg and self.can_place_disk(temp_peg, top_disk, state):
                                state[temp_peg].append(state[from_peg].pop())
                                moves.append((from_peg, temp_peg))
                                move_count += 1
                                break
                        else:
                            break

                # Освобождаем место на приемном шпинделе, если нужно
                while state[to_peg] and state[to_peg][-1] < disk:
                    top_disk = state[to_peg][-1]
                    for temp_peg in self.connections[to_peg]:
                        if temp_peg != from_peg and self.can_place_disk(temp_peg, top_disk, state):
                            state[temp_peg].append(state[to_peg].pop())
                            moves.append((to_peg, temp_peg))
                            move_count += 1
                            break
                    else:
                        for temp_peg in range(8):
                            if temp_peg != from_peg and temp_peg != to_peg and self.can_place_disk(temp_peg, top_disk, state):
                                state[temp_peg].append(state[to_peg].pop())
                                moves.append((to_peg, temp_peg))
                                move_count += 1
                                break
                        else:
                            break

                # Перемещаем нужный диск
                if state[from_peg] and state[from_peg][-1] == disk and self.can_place_disk(to_peg, disk, state):
                    state[to_peg].append(state[from_peg].pop())
                    moves.append((from_peg, to_peg))
                    move_count += 1

                if move_count > max_moves:
                    print("Достигнуто максимальное количество ходов. Прерывание.")
                    break

            if move_count > max_moves:
                break

        return moves

    def generate_and_show_end(self):
        # Показать финальное состояние
        if not self.moves:
            self.moves = self.generate_moves()
        self.show_iteration(len(self.moves))

    def show_iteration(self, iteration):
        # Отобразить состояние на заданной итерации
        if not self.moves and iteration > 0:
            self.moves = self.generate_moves()

        if iteration == 0:
            self.spindles = [list(spindle) for spindle in self.initial_spindles]
            self.label_iteration.setText("Итерация 0")
        elif iteration >= len(self.moves):
            # Полное завершение — все диски на последнем шпинделе
            all_disks = [disk for spindle in self.initial_spindles for disk in spindle]
            all_disks.sort(reverse=True)
            self.spindles = [[] for _ in range(8)]
            self.spindles[7] = all_disks
            self.label_iteration.setText(f"Итерация {len(self.moves)}")
        else:
            # Промежуточное состояние
            state = [list(spindle) for spindle in self.initial_spindles]
            int_iter = int(iteration)
            frac = iteration - int_iter

            for i in range(min(int_iter, len(self.moves))):
                from_peg, to_peg = self.moves[i]
                disk = state[from_peg].pop()
                state[to_peg].append(disk)
            self.spindles = state

            # Анимация движения между шпинделями
            if frac > 0 and int_iter < len(self.moves):
                from_peg, to_peg = self.moves[int_iter]
                disk = self.spindles[from_peg].pop()
                self.draw_spindles()

                spindle_x = 100
                spindle_spacing = 150
                x_from = spindle_x + from_peg * spindle_spacing
                x_to = spindle_x + to_peg * spindle_spacing
                y_base = 500 - (len(self.spindles[to_peg]) + 1) * 12

                x = x_from + (x_to - x_from) * frac
                width = disk * 2
                rect = QGraphicsRectItem(x - width / 2, y_base - 12, width, 12)
                rect.setBrush(QBrush(QColor(self.colors[disk])))
                rect.setPen(QPen(Qt.black))
                self.scene.addItem(rect)

                text = QGraphicsTextItem(str(disk))
                text.setPos(x - 10, y_base - 6)
                self.scene.addItem(text)
                self.label_iteration.setText(f"Итерация {iteration:.3f}")
                return

        self.draw_spindles()
        self.label_iteration.setText(f"Итерация {int(iteration)}")

    def on_percent_click(self, idx):
        # Обработка кнопки итерации по проценту
        if not self.moves:
            self.moves = self.generate_moves()
        try:
            percent = int(self.percent_entries[idx].text())
            if 0 <= percent <= 100:
                iteration = len(self.moves) * percent / 100
                self.show_iteration(iteration)
        except ValueError:
            pass


if __name__ == "__main__":
    stud_id = "70187744"
    app = QApplication(sys.argv)
    window = HanoiTowerQt(stud_id)
    window.show()
    sys.exit(app.exec_())
