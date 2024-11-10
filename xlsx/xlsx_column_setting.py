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
            if not is_hex_color(color):
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