import requests
from bs4 import BeautifulSoup
from typing import Optional, List
from singletons.logger import get_logger
from singletons.config import Config
import re

# Load configuration and setup logger
config = Config()
logger = get_logger()

class Variant:
    """Represents a single variant of a product with title, EU status, and price."""
    def __init__(self, title: Optional[str], eu: bool, price: int):
        self.title = title
        self.eu = eu
        self.price = price

    def __str__(self) -> str:
        """String representation for logging and debugging."""
        eu_status = "EU" if self.eu else "UA"
        return f"Variant(title={self.title}, price={self.price}, region={eu_status})"

class Product:
    def __init__(
        self,
        name: str,
        brand: str,
        url: str,
        positions: List[Variant],
        info: Optional[str] = None,
        on_sale: Optional[bool] = None,
        has_error: Optional[bool] = False
    ):
        self.name = name
        self.brand = brand
        self.url = url
        self.positions = positions
        self.info = info
        self.on_sale = on_sale
        self.has_error = has_error

    def __str__(self) -> str:
        """String representation for logging and debugging."""
        sale_status = "On sale" if self.on_sale else "Regular"
        error_status = "Error encountered" if self.has_error else "No errors"
        return f"Product(name={self.name}, url={self.url}, sale_status={sale_status}, error_status={error_status})"

    @classmethod
    def from_url(cls, url: str) -> "Product":
        """Fetches and parses product data from the given URL."""
        logger.info(f"Fetching product data from URL: {url}")
        info_list: List[str] = []
        headers = {"User-Agent": config.get("user_agent")}

        try:
            response = cls._fetch_product_page(url, headers)
            soup = BeautifulSoup(response.text, 'html.parser')

            product_item = cls._get_product_item(soup, url)
            if not product_item:
                return cls._handle_missing_product(url, info_list)

            name = cls._parse_product_name(product_item, url)
            brand = cls._parse_brand(product_item, url)
            sale = cls._check_sale_status(product_item, info_list)
            positions = cls._parse_variants(product_item, url, info_list)


            prod_return = cls(name=name, brand=brand if brand else "Unrecognized", url=url, positions=positions, on_sale=sale,
                    info=", ".join(info_list) if info_list else None)
            logger.debug(f"Successfully parsed product: {prod_return}")
            return prod_return

        except requests.RequestException as e:
            return cls._handle_request_error(url, e, info_list)

        except Exception as e:
            return cls._handle_unexpected_error(url, e, info_list)

    @staticmethod
    def _fetch_product_page(url: str, headers: dict) -> requests.Response:
        """Fetches the product page content."""
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        logger.debug(f"Received response from {url}")
        return response

    @staticmethod
    def _get_product_item(soup: BeautifulSoup, url: str):
        """Finds the main product item container in the HTML soup."""
        product_item = soup.find('div', class_='product-item')
        if not product_item:
            logger.error(f"Product not found at {url}")
        return product_item

    @classmethod
    def _parse_brand(cls, product_item: BeautifulSoup, url: str) -> str:
        """Parses the product brand from the HTML content."""
        brand_tag = product_item.find("span", itemprop="name")
        if brand_tag:
            brand = brand_tag.text.strip()
        else:
            logger.warning(f"Brand not found for URL: {url}")
            brand = "Unrecognized Brand"
        return brand
    @classmethod
    def _parse_product_name(cls, product_item: BeautifulSoup, url: str) -> str:
        """Parses the product name from the HTML content."""
        name_tag = product_item.find("span", class_="product-item__name")
        if name_tag:
            name = name_tag.text.strip()
        else:
            logger.warning(f"Product name not found for URL: {url}")
            name = "Unnamed Product"
        return name

    @classmethod
    def _check_sale_status(cls, product_item, info_list: List[str]) -> bool:
        """Checks if the product is on sale and updates info_list with sale details."""
        sale = False
        sale_block = product_item.find("div", class_="product-item__message")
        if sale_block:
            sale_text_tag = sale_block.find('a', class_='product-item__attention')
            if sale_text_tag:
                sale_text = sale_text_tag.text.strip()
                if config.get("sale_text") in sale_text:
                    sale = True
                    info_list.append("1+1=3")
        return sale

    @classmethod
    def _parse_variant(cls, variant: BeautifulSoup, info_list: List[str], url: Optional[str]) -> Variant:
        title = variant.get("title")
        try:
            eu = variant.find("i", class_="eu rus") is not None
            price_str = variant.get("data-price")
            if price_str and price_str.isdigit():
                price = int(price_str)
                variant_obj = Variant(title=title, eu=eu, price=price)

                logger.debug(f"Parsed variant: {variant_obj}")
                return variant_obj
            else:
                logger.warning(f"Invalid or missing price for variant '{title if title else '???'}'{f" at {url}" if url else ""}")
                info_list.append(f"Invalid price for '{title if title else '???'}'")
        except Exception as e:
            logger.error(f"Error parsing variant '{title if title else '???'}': {e}")
            info_list.append(f"Error variant '{title if title else '???'}'")

    @classmethod
    def _parse_variants(cls, product_item, url: str, info_list: List[str]) -> List[Variant]:
        """Parses all available product variants and returns them as a list."""
        positions = []
        product_item__buy = product_item.find("div", class_="product-item__buy")
        if product_item__buy:
            variants = product_item__buy.find_all("div", class_="variant")
            for variant in variants:
                positions.append(cls._parse_variant(variant, info_list, url))

        return positions

    @classmethod
    def _handle_missing_product(cls, url: str, info_list: List[str]) -> "Product":
        """Handles the case where the product item is not found."""
        error_message = "Product not found"
        info_list.append(error_message)
        return cls(name="Unknown", brand="Unrecognized", url=url, positions=[], info=error_message, has_error=True)

    @classmethod
    def _handle_request_error(cls, url: str, exception: Exception, info_list: List[str]) -> "Product":
        """Handles request exceptions and logs an appropriate error."""
        error_message = f"Product does not exist! Error fetching product data from URL {url}: {exception}"
        info_list.append("Product does not exist!")
        logger.error(error_message)
        return cls(name="Unknown", brand="Unrecognized", url=url, positions=[], info=", ".join(info_list), has_error=True)

    @classmethod
    def _handle_unexpected_error(cls, url: str, exception: Exception, info_list: List[str]) -> "Product":
        """Handles any unexpected error during product parsing."""
        error_message = "Unexpected error while parsing product data"
        info_list.append("Unexpected error")
        logger.error(f"{error_message} from URL {url}: {exception}")
        return cls(name="Unknown", brand="Unrecognized", url=url, positions=[], info=", ".join(info_list), has_error=True)

def get_usd() -> float:
    """
    Fetches the current USD to UAH exchange rate.

    Returns:
        float: Current USD to UAH exchange rate

    Raises:
        ValueError: If exchange rate cannot be fetched or parsed
    """
    url = config.get("currency_url")
    headers = {"User-Agent": config.get("user_agent")}
    regex_pattern = config.get("usd_regex")

    try:
        logger.info(f"Fetching USD exchange rate from {url}")
        with requests.get(url, headers=headers, timeout=10) as response:
            response.raise_for_status()
            if match := re.search(regex_pattern, response.text):
                usd_rate = float(match.group(1))
                logger.info(f"Fetched USD rate: {usd_rate}")
                return usd_rate

        raise ValueError("USD exchange rate not found in response")

    except (requests.RequestException, ValueError) as e:
        error_message = f"Error fetching exchange rate from {url}: {e}"
        logger.error(error_message)
        raise ValueError(error_message) from e

if __name__ == "__main__":
    product = Product.from_url("https://makeup.com.ua/ua/product/891656/")
    product2 = Product.from_url("https://makeup.com.ua/ua/product/12359/")
    print(product)
    for position in product.positions:
        print(position)
    print(get_usd())
