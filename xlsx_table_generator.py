import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Union, Optional
from functools import lru_cache
import xlsxwriter
from singletons.config import Config


@dataclass
class XlsxColumnSetting:
    """Class for storing Excel column settings with validation."""
    type: str
    width: int = field(default=15)
    header: str = field(default="Something")
    background_color: str = field(default="#FFFFFF")
    font_color: str = field(default="#000000")
    bold: bool = field(default=False)
    italic: bool = field(default=False)
    underline: bool = field(default=False)
    font_name: str = field(default="Arial")
    font_size: int = field(default=10)
    align: str = field(default="left")

    # Class-level constants
    VALID_ALIGNMENTS = {"left", "center", "right", "justify"}
    DEFAULT_SETTINGS = {
        "type": "Variant",
        "width": 30,
        "header": "Something",
        "background_color": "#FFFFFF",
        "font_color": "#000000",
        "bold": False,
        "italic": False,
        "underline": False,
        "font_name": "Arial",
        "font_size": 10,
        "align": "left"
    }

    def __post_init__(self):
        """Validate settings after initialization."""
        self._validate_colors()
        self._validate_align()
        self._validate_numeric_fields()

    def _validate_colors(self):
        """Validate color hex codes."""
        for color_attr in ('background_color', 'font_color'):
            color = getattr(self, color_attr)
            if not self.is_hex_color(color):
                setattr(self, color_attr, self.DEFAULT_SETTINGS[color_attr])

    def _validate_align(self):
        """Validate alignment value."""
        if self.align not in self.VALID_ALIGNMENTS:
            self.align = self.DEFAULT_SETTINGS["align"]

    def _validate_numeric_fields(self):
        """Validate numeric fields."""
        if not isinstance(self.width, int) or self.width <= 0:
            self.width = self.DEFAULT_SETTINGS["width"]
        if not isinstance(self.font_size, int) or self.font_size <= 0:
            self.font_size = self.DEFAULT_SETTINGS["font_size"]

    @staticmethod
    @lru_cache(maxsize=128)
    def is_hex_color(color: str) -> bool:
        """
        Check if the color is a valid hex color.

        Args:
            color: Color string to validate

        Returns:
            bool: True if valid hex color, False otherwise
        """
        if not isinstance(color, str):
            return False

        hex_pattern = re.compile(r'^#[0-9A-Fa-f]{6}$')
        return bool(hex_pattern.match(color))

    @classmethod
    def from_dict(cls, settings: Dict[str, Any]) -> 'XlsxColumnSetting':
        """
        Create XlsxColumnSetting from dictionary.

        Args:
            settings: Dictionary containing column settings

        Returns:
            XlsxColumnSetting: New instance with applied settings
        """

        # Process type field first (required)
        processed_settings = {
            'type': settings.get('type') if settings.get('type') is not None else cls.DEFAULT_SETTINGS['type']}

        # Process header specially
        processed_settings['header'] = (
                settings.get('header') if settings.get('header') is not None else
                processed_settings['type'] or
                cls.DEFAULT_SETTINGS['header']
        )

        # Process all other fields
        for field_name, default_value in cls.DEFAULT_SETTINGS.items():
            if field_name not in ('type', 'header'):
                processed_settings[field_name] = settings.get(field_name) if settings.get(field_name) is not None else default_value

        return cls(**processed_settings)

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
        self.config = config
        self.workbook = xlsxwriter.Workbook(self.config.get("output_file", "output.xlsx"))
        self.worksheet = self.workbook.add_worksheet()
        self.row_index = 1
        self.table_settings = self._load_table_settings()
        self._cell_type_mapping = self._init_cell_type_mapping()
        self._set_headers()
        for col_index, setting in enumerate(self.table_settings):
            self.worksheet.set_column(col_index, col_index, setting.width)


    @staticmethod
    def _init_cell_type_mapping() -> Dict[str, callable]:
        """Initialize cell type mapping."""
        return {
            'brand': lambda p, v, r: p.brand,
            'name': lambda p, v, r: p.name,
            'url': lambda p, v, r: p.url,
            'error': lambda p, v, r: "ERROR" if p.has_error else "",
            'rprice': lambda p, v, r: r,
            'mprice': lambda p, v, r: v.price,
            'variant': lambda p, v, r: v.title,
            'info': lambda p, v, r: f"{p.info}, {v.info}",
            'region': lambda p, v, r: "EU" if v.eu else "UA",
            'saleformula': lambda p, v, r: v.sale_params.price_formula if v.sale_params else None
        }

    def _load_table_settings(self) -> List[XlsxColumnSetting]:
        """Load table settings from configuration."""
        settings = self.config.get("xlsx_table_settings", {})
        return [
            XlsxColumnSetting.from_dict(column)
            for key, column in settings.items()
            if not key.startswith("_")
        ]

    def _set_headers(self) -> None:
        """Set table headers with formatting."""
        header_format = self.workbook.add_format(self.HEADER_FORMAT)
        for col_index, setting in enumerate(self.table_settings):
            self.worksheet.write(0, col_index, setting.header, header_format)

    @lru_cache(maxsize=128)
    def _get_cell_value(self, cell_type: str, product: Any, variant: Any, ref_price: Any) -> Union[str, int, None]:
        """Get cell value based on cell type and provided data."""
        handler = self._cell_type_mapping.get(cell_type.lower())
        return handler(product, variant, ref_price) if handler else None

    @staticmethod
    def _get_cell_format(setting: XlsxColumnSetting, sale_params: Any = None) -> Dict[str, Any]:
        """Get cell format based on settings and sale parameters."""
        return {
            "bg_color": sale_params.price_background_color_hex if sale_params else setting.background_color,
            "font_color": sale_params.price_font_color_hex if sale_params else setting.font_color,
            "font_name": setting.font_name,
            "font_size": setting.font_size,
            "bold": setting.bold,
            "italic": setting.italic,
            "underline": setting.underline,
            "align": setting.align
        }

    def add_product(self, product: Any, ref_price: Union[int, float]) -> None:
        """Add product data to the worksheet."""
        for variant in product.positions:
            row_data = [
                self._get_cell_value(setting.type, product, variant, ref_price)
                for setting in self.table_settings
            ]
            self._write_row(row_data, variant.sale_params)

    def _write_row(self, row: List[Any], sale_params: Any = None) -> None:
        """Write a row of data to the worksheet with formatting."""
        for col_index, value in enumerate(row):
            cell_format = self.workbook.add_format(
                self._get_cell_format(self.table_settings[col_index], sale_params)
            )
            self.worksheet.write(self.row_index, col_index, value, cell_format)
        self.row_index += 1

    def finalize(self) -> None:
        """Finalize and close the workbook."""
        self.workbook.close()