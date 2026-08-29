import math
import os
from pathlib import Path
import sys

import flet as ft


if getattr(sys, "frozen", False):
    os.environ["FLET_VIEW_PATH"] = str(Path(sys._MEIPASS) / "flet_view")


STUDENT_ID = 70187744
MAIN_COLOR = ft.Colors.GREY_800
OPERATION_COLOR = ft.Colors.BLUE_GREY_800
ACCENT_COLOR = ft.Colors.BLUE_GREY_600
ERROR_COLOR = ft.Colors.RED_400


def recursive_sum(number: int, stop_at_ten: bool = False) -> int:
    """Рекурсивно суммирует цифры ID до требуемой длины результата."""
    limit = 10 if stop_at_ten else 9
    if number <= limit:
        return number
    return recursive_sum(sum(int(digit) for digit in str(number)), stop_at_ten)


DISPLAY_ROWS = 2 + recursive_sum(STUDENT_ID, stop_at_ten=True)
MEMORY_COUNT = max(2, recursive_sum(STUDENT_ID % 1000))


class CalculationError(ValueError):
    """Ошибка вычисления, которую можно безопасно показать на дисплее."""


class CalculatorEngine:
    """Вычислительное ядро калькулятора, независимое от интерфейса."""

    def __init__(self, memory_count: int = MEMORY_COUNT):
        self.current = "0"
        self.accumulator: float | None = None
        self.operator: str | None = None
        self.left_text = ""
        self.replace_input = False
        self.history: list[str] = []
        self.memory = [0.0 for _ in range(memory_count)]

    @staticmethod
    def format_number(value: float) -> str:
        if not math.isfinite(value):
            raise CalculationError("результат не является конечным числом")
        if abs(value) < 1e-14:
            value = 0.0
        if value.is_integer():
            return str(int(value))
        return f"{value:.12g}"

    def value(self) -> float:
        if self.current == "Ошибка":
            raise CalculationError("на дисплее ошибка")
        try:
            return float(self.current)
        except ValueError as error:
            raise CalculationError("некорректное число") from error

    def enter_digit(self, digit: str):
        if self.current == "Ошибка" or self.replace_input:
            self.current = digit
            self.replace_input = False
        elif self.current == "0":
            self.current = digit
        elif self.current == "-0":
            self.current = f"-{digit}"
        else:
            self.current += digit

    def enter_decimal_point(self):
        if self.current == "Ошибка" or self.replace_input:
            self.current = "0."
            self.replace_input = False
        elif "." not in self.current and "e" not in self.current.lower():
            self.current += "."

    def toggle_sign(self):
        if self.current == "Ошибка":
            self.current = "0"
            return
        self.current = self.current[1:] if self.current.startswith("-") else f"-{self.current}"

    def clear(self):
        self.current = "0"
        self.accumulator = None
        self.operator = None
        self.left_text = ""
        self.replace_input = False

    def set_operator(self, operator: str):
        if self.operator is not None and not self.replace_input:
            self.equals()
        self.accumulator = self.value()
        self.left_text = self.current
        self.operator = operator
        self.replace_input = True

    def equals(self):
        if self.operator is None or self.accumulator is None:
            return
        right = self.value()
        operator = self.operator
        expression = f"{self.left_text} {operator} {self.current}"
        try:
            if operator == "+":
                result = self.accumulator + right
            elif operator == "-":
                result = self.accumulator - right
            elif operator == "×":
                result = self.accumulator * right
            elif operator == "÷":
                if right == 0:
                    raise CalculationError("деление на ноль")
                result = self.accumulator / right
            elif operator == "xʸ":
                result = self.accumulator**right
                if isinstance(result, complex):
                    raise CalculationError("комплексный результат не поддерживается")
            else:
                raise CalculationError("неизвестная операция")
            self.current = self.format_number(float(result))
            self.history.append(f"{expression} = {self.current}")
        except (ArithmeticError, OverflowError, ValueError, CalculationError):
            self.current = "Ошибка"
            self.history.append(f"{expression} = Ошибка")
        finally:
            self.accumulator = None
            self.operator = None
            self.left_text = ""
            self.replace_input = True

    def unary(self, operation: str):
        source_text = self.current
        try:
            value = self.value()
            if operation == "√":
                if value < 0:
                    raise CalculationError("корень отрицательного числа")
                result = math.sqrt(value)
                expression = f"√({source_text})"
            elif operation == "x³":
                result = value**3
                expression = f"({source_text})³"
            elif operation == "asin":
                result = math.asin(value)
                expression = f"asin({source_text})"
            elif operation == "acos":
                result = math.acos(value)
                expression = f"acos({source_text})"
            else:
                raise CalculationError("неизвестная функция")
            self.current = self.format_number(float(result))
            self.history.append(f"{expression} = {self.current}")
        except (ArithmeticError, OverflowError, ValueError, CalculationError):
            self.current = "Ошибка"
            self.history.append(f"{operation}({source_text}) = Ошибка")
        self.replace_input = True

    def memory_store(self, index: int):
        self.memory[index] = self.value()

    def memory_recall(self, index: int):
        self.current = self.format_number(self.memory[index])
        self.replace_input = True

    def memory_add(self, index: int):
        self.memory[index] += self.value()

    def memory_subtract(self, index: int):
        self.memory[index] -= self.value()

    def memory_clear(self, index: int):
        self.memory[index] = 0.0


class MainWindow(ft.Container):
    """Обычный и инженерный режимы калькулятора из задания № 3."""

    def __init__(self):
        super().__init__(expand=True, padding=10)
        self.engine = CalculatorEngine()
        self.engineering_mode = False
        self.selected_memory = 0

        self.mode_switch = ft.Switch(
            label="Инженерный режим",
            value=False,
            active_color=ACCENT_COLOR,
            on_change=self.change_mode,
        )
        self.display = ft.ListView(
            height=68,
            spacing=3,
            padding=10,
            auto_scroll=True,
        )
        self.display_box = ft.Container(
            bgcolor=MAIN_COLOR,
            border_radius=8,
            content=self.display,
        )

        self.selected_memory_text = ft.Text("Выбрана M1", weight=ft.FontWeight.BOLD)
        self.memory_value_texts = [
            ft.Text("0", selectable=True, expand=True) for _ in range(MEMORY_COUNT)
        ]
        memory_rows = []
        for index in range(MEMORY_COUNT):
            memory_rows.append(
                ft.Row(
                    controls=[
                        ft.Button(
                            content=f"M{index + 1}",
                            on_click=lambda _event, i=index: self.select_memory(i),
                        ),
                        self.memory_value_texts[index],
                    ]
                )
            )

        self.memory_panel = ft.Container(
            visible=False,
            width=290,
            padding=10,
            border=ft.Border.all(1, ACCENT_COLOR),
            border_radius=8,
            content=ft.Column(
                controls=[
                    ft.Text(
                        f"Память: {MEMORY_COUNT} ячеек",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text("Нажмите M1–M6, чтобы выбрать ячейку."),
                    ft.ListView(controls=memory_rows, spacing=5, expand=True),
                ],
                expand=True,
            ),
        )

        memory_controls = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                self.selected_memory_text,
                self.make_button("MC", "MC", compact=True),
                self.make_button("MR", "MR", compact=True),
                self.make_button("M+", "M+", compact=True),
                self.make_button("M−", "M-", compact=True),
                self.make_button("MS", "MS", compact=True),
            ],
        )

        self.engineering_functions = ft.Row(
            visible=False,
            controls=[
                self.make_button("x³", "x³"),
                self.make_button("asin", "asin"),
                self.make_button("acos", "acos"),
            ],
        )

        keyboard = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        self.make_button("AC", "AC", operation=True),
                        self.make_button("±", "±", operation=True),
                        self.make_button("√", "√", operation=True),
                        self.make_button("÷", "÷", operation=True),
                    ]
                ),
                ft.Row(
                    controls=[
                        self.make_button("7", "7"),
                        self.make_button("8", "8"),
                        self.make_button("9", "9"),
                        self.make_button("×", "×", operation=True),
                    ]
                ),
                ft.Row(
                    controls=[
                        self.make_button("4", "4"),
                        self.make_button("5", "5"),
                        self.make_button("6", "6"),
                        self.make_button("−", "-", operation=True),
                    ]
                ),
                ft.Row(
                    controls=[
                        self.make_button("1", "1"),
                        self.make_button("2", "2"),
                        self.make_button("3", "3"),
                        self.make_button("+", "+", operation=True),
                    ]
                ),
                ft.Row(
                    controls=[
                        self.make_button("0", "0"),
                        self.make_button(".", "."),
                        self.make_button("xʸ", "xʸ", operation=True),
                        self.make_button("=", "=", operation=True),
                    ]
                ),
                self.engineering_functions,
            ]
        )

        main_panel = ft.Column(
            width=430,
            controls=[
                self.mode_switch,
                ft.Text(
                    f"Дисплей: {DISPLAY_ROWS} строки · Память: {MEMORY_COUNT} ячеек",
                    size=12,
                    color=ft.Colors.GREY_500,
                ),
                self.display_box,
                memory_controls,
                keyboard,
            ],
        )

        self.content = ft.Row(
            controls=[main_panel, self.memory_panel],
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
        self.refresh(update_control=False)

    def make_button(
        self,
        label: str,
        action: str,
        operation: bool = False,
        compact: bool = False,
    ) -> ft.Button:
        return ft.Button(
            content=label,
            on_click=lambda _event, value=action: self.press(value),
            bgcolor=OPERATION_COLOR if operation else None,
            color=ft.Colors.WHITE if operation else None,
            height=42 if compact else 50,
            expand=True,
        )

    def press(self, action: str):
        if action.isdigit():
            self.engine.enter_digit(action)
        elif action == ".":
            self.engine.enter_decimal_point()
        elif action == "±":
            self.engine.toggle_sign()
        elif action == "AC":
            self.engine.clear()
        elif action in {"+", "-", "×", "÷", "xʸ"}:
            try:
                self.engine.set_operator(action)
            except CalculationError:
                self.engine.current = "Ошибка"
        elif action == "=":
            self.engine.equals()
        elif action in {"√", "x³", "asin", "acos"}:
            self.engine.unary(action)
        elif action in {"MC", "MR", "M+", "M-", "MS"}:
            self.memory_command(action)
        self.refresh()

    def memory_command(self, command: str):
        try:
            if command == "MC":
                self.engine.memory_clear(self.selected_memory)
            elif command == "MR":
                self.engine.memory_recall(self.selected_memory)
            elif command == "M+":
                self.engine.memory_add(self.selected_memory)
            elif command == "M-":
                self.engine.memory_subtract(self.selected_memory)
            elif command == "MS":
                self.engine.memory_store(self.selected_memory)
        except CalculationError:
            self.engine.current = "Ошибка"

    def select_memory(self, index: int):
        self.selected_memory = index
        self.refresh()

    def change_mode(self, event):
        self.engineering_mode = bool(event.control.value)
        if not self.engineering_mode:
            self.selected_memory = 0
        self.engineering_functions.visible = self.engineering_mode
        self.memory_panel.visible = self.engineering_mode
        self.display.height = DISPLAY_ROWS * 38 if self.engineering_mode else 68
        if self.page:
            self.page.window.width = 780 if self.engineering_mode else 470
            self.page.window.height = 700 if self.engineering_mode else 620
        self.refresh()

    def refresh(self, update_control: bool = True):
        if self.engineering_mode:
            lines = self.engine.history + [self.engine.current]
        else:
            lines = [self.engine.current]

        self.display.controls = [
            ft.Text(
                line,
                size=28 if index == len(lines) - 1 else 18,
                weight=ft.FontWeight.BOLD if index == len(lines) - 1 else None,
                color=ERROR_COLOR if "Ошибка" in line else ft.Colors.WHITE,
                text_align=ft.TextAlign.RIGHT,
            )
            for index, line in enumerate(lines)
        ]
        self.selected_memory_text.value = f"Выбрана M{self.selected_memory + 1}"
        for index, value in enumerate(self.engine.memory):
            self.memory_value_texts[index].value = self.engine.format_number(value)
        if update_control:
            self.update()


def main(page: ft.Page):
    page.title = "Калькулятор"
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 470
    page.window.height = 620
    page.window.resizable = False
    page.add(MainWindow())


if __name__ == "__main__":
    ft.run(main)
