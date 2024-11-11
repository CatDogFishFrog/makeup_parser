from typing import Any, Dict, List, Union, Optional
from functools import lru_cache
from utils.hex_tools import darken_color
import xlsxwriter
from parser import SaleParams, Product
from singletons.config import Config
from xlsx.xlsx_column_setting import XlsxColumnSetting
from singletons.logger import get_logger

logger = get_logger()

class XlsxTableGenerator:
    """Class for generating Excel tables."""

    HEADER_FORMAT = {
        "bold": True,
        "italic": True,
        "font_size": 14,
        "align": "center"
    }

    def __init__(self, config: Config):
        """Initialize XlsxTableGenerator with configuration."""
        logger.debug("Initializing XlsxTableGenerator")
        self.config = config
        self.output_file = self.config.get("output_file", "output.xlsx")

        try:
            logger.info(f"Creating Excel workbook: {self.output_file}")
            self.workbook = xlsxwriter.Workbook(self.output_file)
            self.worksheet = self.workbook.add_worksheet()
        except OSError as e:
            logger.error(f"Failed to create Excel workbook: {str(e)}")
            raise RuntimeError(f"Failed to create Excel workbook:\n{str(e)}")

        self.row_index = 1
        logger.debug("Loading table settings")
        self.table_settings = self._load_table_settings()
        self._cell_type_mapping = self._init_cell_type_mapping()
        self.headers_setting = XlsxColumnSetting.from_dict(self.config.get("headers_format", self.HEADER_FORMAT))
        self.striped_zebra = self.config.get("striped_zebra", False)
        self._set_headers()

        for col_index, setting in enumerate(self.table_settings):
            self.worksheet.set_column(col_index, col_index, setting.width)
        logger.info("XlsxTableGenerator initialized successfully")

    @staticmethod
    def _init_cell_type_mapping() -> Dict[str, callable]:
        """Initialize cell type mapping."""
        logger.debug("Initializing cell type mapping")
        return {
            'brand': lambda p, v, r: p.brand,
            'name': lambda p, v, r: (p.name, p.url),  # Tuple to identify as hyperlink
            'error': lambda p, v, r: "ERROR" if p.has_error else "",
            'rprice': lambda p, v, r: r,
            'mprice': lambda p, v, r: v.price,
            'variant': lambda p, v, r: v.title,
            'info': lambda p, v, r: ", ".join((info for info in (p.info, v.info) if info is not None)),
            'region': lambda p, v, r: "EU" if v.eu else "UA",
            'saleformula': lambda p, v, r: v.sale_params.price_formula if v.sale_params else ""
        }

    def _load_table_settings(self) -> List[XlsxColumnSetting]:
        """Load and validate table settings from configuration."""
        logger.debug("Loading table settings from configuration")
        settings = self.config.get("xlsx_table_settings", {})
        if not settings:
            logger.error("No table settings found in configuration")
            raise ValueError("No table settings found in configuration")

        table_settings = [
            XlsxColumnSetting.from_dict(column)
            for key, column in settings.items()
            if not key.startswith("_")
        ]
        logger.info(f"Loaded {len(table_settings)} table settings")
        return table_settings

    def _set_headers(self) -> None:
        """Set table headers with validated formatting using XlsxColumnSetting."""
        header_format = self.workbook.add_format(self._get_cell_format(self.headers_setting))
        for col_index, setting in enumerate(self.table_settings):
            self.worksheet.write(0, col_index, setting.header, header_format)
        logger.debug("Table headers set successfully")

    @lru_cache(maxsize=128)
    def _get_cell_value(self, cell_type: str, product: Any, variant: Any, ref_price: Any) -> Any:
        """Get cell value with error handling."""
        handler = self._cell_type_mapping.get(cell_type.lower())
        try:
            return handler(product, variant, ref_price) if handler else None
        except AttributeError as e:
            logger.warning(f"Failed to get cell value for type {cell_type}: {str(e)}")
            return None

    @staticmethod
    def _get_cell_format(setting: XlsxColumnSetting, sale_params: Optional[SaleParams] = None) -> Dict[str, Any]:
        """Get cell format based on settings and sale parameters."""
        logger.debug("Getting cell format with settings: {}", setting)
        return {
            "bg_color": sale_params.price_background_color_hex if sale_params else setting.background_color_hex,
            "font_color": sale_params.price_font_color_hex if sale_params else setting.font_color_hex,
            "font_name": setting.font_name,
            "font_size": setting.font_size,
            "bold": setting.bold,
            "italic": setting.italic,
            "underline": setting.underline,
            "align": setting.align
        }

    def add_product(self, product: Product, ref_price: Union[int, float]) -> None:
        """Add product data with error handling."""
        logger.info("Adding product {} with reference price {}", product.name, ref_price)
        try:
            for variant in product.positions:
                logger.debug("Processing variant: {}", variant.title)
                row_data = [
                    self._get_cell_value(setting.type, product, variant, ref_price)
                    for setting in self.table_settings
                ]
                self._write_row(row_data, getattr(variant, 'sale_params', None))
        except Exception as e:
            logger.error("Failed to add product {}: {}", product.name, str(e))
            raise RuntimeError(f"Failed to add product: {str(e)}")

    def _write_row(self, row: List[Any], sale_params: Optional[SaleParams] = None) -> None:
        """Write a row, creating hyperlinks for 'name' type cells."""
        for col_index, value in enumerate(row):
            setting = self.table_settings[col_index]
            cell_format_dict = self._get_cell_format(setting, sale_params)
            if self.striped_zebra and self.row_index % 2 != 0:
                cell_format_dict["bg_color"] = darken_color(cell_format_dict["bg_color"])

            cell_format = self.workbook.add_format(cell_format_dict)

            # Check if the cell is a hyperlink for "Product Name" type
            if setting.type.lower() == "name" and isinstance(value, tuple) and len(value) == 2:
                text, url = value
                self.worksheet.write_url(self.row_index, col_index, url, cell_format, string=text)
            else:
                self.worksheet.write(self.row_index, col_index, value, cell_format)
        self.row_index += 1

    def finalize(self) -> None:
        """Safely close the workbook."""
        logger.info("Finalizing workbook: {}", self.output_file)
        try:
            self.workbook.close()
            logger.success("Successfully closed workbook")
        except Exception as e:
            logger.error("Failed to close workbook: {}", str(e))
            raise RuntimeError(f"Failed to close workbook: {str(e)}")

    def __enter__(self):
        """Context manager entry point."""
        logger.debug("Entering context manager")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point, ensure workbook is closed."""
        logger.debug("Exiting context manager")
        self.finalize()