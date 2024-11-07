import os
import json
from typing import Any, Dict


class Config:
    CONFIG_PATH = 'config.json'
    DEFAULT_CONFIG = {
        "input_file": "input_table.csv",
        "output_file": "out_table.xlsx",
        "currency_url": "https://obmennovosti.info/city.php?city=45",
        "usd_regex": r'"USD","quoted":"UAH","bid":"[\d.]+","ask":"([\d.]+)"',
        "sale_text": "Товар з найменшою вартістю у подарунок",
        "log_file": "app.log",
        "log_level": "WARNING",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36 OPR/43.0.2442.991",
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
            with open(cls.CONFIG_PATH, 'r', encoding='utf-8') as f:
                existing_config = json.load(f)

            updated_config = {**cls.DEFAULT_CONFIG, **existing_config}

            if updated_config != existing_config:
                cls._save_config(updated_config)

            return updated_config

        cls._save_config(cls.DEFAULT_CONFIG)
        return cls.DEFAULT_CONFIG

    @classmethod
    def _save_config(cls, config: Dict[str, Any]) -> None:
        with open(cls.CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)

    def get(self, key: str, default: Any = None) -> Any:
        return self._config_data.get(key, default)