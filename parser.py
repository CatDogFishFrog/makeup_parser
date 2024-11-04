import requests
from bs4 import BeautifulSoup
from typing import Optional, List, Dict
from singletons.logger import get_logger
from singletons.config import Config
import re

# Load configuration and setup logger
config = Config()
logger = get_logger()

class Product:
    def __init__(
        self,
        name: str,
        url: str,
        positions: List[Dict],
        info: Optional[str] = None,
        on_sale: Optional[bool] = None,
        has_error: Optional[bool] = False
    ):
        self.name = name
        self.url = url
        self.positions = positions
        self.info = info
        self.on_sale = on_sale
        self.has_error = has_error

    @classmethod
    def from_url(cls, url: str) -> "Product":
        """Fetches and parses product data from the given URL."""
        logger.info(f"Fetching product data from URL: {url}")
        info_list: List[str] = []
        headers = {"User-Agent": config.get("user_agent")}
        name = None
        positions = []
        sale = False

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            logger.debug(f"Received response from {url}")
            soup = BeautifulSoup(response.text, "lxml")

            product_item = soup.find('div', class_='product-item')
            if not product_item:
                error_message = "Product not found"
                logger.error(f"{error_message} at {url}")
                return cls(name="Unknown", url=url, positions=[], info=error_message, has_error=True)

            # Parse product name
            name_tag = product_item.find("span", class_="product-item__name")
            if name_tag:
                name = name_tag.text.strip()
            else:
                logger.warning(f"Product name not found for URL: {url}")
                name = "Unnamed Product"

            # Check if product is on sale
            sale_block = product_item.find("div", class_="product-item__message")
            if sale_block:
                sale_text_tag = sale_block.find('a', class_='product-item__attention')
                if sale_text_tag:
                    sale_text = sale_text_tag.text.strip()
                    if "Товар з найменшою вартістю у подарунок" in sale_text:
                        sale = True
                        info_list.append("1+1=3")

            # Parse product variants
            product_item__buy = product_item.find("div", class_="product-item__buy")
            if product_item__buy:
                variants = product_item__buy.find_all("div", class_="variant")
                for variant in variants:
                    title = variant.get("title")
                    try:
                        eu = variant.find("i", class_="eu rus") is not None
                        price_str = variant.get("data-price")
                        if price_str and price_str.isdigit():
                            price = int(price_str)
                            positions.append({"title": title, "eu": eu, "price": price})
                        else:
                            logger.warning(f"Invalid or missing price for variant '{title if title else '???'}' at {url}")
                            info_list.append(f"Invalid price for '{title if title else '???'}'")
                    except Exception as e:
                        logger.error(f"Error parsing variant '{title if title else '???'}': {e}")
                        info_list.append(f"Error variant '{title if title else '???'}'")

            logger.info(f"Product '{name}' fetched successfully with {len(positions)} variants.")
            return cls(name=name, url=url, positions=positions, on_sale=sale, info=", ".join(info_list) if info_list else None)

        except requests.RequestException as e:
            error_message = f"Product not exist! Error fetching product data from URL {url}: {e}"
            info_list.append("Product not exist!")
            logger.error(error_message)
            return cls(name=name if name else "Unknown", url=url, positions=positions, info=", ".join(info_list) if info_list else None, has_error=True)

        except Exception as e:
            error_message = "Unexpected error while parsing product data"
            info_list.append("Unexpected error")
            logger.error(f"{error_message} from URL {url}: {e}")
            return cls(name=name if name else "Unknown", url=url, positions=positions, info=", ".join(info_list) if info_list else None, has_error=True)

def get_usd() -> float:
    """Fetches the current USD to UAH exchange rate."""
    url = config.get("currency_url")
    headers = {"User-Agent": config.get("user_agent")}
    regex_pattern = config.get("usd_regex")

    try:
        logger.info(f"Fetching USD exchange rate from {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        page_content = response.text

        match = re.search(regex_pattern, page_content)
        if match:
            usd_rate = float(match.group(1))
            logger.info(f"Fetched USD rate: {usd_rate}")
            return usd_rate
        else:
            error_message = "USD exchange rate not found in response."
            logger.error(error_message)
            raise ValueError(error_message)

    except requests.RequestException as e:
        error_message = f"Error fetching exchange rate from {url}: {e}"
        logger.error(error_message)
        raise ValueError(error_message)

if __name__ == "__main__":
    product = Product.from_url("https://makeup.com.ua/ua/product/891656/")
    print(product)
    print(get_usd())
