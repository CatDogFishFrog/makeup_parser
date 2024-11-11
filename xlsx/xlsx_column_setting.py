from dataclasses import field, dataclass
from typing import Optional, Dict, Any

from singletons.logger import get_logger
from utils.hex_tools import is_hex_color

logger = get_logger()


@dataclass
class XlsxColumnSetting:
    """Class for storing Excel column settings with validation."""
    type: Optional[str] = field(default=None)
    width: int = field(default=15)
    header: str = field(default="Something")
    background_color_hex: str = field(default="#FFFFFF")
    font_color_hex: str = field(default="#000000")
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
        "background_color_hex": "#FFFFFF",
        "font_color_hex": "#000000",
        "bold": False,
        "italic": False,
        "underline": False,
        "font_name": "Arial",
        "font_size": 10,
        "align": "left"
    }

    def __post_init__(self):
        """Validate settings after initialization."""
        try:
            self._validate_colors()
            self._validate_align()
            self._validate_numeric_fields()
        except Exception as e:
            logger.error(f"Error validating settings: {str(e)}")
            raise

    def _validate_colors(self):
        """Validate color hex codes."""
        for color_attr in ('background_color_hex', 'font_color_hex'):
            color = getattr(self, color_attr)
            if not is_hex_color(color):
                logger.warning(f"Invalid {color_attr} value: {color}. Using default value.")
                setattr(self, color_attr, self.DEFAULT_SETTINGS[color_attr])

    def _validate_align(self):
        """Validate alignment value."""
        if self.align not in self.VALID_ALIGNMENTS:
            logger.warning(f"Invalid alignment value: {self.align}. Using default value.")
            self.align = self.DEFAULT_SETTINGS["align"]

    def _validate_numeric_fields(self):
        """Validate numeric fields."""
        if not isinstance(self.width, int) or self.width <= 0:
            logger.warning(f"Invalid width value: {self.width}. Using default value.")
            self.width = self.DEFAULT_SETTINGS["width"]
        if not isinstance(self.font_size, int) or self.font_size <= 0:
            logger.warning(f"Invalid font size value: {self.font_size}. Using default value.")
            self.font_size = self.DEFAULT_SETTINGS["font_size"]

    def __str__(self):
        return f"XlsxColumnSetting(type={self.type}, width={self.width}, header={self.header}, " \
               f"background_color={self.background_color_hex}, font_color={self.font_color_hex}, " \
               f"bold={self.bold}, italic={self.italic}, underline={self.underline}, " \
               f"font_name={self.font_name}, font_size={self.font_size}, align={self.align})"

    @classmethod
    def from_dict(cls, settings: Dict[str, Any]) -> 'XlsxColumnSetting':
        """
        Create XlsxColumnSetting from dictionary.

        Args:
            settings: Dictionary containing column settings

        Returns:
            XlsxColumnSetting: New instance with applied settings

        Raises:
            ValueError: If settings dictionary is invalid
        """
        try:
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

            logger.debug(f"Creating XlsxColumnSetting with settings: {processed_settings}")
            return cls(**processed_settings)
        except Exception as e:
            logger.error(f"Error creating XlsxColumnSetting from dictionary: {str(e)}")
            raise ValueError(f"Invalid settings dictionary: {str(e)}")