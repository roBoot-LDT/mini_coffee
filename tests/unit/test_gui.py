from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()


def calculate(a: float, b: float, operation: str) -> float:
    """Выполняет арифметическую операцию между двумя числами."""
    if operation == "+":
        return a + b
    elif operation == "-":
        return a - b
    elif operation == "*":
        return a * b
    elif operation == "/":
        if b == 0:
            raise ZeroDivisionError("Деление на ноль невозможно.")
        return a / b
    else:
        raise ValueError("Недопустимая операция. Используйте +, -, *, /.")


def analyze_data(data_string: str) -> dict:
    """Проводит базовый анализ числовых данных, введённых через запятую."""
    try:
        numbers = [float(x.strip()) for x in data_string.split(",")]
    except ValueError:
        raise ValueError("Все элементы должны быть числами, разделёнными запятой.")

    return {
        "sum": sum(numbers),
        "avg": sum(numbers) / len(numbers),
        "unique": set(numbers),
        "sorted": sorted(numbers),
        "min_max": (min(numbers), max(numbers))
    }


def render_analysis(results: dict):
    """Форматирует и отображает результаты анализа данных."""
    table = Table(title="Анализ данных", title_style="bold cyan", show_lines=True)

    table.add_column("Показатель", style="bold")
    table.add_column("Значение")

    table.add_row("Сумма", f"{results['sum']}")
    table.add_row("Среднее", f"{results['avg']:.2f}")
    table.add_row("Уникальные", f"{results['unique']}")
    table.add_row("Отсортированный список", f"{results['sorted']}")
    table.add_row("Мин/Макс", f"{results['min_max']}")

    console.print(table)


def main():
    """Основной цикл работы программы."""
    console.print(Panel("Калькулятор и Анализатор данных", style="bold green"))

    while True:
        mode = Prompt.ask("\nВыберите режим (calc/data/exit)", choices=["calc", "data", "exit"])

        if mode == "exit":
            console.print("[italic red]Завершение программы.[/italic red]")
            break

        elif mode == "calc":
            try:
                a = float(Prompt.ask("Введите первое число"))
                operation = Prompt.ask("Введите операцию (+, -, *, /)", choices=["+", "-", "*", "/"])
                b = float(Prompt.ask("Введите второе число"))
                result = calculate(a, b, operation)
                console.print(f"[bold green]Результат:[/bold green] {result}")
            except Exception as e:
                console.print(f"[bold red]Ошибка:[/bold red] {e}")

        elif mode == "data":
            try:
                data_string = Prompt.ask("Введите числа через запятую (пример: 1, 2, 3)")
                results = analyze_data(data_string)
                render_analysis(results)
            except Exception as e:
                console.print(f"[bold red]Ошибка:[/bold red] {e}")


if __name__ == "__main__":
    main()
