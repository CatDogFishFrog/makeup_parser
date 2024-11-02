import argparse
import textwrap
from pathlib import Path
from loguru import logger
from .config import settings
from .excel_processor import ExcelProcessor


def setup_logger():
    """Налаштування логування."""
    logger.add(
        settings.ERROR_LOG,
        rotation="1 MB",
        level="DEBUG" if settings.DEBUG else "INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )


def parse_arguments():
    """Парсинг аргументів командного рядка."""
    description = textwrap.dedent("""
        Створення таблиці з обраних товарів з сайту makeup.com.ua.

        Вхідні дані:
        - CSV файл з колонками: URL, Варіант (опціонально), Ціна USD, Ціна UAH
        - Якщо вказані обидві ціни, використовується USD

        Вихідні дані:
        - XLSX файл з відфільтрованими позиціями
        - За замовчуванням виводяться позиції з ціною нижче референтної
        - Опція -f виводить всі позиції
    """)

    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--input", "-i",
        type=Path,
        default=settings.INPUT_FILE,
        help="Шлях до вхідного CSV файлу"
    )

    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=settings.OUTPUT_FILE,
        help="Шлях до вихідного XLSX файлу"
    )

    parser.add_argument(
        "--full", "-f",
        action="store_true",
        help="Вивести всі позиції без фільтрації за ціною"
    )

    return parser.parse_args()


def main():
    """Головна функція програми."""
    setup_logger()
    args = parse_arguments()

    logger.info("Початок обробки даних")
    processor = ExcelProcessor(args.input, args.output)
    result = processor.process_data(full_table=args.full)

    if result.success:
        logger.info(result.message)
        print(result.message)
    else:
        logger.error(result.error)
        print(f"Помилка: {result.error}")


if __name__ == "__main__":
    main()