import requests
from bs4 import BeautifulSoup
from typing import Optional, List
from singletons.logger import get_logger
from singletons.config import Config
import re

from utils.hex_tools import normalize_hex_color

# Load configuration and setup logger
config = Config()
logger = get_logger()

class SaleParams:
    """Represents parameters for a sale condition."""
    def __init__(self, text_for_search: str, apply_to: dict[str, bool], price_formula: str, info_text: Optional[str] = None, price_background_color_hex:Optional[str] = None, price_font_color_hex:Optional[str] = None ):
        self.text_for_search:str = text_for_search
        self.apply_to: dict[str, bool] = apply_to
        self.price_formula: str = price_formula
        self.info_text: Optional[str] = info_text
        self.price_background_color_hex = normalize_hex_color(price_background_color_hex)
        self.price_font_color_hex = normalize_hex_color(price_font_color_hex)

    @classmethod
    def from_dict(cls, data: dict) -> "SaleParams":
        """Creates a SaleParams instance from a dictionary."""
        return cls(
            text_for_search=data["text_for_search"],
            apply_to=data["apply_to"],
            price_formula=data["price_formula"],
            info_text=data.get("info_text"),
            price_background_color_hex=data.get("price_background_color_hex"),
            price_font_color_hex=data.get("price_font_color_hex")
        )

    def __str__(self) -> str:
        """String representation for logging and debugging."""
        return f"SaleParams(text_for_search={self.text_for_search}, apply_to={self.apply_to}, price_formula={self.price_formula}, info_text={self.info_text}, price_background_color_hex={self.price_background_color_hex}, price_font_color_hex={self.price_font_color_hex})"

class Variant:
    """Represents a single variant of a product with title, EU status, and price."""
    def __init__(self, title: Optional[str], eu: bool, price: int, sale_params: Optional[SaleParams] = None, info: Optional[str] = None):
        self.title = title
        self.eu = eu
        self.price = price
        self.sale_params = sale_params
        self.info = info

    def __str__(self) -> str:
        """String representation for logging and debugging."""
        eu_status = "EU" if self.eu else "UA"
        return f"Variant(title={self.title}, eu={eu_status}, price={self.price}, sale_params={self.sale_params}, info={self.info})"

class Product:
    def __init__(
        self,
        name: str,
        brand: str,
        url: str,
        positions: List[Variant],
        info: Optional[str] = None,
        sale_params: Optional[SaleParams] = None,
        has_error: Optional[bool] = False,
        ref_price: Optional[int] = None
    ):
        self.name = name
        self.brand = brand
        self.url = url
        self.positions = positions
        self.info = info
        self.sale_params = sale_params
        self.has_error = has_error
        self.ref_price = ref_price

    def __str__(self) -> str:
        """String representation for logging and debugging."""
        sale_status = "On sale" if self.sale_params else "Regular"
        error_status = "Error encountered" if self.has_error else "No errors"
        return f"Product(brand={self.brand}, name={self.name}, url={self.url}, sale_status={sale_status}, error_status={error_status})"

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
            sale_params = cls._check_sale_status(product_item)
            positions = cls._parse_variants(product_item, url, sale_params)


            prod_return = cls(name=name, brand=brand if brand else "Unrecognized", url=url, positions=positions, sale_params=sale_params if sale_params  else None,
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
    def _check_sale_status(cls, product_item) -> SaleParams | None:
        """Checks if the product is on sale and updates info_list with sale details."""
        sale = None
        if sale_block := product_item.find("div", class_="product-item__message"):
            if sale_text_tag := sale_block.find('a', class_='product-item__attention'):
                sale_text = sale_text_tag.text.strip()
                for sale_item in config.get("sale_list", []):
                    if sale_item["text_for_search"] in sale_text:
                        sale = SaleParams.from_dict(sale_item)
                        logger.debug(f"Sale detected: {sale_item['info_text']}")
                        break
        return sale

    @classmethod
    def _extract_price(cls, variant: BeautifulSoup, title: Optional[str], url: Optional[str]) -> Optional[int]:
        """Extract and validate the price from the variant element."""
        price_str = variant.get("data-price")
        if not price_str or not price_str.isdigit():
            logger.warning(f"Invalid/missing price for variant '{title or '???'}'{f' at {url}' if url else ''}")
            return None
        return int(price_str)

    @classmethod
    def _calculate_final_price(cls, base_price: int, eu: bool, sale_params: Optional[SaleParams]) -> (int, str):
        """Calculate the final price using the sale formula if available."""
        price = base_price
        variant_info = ''

        if sale_params:
            if (eu and sale_params.apply_to["eu"]) or (not eu and sale_params.apply_to["ua"]):
                try:
                    x = base_price  # x is used in eval formula
                    price = eval(sale_params.price_formula)
                    variant_info = sale_params.info_text or ''
                    logger.debug(f"Applied sale formula: {sale_params.price_formula}")
                except Exception as e:
                    logger.error(f"Error applying sale formula '{sale_params.price_formula}': {e}")
                    variant_info = f"{sale_params.info_text + ', but ' if sale_params.info_text else ''}Error applying sale formula '{sale_params.price_formula}'"
                    price = base_price

        return price, variant_info

    @classmethod
    def _create_variant_object(cls, title: Optional[str], eu: bool, sale_params: Optional[SaleParams], final_price: int, info: str) -> Variant:
        """Create a Variant object from parsed details."""
        variant_obj = Variant(title=title, eu=eu, sale_params=sale_params, price=final_price, info=info)
        logger.debug(f"Parsed variant: {variant_obj}")
        return variant_obj

    @classmethod
    def _parse_variant(cls, variant: BeautifulSoup, url: Optional[str], sale_params: Optional[SaleParams]) -> Optional[Variant]:
        """Parse a single variant from BeautifulSoup element into a Variant object."""
        title = variant.get("title")

        try:
            # Check if variant has EU status
            eu = bool(variant.find("i", class_="eu rus"))

            # Extract and validate price
            base_price = cls._extract_price(variant, title, url)
            if base_price is None:
                return None

            # Calculate the final price considering any sale
            final_price, variant_info = cls._calculate_final_price(base_price, eu, sale_params)

            # Create and return the Variant object
            return cls._create_variant_object(title=title, eu=eu, sale_params=sale_params if final_price != base_price else None,
                                              final_price=final_price, info=variant_info)

        except Exception as e:
            logger.error(f"Error parsing variant '{title or '???'}' from {url if url else 'unknown source'}: {e}")
            return None

    @classmethod
    def _parse_variants(cls, product_item, url: str, sale_params: Optional[SaleParams] ) -> List[Variant]:
        """Parses all available product variants and returns them as a list."""
        positions = []
        product_item__buy = product_item.find("div", class_="product-item__buy")
        if product_item__buy:
            variants = product_item__buy.find_all("div", class_="variant")
            for variant in variants:
                positions.append(cls._parse_variant(variant, url, sale_params))

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
        error_message = f"Request error! Error fetching product data from URL {url}: {exception}"
        info_list.append("Request error!")
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
    url = config.get("usd_url")
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