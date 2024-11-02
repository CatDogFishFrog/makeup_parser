import xlsxwriter
from typing import List, Dict, Any
from pathlib import Path
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from loguru import logger
from .models import Product, ProcessingResult
from .parsers import MakeupParser
import csv


class ExcelProcessor:
    def __init__(self, input_path: Path, output_path: Path):
        self.input_path = input_path
        self.output_path = output_path
        self.parser = MakeupParser()

    def _setup_worksheet(self, workbook: xlsxwriter.Workbook) -> tuple:
        """Налаштовує форматування та заголовки worksheet."""
        worksheet = workbook.add_worksheet("output_list")
        bold = workbook.add_format({"bold": True})
        italic = workbook.add_format({"italic": True})

        # Встановлення ширини колонок
        column_widths = [35, 20, 6, 6, 3, 40]
        for i, width in enumerate(column_widths):
            worksheet.set_column(i, i, width)

        # Заголовки
        headers = ["Назва товару", "Варіант", "ref Ціна", "makeup Ціна", "Склад", "URL"]
        for i, header in enumerate(headers):
            worksheet.write(0, i, header, bold)

        return worksheet, bold, italic

    def process_data(self, full_table: bool = False) -> ProcessingResult:
        """Обробляє дані та створює Excel файл."""
        try:
            if not self.input_path.exists():
                return ProcessingResult(
                    success=False,
                    error=f"Вхідний файл не існує: {self.input_path}"
                )

            # Отримуємо курс USD
            usd_rate = self.parser.get_usd_rate()
            logger.info(f"Поточний курс USD: {usd_rate}")

            # Створюємо новий Excel файл
            workbook = xlsxwriter.Workbook(str(self.output_path))
            worksheet, bold, italic = self._setup_worksheet(workbook)

            row = 1  # Починаємо з другого рядка після заголовків
            skipped_items = []

            # Підраховуємо кількість рядків для прогрес-бару
            with open(self.input_path, "r") as f:
                total_rows = sum(1 for _ in csv.reader(f))

            with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                    TimeRemainingColumn(),
            ) as progress:
                task = progress.add_task("Обробка товарів...", total=total_rows)

                with open(self.input_path, "r") as file:
                    reader = csv.reader(file, delimiter=";")

                    for line in reader:
                        progress.update(task, advance=1)

                        try:
                            url, variant_filter, ref_price_usd, ref_price_uah = line + [""] * (4 - len(line))

                            # Визначення референтної ціни
                            if ref_price_usd:
                                ref_price = round(float(ref_price_usd.replace(",", ".")) * usd_rate)
                            elif ref_price_uah:
                                ref_price = int(ref_price_uah)
                            else:
                                skipped_items.append(f"Пропущено: немає референтної ціни для {url}")
                                continue

                            # Парсинг продукту
                            product = self.parser.parse_product(url)
                            if not product:
                                continue

                            # Фільтрація та запис варіантів
                            for variant in product.variants:
                                if full_table or (
                                        ref_price >= variant.price
                                        and (not variant_filter or variant_filter in variant.title)
                                ):
                                    worksheet.write(row, 0, product.name, bold)
                                    worksheet.write(row, 1, variant.title)
                                    worksheet.write(row, 2, ref_price, italic)
                                    worksheet.write(row, 3, variant.price)
                                    worksheet.write(row, 4, "EU" if variant.eu_stock else "UA")
                                    worksheet.write(row, 5, str(product.url))
                                    row += 1

                        except Exception as e:
                            logger.error(f"Помилка обробки рядка: {e}")
                            skipped_items.append(f"Помилка: {str(e)} для {url}")

            workbook.close()

            result_message = "Таблиця успішно створена"
            if skipped_items:
                result_message += f"\nПропущені позиції:\n" + "\n".join(skipped_items)

            return ProcessingResult(success=True, message=result_message)

        except Exception as e:
            logger.error(f"Критична помилка: {e}")
            return ProcessingResult(success=False, error=str(e))