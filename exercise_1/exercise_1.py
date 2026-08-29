from string import punctuation
from pathlib import Path
import sys


def resource_path(filename: str) -> Path:
    """Возвращает путь к ресурсу как для Python, так и для one-file EXE."""
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base_path / filename


def output_path(filename: str) -> Path:
    """Сохраняет результат рядом со скриптом или собранным EXE."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / filename
    return Path(__file__).resolve().parent / filename


def sort_words(words_list: list) -> list:
    """
    Запускает цикл for для списка с дополнительным счетчиком
    Цикл проходит по словам, проверяет число из кортежа
    и если число не совпадает с числом key, то присваивает
    key значение числа и добавляет значения из буферного листа
    в reversed_list, предварительно отзеркалив их.
    Если число совпадает с key, то добавляем кортеж в
    буфферный лист.
    При использование стандартного метода list.sort() с параметром
    reverse=True, данные сортируются по убыванию сначала для первого
    элемента кортежа, а потом и для второго. Но по условиям задачи
    список должен быть отсортирован в обратном порядке для числа и
    в прямом порядке для слова. Эта функция решает данную проблему.
    :param words_list:
    :return:
    """
    reversed_list = []
    key = 0
    buffer_list = []

    # Сортируем лист в прямом порядке
    words_list.sort(reverse=True)

    for i, word in enumerate(words_list):
        if key != word[0]:
            key = word[0]
            buffer_list.reverse()
            reversed_list += buffer_list
            buffer_list.clear()
        buffer_list.append(word)
        if i + 1 == len(words_list):
            buffer_list.reverse()
            reversed_list += buffer_list
    # Возращаем полученный лист
    return reversed_list


# Читаем содержимое входного файла в кодировке UTF-8,
# убирая переносы в конце и в начале
try:
    with resource_path('resource_1.txt').open(encoding='utf-8') as input_data:
        data = input_data.read().strip()
# Обработка исключения, если файл не найден
except FileNotFoundError:
    data = []
    print('Файл exercise_1\\resource_1.txt не найден '
          'или программа запущена из неверной директории')

# Убираем переносы внутри текста
data = data.replace('\n', ' ')

# Убираем все знаки пунктуации в тексте
for p in punctuation:
    data = data.replace(p, '')

# Создаем пустой лист для слов в тексте
words_counts = []

# Проходим в цикле for по словам в тексте,
# которые преобразовываем в список методом
# split(), разделяя слова пробелами
for word in data.split(' '):
    # Проверка на пустое слово
    if word != '':
        # Заменяем все буквы в слове на строчные (маленькие)
        word = word.lower()
        # Создаем список слов из кортежей в генерируем списке
        # с помощью list comprehensions
        words = [w[1] for w in words_counts]

        # Проверяем существование слова сгенерированном списке
        if word not in words:
            # Создаем кортеж
            words_counts.append((1, word))
        else:
            # Увеличиваем число повторения слова в кортеже
            index = words.index(word)
            words_counts[index] = (words_counts[index][0] + 1, word)


# Проверка аргументов при запуске
if len(sys.argv) > 1 and sys.argv[1] == "-c":
    # Вывод результата в файл
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for word in sort_words(words_counts):
        print(word[1], word[0])
else:
    # Выгрузка результата в файл
    try:
        with output_path('result.txt').open('w', encoding='utf-8') as output_data:
            output_data.writelines([f'{a} {b}\n' for a, b in sort_words(words_counts)])
    # Проверка файл на недоступность/занятость другой программой
    except PermissionError:
        print('Закройте файл и повторите запрос!')
    else:
        print('Результат выгружен в файл result.txt')

