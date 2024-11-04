import os
import json


class Config():
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
                "log_file": "app.log",
                "error_file": "errors.txt",
                "parser_delay": 3,
                "log_level": "INFO",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36 OPR/43.0.2442.991",
                "usd_regex": r'"USD","quoted":"UAH","bid":"([\d.]+)","ask"'
            }
            with open(self.CONFIG_PATH, 'w') as f:
                json.dump(default_config, f, indent=4)
            return default_config

    def get(self, key: str):
        return self._config_data.get(key)

# Приклад використання
if __name__ == "__main__":
    config = Config()
    print(config.get("input_file"))
    print(config.get("output_file"))
    print(config.get("currency_url"))
    print(config.get("log_file"))
    config2 = Config()
    config3 = Config()
    print(config.get("error_file"))
    print(config.get("parser_delay"))
    print(config.get("log_level"))
    print(config.get("user_agent"))
    print(config.get("usd_regex"))