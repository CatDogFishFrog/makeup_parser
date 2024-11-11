from dataclasses import dataclass
from typing import Any, Dict, List, Union, Optional
from functools import lru_cache
from utils.hex_tools import darken_color
import xlsxwriter
from parser import SaleParams, Product
from singletons.config import Config
from xlsx.xlsx_column_setting import XlsxColumnSetting
from singletons.logger import get_logger

logger = get_logger()

@dataclass
class CellData:
    value: Any
    format_dict: Dict[str, Any]
    is_hyperlink: bool = False
    url: Optional[str] = None

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
            'info': lambda p, v, r: ", ".join(
                info for info in (
                    getattr(p, 'info', None),
                    getattr(v, 'info', None)
                ) if info is not None
            ),
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
    def _get_cell_value(
            self,
            cell_type: str,
            product: Product,
            variant: Optional[Any],
            ref_price: Union[int, float]
    ) -> Any:
        """
        Get cell value with error handling and caching.

        Args:
            cell_type: Type of cell to generate value for
            product: Product object
            variant: Optional variant object
            ref_price: Reference price

        Returns:
            Cell value or None if handler not found or error occurs
        """
        try:
            handler = self._cell_type_mapping.get(cell_type.lower())
            if not handler:
                logger.warning(f"No handler found for cell type: {cell_type}")
                return None

            return handler(product, variant, ref_price)

        except AttributeError as e:
            logger.warning(
                "Failed to get cell value for type {}: {}",
                cell_type,
                str(e)
            )
            return None
        except Exception as e:
            logger.error(
                "Unexpected error getting cell value for type {}: {}",
                cell_type,
                str(e)
            )
            return None

    def _get_cell_format(
            self,
            setting: XlsxColumnSetting,
            sale_params: Optional[SaleParams] = None,
            is_striped: bool = False
    ) -> Dict[str, Any]:
        """
        Get cell format based on settings and parameters.

        Args:
            setting: Column setting object
            sale_params: Optional sale parameters
            is_striped: Whether to apply striped formatting

        Returns:
            Dictionary containing cell formatting
        """
        bg_color = (
            sale_params.price_background_color_hex
            if sale_params
            else setting.background_color_hex
        )

        if is_striped:
            bg_color = darken_color(bg_color)

        return {
            "bg_color": bg_color,
            "font_color": (
                sale_params.price_font_color_hex
                if sale_params
                else setting.font_color_hex
            ),
            "font_name": setting.font_name,
            "font_size": setting.font_size,
            "bold": setting.bold,
            "italic": setting.italic,
            "underline": setting.underline,
            "align": setting.align
        }

    def _prepare_cell_data(
            self,
            value: Any,
            setting: XlsxColumnSetting,
            sale_params: Optional[SaleParams],
            is_striped: bool
    ) -> CellData:
        """
        Prepare cell data including value and formatting.

        Args:
            value: Cell value
            setting: Column setting
            sale_params: Optional sale parameters
            is_striped: Whether to apply striped formatting

        Returns:
            CellData object containing cell information
        """
        format_dict = self._get_cell_format(setting, sale_params, is_striped)

        if setting.type.lower() == "name" and isinstance(value, tuple) and len(value) == 2:
            text, url = value
            return CellData(
                value=text,
                format_dict=format_dict,
                is_hyperlink=True,
                url=url
            )

        return CellData(
            value=value,
            format_dict=format_dict
        )

    def _write_cell(self, cell_data: CellData, row: int, col: int) -> None:
        """
        Write a single cell to the worksheet.

        Args:
            cell_data: CellData object containing cell information
            row: Row index
            col: Column index
        """
        cell_format = self.workbook.add_format(cell_data.format_dict)

        if cell_data.is_hyperlink:
            self.worksheet.write_url(
                row,
                col,
                cell_data.url,
                cell_format,
                string=cell_data.value
            )
        else:
            self.worksheet.write(row, col, cell_data.value, cell_format)

    def add_product(self, product: Product, ref_price: Union[int, float]) -> None:
        """
        Add product data to the worksheet.

        Args:
            product: Product object to add
            ref_price: Reference price

        Raises:
            RuntimeError: If there's an error adding the product
        """
        try:
            if not product.positions:
                self._add_product_without_variants(product, ref_price)
                return

            for variant in product.positions:
                self._add_product_variant(product, variant, ref_price)

        except Exception as e:
            error_msg = f"Failed to add product {product.name}: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def write_row(self, row_data: List[Any], sale_params: Optional[SaleParams] = None) -> None:
        """
        Write a complete row to the worksheet.

        Args:
            row_data: List of values to write
            sale_params: Optional sale parameters
        """
        is_striped = self.striped_zebra and self.row_index % 2 != 0

        for col_index, value in enumerate(row_data):
            setting = self.table_settings[col_index]
            cell_data = self._prepare_cell_data(
                value,
                setting,
                sale_params,
                is_striped
            )
            self._write_cell(cell_data, self.row_index, col_index)

        self.row_index += 1

    def _add_product_variant(
            self,
            product: Product,
            variant: Any,
            ref_price: Union[int, float]
    ) -> None:
        """Add a single product variant to the worksheet."""
        logger.debug("Processing variant: {}", variant.title)
        row_data = [
            self._get_cell_value(setting.type, product, variant, ref_price)
            for setting in self.table_settings
        ]
        self.write_row(row_data, getattr(variant, 'sale_params', None))

    def _add_product_without_variants(
            self,
            product: Product,
            ref_price: Union[int, float]
    ) -> None:
        """Add a product without variants to the worksheet."""
        row_data = [
            self._get_cell_value(setting.type, product, None, ref_price)
            for setting in self.table_settings
        ]
        self.write_row(row_data, None)

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