import os
from pathlib import Path
import sys

import flet as ft


if getattr(sys, "frozen", False):
    os.environ["FLET_VIEW_PATH"] = str(Path(sys._MEIPASS) / "flet_view")


STUDENT_ID = 70187744
INITIAL_CLIENT = "Latypov"
MAIN_COLOR = ft.Colors.GREEN_700
ERROR_COLOR = ft.Colors.RED_700


class CommandError(ValueError):
    """Ошибка синтаксиса или аргументов банковской команды."""


class BankSystem:
    """Хранит счета и выполняет команды из задания № 2."""

    def __init__(self):
        self.clients: dict[str, int] = {INITIAL_CLIENT: STUDENT_ID}

    @staticmethod
    def _check_name(name: str) -> str:
        if not name or not name.isalnum():
            raise CommandError("некорректное имя клиента")
        return name

    @staticmethod
    def _parse_number(value: str, label: str = "сумма") -> int:
        if not value.isdigit():
            raise CommandError(f"{label} должна быть целым неотрицательным числом")
        return int(value)

    @staticmethod
    def _require_count(arguments: list[str], expected: int, command: str):
        if len(arguments) != expected:
            raise CommandError(
                f"команда {command} ожидает {expected} аргумент(а), получено {len(arguments)}"
            )

    def _ensure_client(self, name: str):
        self.clients.setdefault(name, 0)

    def _account(self, name: str) -> str:
        return f"{name} {self.clients[name]}"

    def execute(self, line: str) -> list[str]:
        parts = line.split()
        if not parts:
            raise CommandError("пустая команда")

        command, arguments = parts[0], parts[1:]
        if command != command.upper():
            raise CommandError("название команды должно быть написано заглавными буквами")

        if command == "DEPOSIT":
            self._require_count(arguments, 2, command)
            name = self._check_name(arguments[0])
            amount = self._parse_number(arguments[1])
            self._ensure_client(name)
            self.clients[name] += amount
            return [self._account(name)]

        if command == "WITHDRAW":
            self._require_count(arguments, 2, command)
            name = self._check_name(arguments[0])
            amount = self._parse_number(arguments[1])
            self._ensure_client(name)
            self.clients[name] -= amount
            return [self._account(name)]

        if command == "BALANCE":
            if len(arguments) > 1:
                raise CommandError("команда BALANCE ожидает 0 или 1 аргумент")
            if not arguments:
                return [self._account(name) for name in self.clients]
            name = self._check_name(arguments[0])
            if name not in self.clients:
                return ["NO CLIENT"]
            return [self._account(name)]

        if command == "TRANSFER":
            self._require_count(arguments, 3, command)
            sender = self._check_name(arguments[0])
            receiver = self._check_name(arguments[1])
            amount = self._parse_number(arguments[2])
            self._ensure_client(sender)
            self._ensure_client(receiver)
            self.clients[sender] -= amount
            self.clients[receiver] += amount
            return [self._account(sender), self._account(receiver)]

        if command == "INCOME":
            self._require_count(arguments, 1, command)
            percent = self._parse_number(arguments[0], "процент")
            for name, balance in self.clients.items():
                if balance > 0:
                    self.clients[name] = balance * (100 + percent) // 100
            return [self._account(name) for name in self.clients]

        raise CommandError("нераспознанная команда")

    def execute_batch(self, text: str) -> str:
        """Выполняет команды последовательно и останавливается на первой ошибке."""
        output: list[str] = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            try:
                results = self.execute(line)
            except CommandError:
                output.append(f"ОШИБКА: {line}")
                break
            output.append(line)
            output.extend(f"    {result}" for result in results)
            output.append(">>>")
        return "\n".join(output)


class MainWindow(ft.Container):
    """Графический интерфейс банковской экспертной системы."""

    def __init__(self):
        super().__init__(expand=True, padding=12)
        self.bank = BankSystem()

        self.command_input = ft.TextField(
            label="Команды",
            hint_text="По одной команде на строке. Enter — расчёт, Shift+Enter — новая строка.",
            multiline=True,
            min_lines=8,
            max_lines=14,
            shift_enter=True,
            on_submit=self.calculate,
            autofocus=True,
            expand=True,
        )
        self.result_output = ft.TextField(
            label="Результаты",
            multiline=True,
            min_lines=10,
            max_lines=16,
            read_only=True,
            value="",
            text_style=ft.TextStyle(font_family="Consolas", size=15),
            expand=True,
        )
        self.file_input = ft.TextField(
            label="Имя или путь к файлу",
            hint_text="commands.txt",
            multiline=False,
            on_submit=self.load_file,
            expand=True,
        )
        self.status = ft.Text(color=ERROR_COLOR)

        self.content = ft.Column(
            expand=True,
            controls=[
                ft.Container(
                    bgcolor=MAIN_COLOR,
                    border_radius=8,
                    padding=12,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.ACCOUNT_BALANCE, color=ft.Colors.WHITE),
                                    ft.Text("Bank System", size=22, color=ft.Colors.WHITE),
                                ]
                            ),
                            ft.Button(
                                content="Очистить вывод",
                                icon=ft.Icons.CLEAR,
                                on_click=self.clear_output,
                            ),
                        ],
                    ),
                ),
                ft.Text("Поле ввода команд", weight=ft.FontWeight.BOLD),
                self.command_input,
                ft.Row(
                    controls=[
                        ft.Button(
                            content="Расчёт",
                            icon=ft.Icons.PLAY_ARROW,
                            on_click=self.calculate,
                            bgcolor=MAIN_COLOR,
                            color=ft.Colors.WHITE,
                        ),
                        ft.Button(
                            content="Очистить ввод",
                            icon=ft.Icons.BACKSPACE,
                            on_click=self.clear_input,
                        ),
                    ]
                ),
                ft.Text("Поле вывода результатов", weight=ft.FontWeight.BOLD),
                self.result_output,
                ft.Row(
                    controls=[
                        self.file_input,
                        ft.Button(
                            content="Загрузить",
                            icon=ft.Icons.FILE_UPLOAD,
                            on_click=self.load_file,
                        ),
                    ]
                ),
                self.status,
            ],
        )

    def calculate(self, _event=None):
        self.status.value = ""
        text = self.command_input.value or ""
        if not text.strip():
            return
        result = self.bank.execute_batch(text)
        if result:
            old = (self.result_output.value or "").rstrip()
            self.result_output.value = f"{old}\n{result}".strip() if old else result
        self.update()

    def load_file(self, _event=None):
        raw_path = (self.file_input.value or "").strip()
        if not raw_path:
            self.status.value = "Укажите имя или путь к файлу."
            self.update()
            return

        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
        try:
            self.command_input.value = path.read_text(encoding="utf-8")
            self.status.value = f"Загружено: {path.name}. Команды ещё не выполнены."
            self.status.color = MAIN_COLOR
        except (OSError, UnicodeError) as error:
            self.status.value = f"Не удалось загрузить файл: {error}"
            self.status.color = ERROR_COLOR
        self.update()

    def clear_input(self, _event=None):
        self.command_input.value = ""
        self.update()

    def clear_output(self, _event=None):
        self.result_output.value = ""
        self.update()


def main(page: ft.Page):
    page.title = "Bank System"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.min_width = 900
    page.window.min_height = 760
    page.add(MainWindow())


if __name__ == "__main__":
    ft.run(main)
