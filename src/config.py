from pydantic import BaseModel, HttpUrl
from typing import Optional
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    INPUT_FILE: Path = Path("input_table.csv")
    OUTPUT_FILE: Path = Path("out_table.xlsx")
    ERROR_LOG: Path = Path("errors.log")
    CURRENCY_URL: HttpUrl = "https://obmennovosti.info/city.php?city=45"
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36"
    REQUEST_DELAY: float = 3.0
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

settings = Settings()