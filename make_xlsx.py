import xlsxwriter
import csv
import os
from typing import List, Optional
from tqdm import tqdm
from parser import Product, get_usd
from singletons.console import ConsoleSingleton
from singletons.logger import get_logger
from singletons.config import Config

# Configuration and logger
config = Config()
logger = get_logger()
console_out = ConsoleSingleton()

def load_input_data(path_input: str) -> List[List[str]]:
    """Loads data from the input CSV file."""
    if not os.path.exists(path_input):
        logger.error(f"Input file does not exist: {path_input}")
        raise FileNotFoundError(f"Input file does not exist: {path_input}")

    with open(path_input, "r") as file_in:
        reader = csv.reader(file_in, delimiter=";")
        return list(reader)

def initialize_workbook(path_output: str):
    """Initializes an Excel workbook with column formatting and headers."""
    if os.path.exists(path_output):
        os.remove(path_output)
        logger.info(f"Old file {path_output} deleted.")

    workbook = xlsxwriter.Workbook(path_output)
    worksheet = workbook.add_worksheet("Products")

    formats = {
        "bold": workbook.add_format({"bold": True}),
        "italic": workbook.add_format({"italic": True}),
        "highlight": workbook.add_format({"bg_color": "#C6EFCE", "bold": True}),
    }

    headers = ["Brand", "Product Name", "Variant", "Ref Price", "Makeup Price", "Region", "Info"]
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header, formats["bold"])

    worksheet.set_column(0, 0, 15)
    worksheet.set_column(1, 1, 35)
    worksheet.set_column(2, 2, 25)
    worksheet.set_column(3, 4, 5)
    worksheet.set_column(4, 4, 5)
    worksheet.set_column(5, 5, 5)
    worksheet.set_column(6, 6, 50)

    return workbook, worksheet, formats

def parse_ref_price(row: List[str], usd_rate: float) -> Optional[int]:
    """Parses and converts the reference price."""
    try:
        if row[2]:
            return round(float(row[2].replace(",", ".")) * usd_rate)
        elif row[3]:
            return int(row[3])
    except ValueError:
        logger.warning(f"Invalid ref price value: {row}")
    return None

def process_product_row(product: Product, ref_price: int, target_variant: str = None) -> Optional[List[List]]:
    """Processes a single product for Excel output."""
    rows = []

    if (not product.positions) or (len(product.positions) == 0):
        logger.warning(f"No positions found for product: {product.name} from URL {product.url}")
        if product.has_error:
            row = [
                product.brand,
                product.name,
                None,
                ref_price,
                None,
                None,
                product.info or "Error - no positions",
                product.url
            ]
            rows.append(row)
        return rows if rows else None

    for variant in product.positions:
        if target_variant and target_variant not in (variant.title or ""):
            continue
        if variant.price < ref_price or product.has_error:
            row = [
                product.brand,
                product.name,
                variant.title,
                ref_price,
                variant.price,
                "EU" if variant.eu else "UA",
                product.info or "",
                product.url
            ]
            rows.append(row)

    return rows if rows else None


def write_products(worksheet, products: List[List], linecount: int, formats) -> int:
    """Writes processed product data to the Excel worksheet."""
    for product in products:
        for row in product:
            worksheet.write(linecount, 0, row[0], formats["italic"])
            worksheet.write_url(linecount, 1, row[7], string=row[1])
            for col_num, cell_data in enumerate(row[2:7], start=2):
                format_to_use = formats["highlight"] if col_num == 4 and "On sale" in row else formats["italic"]
                worksheet.write(linecount, col_num, cell_data, format_to_use)
            linecount += 1
    return linecount
def process_product_list(path_input: str = 'input_table.csv', path_output: str = 'out_table.xlsx'):
    """Main function to create Excel table with processed products."""
    try:
        data_rows = load_input_data(path_input)
        console_out.info(f"Вхідна таблиця {path_input} завантажена.")
        usd_rate = get_usd()
        console_out.info(f"Курс USD: {usd_rate}")
        workbook, worksheet, formats = initialize_workbook(path_output)

        linecount = 1
        sale_products = []
        regular_products = []
        error_products = []

        console_out.info("Обробка продуктів...")
        logger.info("Starting product processing...")
        for row in tqdm(data_rows, desc="Processing products"):
            ref_price = parse_ref_price(row, usd_rate)
            if ref_price is None:
                logger.warning(f"Skipping product due to invalid ref price: {row}")
                continue

            try:
                product = Product.from_url(row[0])
                processed_rows = process_product_row(product, ref_price, row[1] if len(row) > 1 else None)
                if processed_rows is None:
                    continue
                elif product.has_error:
                    error_products.append(processed_rows)
                elif product.sale_params:
                    sale_products.append(processed_rows)
                else:
                    regular_products.append(processed_rows)

            except Exception as e:
                logger.error(f"Error processing product at URL {row[0]}: {e}")
                error_product = Product(name="Unknown", brand="Unrecognized", url=row[0], positions=[], info=str(e), has_error=True)
                error_products.append(process_product_row(error_product, ref_price))


        console_out.info("Завершено!")

        products_len = len(regular_products) + len(sale_products) + len(error_products)

        if products_len > 0:
            console_out.info(f"Оброблено {products_len} продуктів:")
            if len(regular_products) > 0:
                console_out.success(f'Серед них {len(regular_products)} звичайних')
            if len(sale_products) > 0:
                console_out.warning(f'{len(sale_products)} акційних')
            if len(error_products) > 0:
                console_out.error(f'{len(error_products)} з помилками')
        else:
            console_out.warning("Але у результаті вийшло 0 продуктів")
            console_out.info("Тому програма завершується")
            return


        # Write sale, regular, and error products in order
        console_out.info("Запис у файл xlsx...")
        linecount = write_products(worksheet, sale_products, linecount, formats)
        linecount = write_products(worksheet, regular_products, linecount, formats)
        write_products(worksheet, error_products, linecount, formats)

        workbook.close()
        console_out.success(f"Файл {path_output} створено!")
        logger.info("Excel file created successfully.")
    except Exception as e:
        logger.critical(f"Failed to create Excel file: {e}")
        console_out.critical(f"Критична помилка: {e}")
        raise e

if __name__ == "__main__":
    process_product_list(config.get("input_file"), config.get("output_file"))
