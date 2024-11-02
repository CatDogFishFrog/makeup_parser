from bs4 import BeautifulSoup
import requests
from loguru import logger
from typing import Optional
from .models import Product, ProductVariant
from .config import settings
import time


class MakeupParser:
    def __init__(self):
        self.headers = {"User-Agent": settings.USER_AGENT}

    def get_usd_rate(self) -> float:
        """Отримує поточний курс USD."""
        try:
            response = requests.get(settings.CURRENCY_URL, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            data = soup.find_all("script")
            index_start = str(data[-1]).find('"USD","quoted":"UAH","bid":') + 44
            index_end = index_start + 7
            return float(str(data[-1])[index_start:index_end])
        except Exception as e:
            logger.error(f"Помилка отримання курсу валют: {e}")
            raise

    def parse_product(self, url: str) -> Optional[Product]:
        """Парсить інформацію про продукт з makeup.com.ua."""
        try:
            time.sleep(settings.REQUEST_DELAY)
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            product_name = soup.find("span", class_="product-item__name").text

            variants = []
            product_buy = soup.find("div", class_="product-item__buy")
            variant_elements = product_buy.find_all("div", class_="variant")

            for element in variant_elements:
                variant = ProductVariant(
                    title=element.get("title"),
                    price=int(element.get("data-price")),
                    eu_stock=element.find("i", class_="eu rus") is not None
                )
                variants.append(variant)

            return Product(name=product_name, url=url, variants=variants)

        except Exception as e:
            logger.error(f"Помилка парсингу продукту {url}: {e}")
            return None