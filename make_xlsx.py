import csv
import os
from typing import List, Optional, Tuple
from tqdm import tqdm
from parser import Product, get_usd
from singletons.console import ConsoleSingleton
from singletons.logger import get_logger
from singletons.config import Config
from xlsx.xlsx_table_generator import XlsxTableGenerator

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


def process_product(product: Product, ref_price: int) -> Tuple[Product | None, bool]:
    """
    Processes a product and filters its variants based on reference price.

    Args:
        product: Product object containing variants
        ref_price: Reference price for filtering variants

    Returns:
        Tuple[Product | None, bool]: Processed product (or None) and sale status
    """
    # Filter variants in a list comprehension instead of modifying while iterating
    product.positions = [
        variant for variant in product.positions
        if variant.price < ref_price
    ]

    # Early return if no positions left
    if not product.positions:
        return None, False

    # Simplified return using direct boolean check
    return product, bool(product.sale_params)


def process_row(row: List[str], usd_rate: float, product_lists: dict[str, List[Product]]) -> None:
    """
    Process a single row of product data.

    Args:
        row: List of strings containing product data
        usd_rate: Current USD exchange rate
        product_lists: Dictionary containing lists of different product categories

    Returns:
        None
    """
    if not row:
        logger.warning("Empty row received")
        return

    try:
        # Get reference price
        ref_price = parse_ref_price(row, usd_rate)
        if ref_price is None:
            logger.warning(f"Skipping product due to invalid ref price: {row}")
            return

        # Create product from URL
        product = Product.from_url(row[0])

        # Handle error cases
        if product.has_error:
            product_lists["error_products"].append(product)
            return

        if not product.positions or len(product.positions) == 0:
            logger.warning(f"No variants found for product: {row}")
            return

        # Filter variants by title if specified
        variant_filter = row[1]
        if variant_filter:
            product.positions = [
                variant for variant in product.positions
                if variant_filter in variant.title
            ]

            if not product.positions:
                logger.warning(f"No variants match the filter '{variant_filter}' for product: {row}")
                return

        # Process product and determine if it's on sale
        final_product, is_sale = process_product(product, ref_price)
        if not final_product:
            return

        # Set reference price and add to appropriate list
        final_product.ref_price = ref_price
        product_lists["sale_products" if is_sale else "regular_products"].append(final_product)

    except Exception as e:
        logger.error(f"Error processing row {row}: {str(e)}")
        product_lists["error_products"].append(
            Product(
                name="Error",
                brand="Error",
                url=row[0] if row else "Unknown",
                positions=[],
                info=str(e),
                has_error=True
            )
        )


def process_product_list(path_input: str = 'input_table.csv', path_output: str = 'out_table.xlsx'):
    """Main function to create Excel table with processed products."""
    data_rows = load_input_data(path_input)
    console_out.info(f"Вхідна таблиця {path_input} завантажена.")
    usd_rate = get_usd()
    console_out.info(f"Курс USD: {usd_rate}")

    product_lists = {
        "sale_products": [],
        "regular_products": [],
        "error_products": []
    }

    console_out.info("Обробка продуктів...")
    logger.info("Starting product processing...")
    for row in tqdm(data_rows, desc="Processing products"):
        process_row(row, usd_rate, product_lists)

    console_out.info("Завершено!")

    products_len = product_lists["sale_products"].__len__() + product_lists["regular_products"].__len__() + product_lists["error_products"].__len__()

    if products_len > 0:
        console_out.info(f"Оброблено {products_len} продуктів.\nСеред них:")
        if product_lists["regular_products"].__len__() > 0:
            console_out.success(f'{product_lists["regular_products"].__len__()} звичайних')
        if product_lists["sale_products"].__len__() > 0:
            console_out.warning(f'{product_lists["sale_products"].__len__()} акційних')
        if product_lists["error_products"].__len__() > 0:
            console_out.error(f'{product_lists["error_products"].__len__()} з помилками')
    else:
        console_out.warning("Але у результаті вийшло 0 продуктів")
        console_out.info("Тому програма завершується")
        return

    console_out.info("Створюємо таблицю...")
    logger.info("Creating Excel table...")
    with XlsxTableGenerator(config) as xlsx_table:
        for product in product_lists["sale_products"]:
            xlsx_table.add_product(product, ref_price=product.ref_price)
        for product in product_lists["regular_products"]:
            xlsx_table.add_product(product, ref_price=product.ref_price)
        for product in product_lists["error_products"]:
            xlsx_table.add_product(product, ref_price=product.ref_price)

    console_out.success(f"Таблиця створена успішно: {path_output}")


if __name__ == "__main__":
    process_product_list(config.get("input_file"), config.get("output_file"))
