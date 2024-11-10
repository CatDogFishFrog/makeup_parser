import os
import json
from typing import Any, Dict
from singletons.console import ConsoleSingleton

console_singleton = ConsoleSingleton()

class Config:
    CONFIG_PATH = 'config.json'
    DEFAULT_CONFIG = {
        "input_file": "input_table.csv",
        "output_file": "out_table.xlsx",
        "usd_url": "https://obmennovosti.info/city.php?city=45",
        "usd_regex": r'"USD","quoted":"UAH","bid":"[\d.]+","ask":"([\d.]+)"',
        "usd_regex_comment": "https://inweb.ua/blog/ua/regulyarnye-vyrazheniya/",
        "log_file": "app.log",
        "log_level": "WARNING",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36 OPR/43.0.2442.991",
        "sale_list": [
            {
                "_comment": "This is a comment. Not used in program",
                "apply_to": {
                    "ua": True,
                    "eu": False
                },
                "text_for_search": "Товар з найменшою вартістю у подарунок",
                "price_formula": "x*2/3",
                "info_text": "1+1=3",
                "price_background_color_hex":  "#45F200",
                "price_font_color_hex":  None
            },
            {
                "_comment": "Use X as base price value",
                "text_for_search": "Олівець для повік та лак для нігтів у подарунок, за умови придбання продукції Bourjois на суму від 680 грн",
                "apply_to": {
                    "ua": True,
                    "eu": False
                },
                "price_formula": "x-100 if x>680 else x",
                "info_text": "Подарунок олівець",
                "price_background_color_hex": "#45F200",
                "price_font_color_hex": None
            }
        ],
        "xlsx_table_settings": {
            "_comment": 'Types: "Brand", "Name" - Product Name, "Variant" - Variant name, "RPrice" - Reference price from input table, "MPrice" - Price from Makeup website (with sale price recalculating), "Region" - EU or UA, "Info" - info text with same information (sale, error)',
            "column_1": {"type": "Brand", "width": 30, "header": "Brand", "background_color_hex": None,
                         "font_color_hex": None, "bold": True, "italic": False, "underline": False, "font_name": None,
                         "font_size": None, "align": None},
            "column_2": {"type": "Name", "width": 30, "header": "Product Name", "background_color_hex": None,
                         "font_color_hex": None, "bold": True, "italic": False, "underline": False, "font_name": None,
                         "font_size": None, "align": None},
            "column_3": {"type": "Variant", "width": 30, "header": "Variant", "background_color_hex": None,
                         "font_color_hex": None, "bold": True, "italic": False, "underline": False, "font_name": None,
                         "font_size": None, "align": None},
            "column_4": {"type": "RPrice", "width": 30, "header": "Reference price", "background_color_hex": None,
                         "font_color_hex": None, "bold": True, "italic": False, "underline": False, "font_name": None,
                         "font_size": None, "align": None},
            "column_5": {"type": "MPrice", "width": 30, "header": "Makeup Price", "background_color_hex": None,
                         "font_color_hex": None, "bold": True, "italic": False, "underline": False, "font_name": None,
                         "font_size": None, "align": None},
            "column_6": {"type": "Region", "width": 30, "header": "Region", "background_color_hex": None,
                         "font_color_hex": None, "bold": True, "italic": False, "underline": False, "font_name": None,
                         "font_size": None, "align": None},
            "column_7": {"type": "Info", "width": 30, "header": "Info", "background_color_hex": None,
                         "font_color_hex": None, "bold": True, "italic": False, "underline": False, "font_name": None,
                         "font_size": None, "align": None},
        }
    }

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._config_data = cls._instance._load_config()
        return cls._instance

    @classmethod
    def _load_config(cls) -> Dict[str, Any]:
        if os.path.exists(cls.CONFIG_PATH):
            try:
                with open(cls.CONFIG_PATH, 'r', encoding='utf-8') as f:
                    existing_config = json.load(f)
            except Exception as e:
                console_singleton.error(f"Error loading configuration. Invalid configuration file. Please check the file format.\n\n{e}")
                raise ValueError("Invalid configuration file. Please check the file format.") from e

            updated_config = {**cls.DEFAULT_CONFIG, **existing_config}

            if updated_config != existing_config:
                cls._save_config(updated_config)

            return updated_config

        cls._save_config(cls.DEFAULT_CONFIG)
        return cls.DEFAULT_CONFIG

    @classmethod
    def _save_config(cls, config_: Dict[str, Any]) -> None:
        try:
            with open(cls.CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(config_, f, ensure_ascii=False, indent=4) # type: ignore
            console_singleton.info(f"Configuration saved to {cls.CONFIG_PATH}")
        except Exception as e:
            console_singleton.error(f"Error saving configuration: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self._config_data.get(key, default)


if __name__ == "__main__":
    config = Config()
    print(config.get('input_file'))
    print(config.get('nonexistent_key', 'Default Value'))