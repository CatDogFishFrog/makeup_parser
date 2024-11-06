import os
import json


class Config:
    CONFIG_PATH = 'config.json'

    _instance = None

    def __new__(cls):
        if cls._instance is None: cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self._config_data = self._load_config()

    def _load_config(self):
        if os.path.exists(self.CONFIG_PATH):
            with open(self.CONFIG_PATH, 'r') as f:
                return json.load(f)
        else:
            default_config = {
                "input_file": "input_table.csv",
                "output_file": "out_table.xlsx",
                "currency_url": "https://obmennovosti.info/city.php?city=45",
                "usd_regex": r'"USD","quoted":"UAH","bid":"([\d.]+)","ask"',
                "sale_text": "Товар з найменшою вартістю у подарунок",
                "log_file": "app.log",
                "log_level": "WARNING",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36 OPR/43.0.2442.991",
            }
            with open(self.CONFIG_PATH, 'w') as f:
                json.dump(default_config, f, indent=4)
            return default_config

    def get(self, key: str):
        return self._config_data.get(key)