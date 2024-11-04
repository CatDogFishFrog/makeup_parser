import xlsxwriter
import csv
import os
from typing import List
from tqdm import tqdm
from parser import Product, get_usd
from singletons.logger import get_logger
from singletons.config import Config

# Конфігурація та логування
config = Config()
logger = get_logger()


def load_input_data(path_input: str) -> List[List[str]]:
    """Завантажує дані з вхідного файлу CSV."""
    if not os.path.exists(path_input):
        logger.error(f"Вхідного файла не існує: {path_input}")
        raise FileNotFoundError(f"Вхідного файла не існує: {path_input}")

    with open(path_input, "r") as file_in:
        reader = csv.reader(file_in, delimiter=";")
        return list(reader)


def initialize_workbook(path_output: str):
    """Ініціалізує вихідну книгу Excel та лист з форматом колонок."""
    if os.path.exists(path_output):
        os.remove(path_output)
        logger.info(f"Старий файл {path_output} видалено.")

    workbook = xlsxwriter.Workbook(path_output)
    worksheet = workbook.add_worksheet("output_list")

    formats = {
        "bold": workbook.add_format({"bold": True}),
        "italic": workbook.add_format({"italic": True})
    }

    setup_worksheet(worksheet, formats["bold"])
    return workbook, worksheet, formats


def setup_worksheet(worksheet, bold_format):
    """Налаштовує форматування колонок і заголовків."""
    worksheet.set_column(0, 0, 35)
    worksheet.set_column(1, 1, 20)
    worksheet.set_column(2, 2, 6)
    worksheet.set_column(3, 3, 6)
    worksheet.set_column(4, 4, 3)
    worksheet.set_column(5, 5, 40)

    headers = ["Назва товару", "Варіант", "ref Ціна", "makeup Ціна", "Склад", "URL", "info"]
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header, bold_format)


def parse_ref_price(row: List[str], usd_rate: float) -> int | None:
    """Парсить і конвертує референсну ціну."""
    try:
        if row[2]:
            return round(float(row[2].replace(",", ".")) * usd_rate)
        elif row[3]:
            return int(row[3])
    except ValueError:
        logger.warning(f"Некоректне значення ref price: {row}")
    return None


def process_product_row(product: Product, ref_price: int, full_table: bool) -> List[List]:
    """Обробляє окремий продукт для запису в Excel."""
    rows = []
    for variant in product.positions:
        if ref_price < variant['price'] or (variant['title'] and row[1] not in variant['title'] and not full_table):
            continue
        row = [
            product.name,
            variant["title"],
            ref_price,
            variant["price"],
            "EU" if variant["eu"] else "UA",
            product.url,
            product.info or ""
        ]
        rows.append(row)
    return rows


def write_products(worksheet, products, linecount, formats):
    """Записує дані продуктів у таблицю."""
    for product in products:
        for row in product:
            for col_num, cell_data in enumerate(row):
                worksheet.write(linecount, col_num, cell_data,
                                formats["bold"] if col_num in [0, 1] else formats.get("italic", None))
            linecount += 1
    return linecount


def make_xlsx(path_input: str = 'input_table.csv', path_output: str = 'out_table.xlsx', full_table: bool = False):
    """Основна функція для створення таблиці Excel з обробкою продуктів."""
    try:
        data_rows = load_input_data(path_input)
        usd_rate = get_usd()
        workbook, worksheet, formats = initialize_workbook(path_output)

        linecount = 1
        sale_products = []
        regular_products = []
        error_products = []

        logger.info("Початок обробки продуктів...")
        for row in tqdm(data_rows, desc="Обробка продуктів"):
            ref_price = parse_ref_price(row, usd_rate)
            if ref_price is None:
                logger.warning(f"Продукт пропущено через відсутність коректної ref price: {row}")
                continue

            try:
                product = Product.from_url(row[0])
                if product.has_error:
                    error_products.append(process_product_row(product, ref_price, full_table))
                    continue

                processed_rows = process_product_row(product, ref_price, full_table)
                if product.on_sale:
                    sale_products.append(processed_rows)
                else:
                    regular_products.append(processed_rows)

            except Exception as e:
                logger.error(f"Помилка під час обробки продукту за URL {row[0]}: {e}")
                product = Product(name="Unknown", url=row[0], positions=[], info=str(e), has_error=True)
                error_products.append(process_product_row(product, ref_price, full_table))

        # Запис акційних продуктів, звичайних, і з помилками
        linecount = write_products(worksheet, sale_products, linecount, formats)
        linecount = write_products(worksheet, regular_products, linecount, formats)
        write_products(worksheet, error_products, linecount, formats)

        workbook.close()
        logger.info("Таблиця успішно створена.")
    except Exception as e:
        logger.critical(f"Таблиця не була створена: {e}")
        raise e
