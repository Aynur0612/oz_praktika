import argparse
import math
from pathlib import Path
import sys

import matplotlib
import numpy as np
import pandas as pd


MIN_VALUE = -10_000
MAX_VALUE = 10_000
DATA_COUNT = 1_000


def generate_series(seed: int | None = None) -> pd.Series:
    """Генерирует Series из 1000 случайных целых чисел заданного диапазона."""
    generator = np.random.default_rng(seed)
    values = generator.integers(
        MIN_VALUE,
        MAX_VALUE + 1,
        size=DATA_COUNT,
        dtype=np.int64,
    )
    return pd.Series(values, name="Исходные значения")


def calculate_statistics(series: pd.Series) -> dict[str, int | float]:
    """Рассчитывает требуемые стандартные числовые характеристики."""
    values = series.to_numpy(dtype=float)
    mean = float(np.mean(values))
    rms_deviation = math.sqrt(float(np.mean((values - mean) ** 2)))
    frequencies = series.value_counts()

    return {
        "minimum": int(series.min()),
        "duplicate_elements": int(series.duplicated().sum()),
        "repeated_unique_values": int((frequencies > 1).sum()),
        "maximum": int(series.max()),
        "sum": int(series.sum()),
        "rms_deviation": rms_deviation,
    }


def round_to_hundreds(series: pd.Series) -> pd.Series:
    """Округляет до сотен по правилу: 50 округляется от нуля."""
    values = series.to_numpy(dtype=float)
    rounded = np.sign(values) * np.floor(np.abs(values) / 100 + 0.5) * 100
    return pd.Series(rounded.astype(np.int64), name="Округлено до сотен")


def build_dataframe(series: pd.Series) -> pd.DataFrame:
    """Формирует DataFrame с исходными и двумя отсортированными наборами."""
    return pd.DataFrame(
        {
            "Исходные значения": series.reset_index(drop=True),
            "По возрастанию": series.sort_values(ascending=True, ignore_index=True),
            "По убыванию": series.sort_values(ascending=False, ignore_index=True),
        }
    )


def print_results(statistics: dict[str, int | float], dataframe: pd.DataFrame):
    print("Результаты анализа Series")
    print(f"Минимальное значение: {statistics['minimum']}")
    print(
        "Количество повторяющихся элементов "
        f"(без первых вхождений): {statistics['duplicate_elements']}"
    )
    print(
        "Количество различных значений, встречающихся более одного раза: "
        f"{statistics['repeated_unique_values']}"
    )
    print(f"Максимальное значение: {statistics['maximum']}")
    print(f"Сумма чисел: {statistics['sum']}")
    print(
        "Среднеквадратическое отклонение: "
        f"{statistics['rms_deviation']:.6f}"
    )
    print("\nПервые пять строк сформированного DataFrame:")
    print(dataframe.head().to_string(index=False))


def create_visualizations(
    series: pd.Series,
    rounded_series: pd.Series,
    dataframe: pd.DataFrame,
    output_directory: Path,
    show: bool = True,
) -> list[Path]:
    """Строит и сохраняет три визуализации из задания."""
    if not show:
        matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    output_directory.mkdir(parents=True, exist_ok=True)
    saved_files: list[Path] = []

    figure_1, axis_1 = plt.subplots(figsize=(12, 5))
    axis_1.plot(series.index, series.values, color="royalblue", linewidth=0.9)
    axis_1.set_title("Линейный график исходного Series")
    axis_1.set_xlabel("Индекс элемента")
    axis_1.set_ylabel("Значение")
    axis_1.grid(True, alpha=0.3)
    figure_1.tight_layout()
    line_path = output_directory / "01_line_plot.png"
    figure_1.savefig(line_path, dpi=150)
    saved_files.append(line_path)

    figure_2, axis_2 = plt.subplots(figsize=(12, 5))
    bin_edges = np.arange(MIN_VALUE - 50, MAX_VALUE + 151, 100)
    axis_2.hist(
        rounded_series.values,
        bins=bin_edges,
        color="darkorange",
        edgecolor="black",
        linewidth=0.35,
        rwidth=0.9,
    )
    axis_2.set_title("Гистограмма значений, округлённых до сотен")
    axis_2.set_xlabel("Округлённое значение")
    axis_2.set_ylabel("Количество")
    axis_2.grid(axis="y", alpha=0.3)
    figure_2.tight_layout()
    histogram_path = output_directory / "02_histogram_hundreds.png"
    figure_2.savefig(histogram_path, dpi=150)
    saved_files.append(histogram_path)

    figure_3, axis_3 = plt.subplots(figsize=(12, 6))
    axis_3.plot(
        dataframe.index,
        dataframe["По возрастанию"],
        label="По возрастанию",
        color="seagreen",
        linewidth=1.5,
    )
    axis_3.plot(
        dataframe.index,
        dataframe["По убыванию"],
        label="По убыванию",
        color="crimson",
        linewidth=1.5,
    )
    axis_3.set_title("Отсортированные значения Series")
    axis_3.set_xlabel("Позиция после сортировки")
    axis_3.set_ylabel("Значение")
    axis_3.legend()
    axis_3.grid(True, alpha=0.3)
    figure_3.tight_layout()
    sorted_path = output_directory / "03_sorted_line_plots.png"
    figure_3.savefig(sorted_path, dpi=150)
    saved_files.append(sorted_path)

    if show:
        plt.show()
    plt.close("all")
    return saved_files


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SimpleAnalysis")
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed генератора для воспроизводимого результата.",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Сохранить графики без открытия окон.",
    )
    return parser.parse_args()


def application_directory() -> Path:
    """Возвращает папку скрипта либо папку собранного one-file EXE."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    arguments = parse_arguments()
    series = generate_series(arguments.seed)
    statistics = calculate_statistics(series)
    dataframe = build_dataframe(series)
    rounded_series = round_to_hundreds(series)

    print_results(statistics, dataframe)

    output_directory = application_directory() / "plots"
    saved_files = create_visualizations(
        series,
        rounded_series,
        dataframe,
        output_directory,
        show=not arguments.no_show,
    )
    print("\nГрафики сохранены:")
    for path in saved_files:
        print(f"- {path}")


if __name__ == "__main__":
    main()
