import re
from functools import lru_cache
from typing import Tuple, Optional

# Common color names mapping to hex values
COLOR_NAMES = {
    'aliceblue': '#f0f8ff', 'antiquewhite': '#faebd7', 'aqua': '#00ffff', 'aquamarine': '#7fffd4',
    'azure': '#f0ffff', 'beige': '#f5f5dc', 'bisque': '#ffe4c4', 'black': '#000000',
    'blanchedalmond': '#ffebcd', 'blue': '#0000ff', 'blueviolet': '#8a2be2', 'brown': '#a52a2a',
    'burlywood': '#deb887', 'cadetblue': '#5f9ea0', 'chartreuse': '#7fff00', 'chocolate': '#d2691e',
    'coral': '#ff7f50', 'cornflowerblue': '#6495ed', 'cornsilk': '#fff8dc', 'crimson': '#dc143c',
    'cyan': '#00ffff', 'darkblue': '#00008b', 'darkcyan': '#008b8b', 'darkgoldenrod': '#b8860b',
    'darkgray': '#a9a9a9', 'darkgreen': '#006400', 'darkkhaki': '#bdb76b', 'darkmagenta': '#8b008b',
    'darkolivegreen': '#556b2f', 'darkorange': '#ff8c00', 'darkorchid': '#9932cc', 'darkred': '#8b0000',
    'darksalmon': '#e9967a', 'darkseagreen': '#8fbc8f', 'darkslateblue': '#483d8b', 'darkslategray': '#2f4f4f',
    'darkturquoise': '#00ced1', 'darkviolet': '#9400d3', 'deeppink': '#ff1493', 'deepskyblue': '#00bfff',
    'dimgray': '#696969', 'dodgerblue': '#1e90ff', 'firebrick': '#b22222', 'floralwhite': '#fffaf0',
    'forestgreen': '#228b22', 'fuchsia': '#ff00ff', 'gainsboro': '#dcdcdc', 'ghostwhite': '#f8f8ff',
    'gold': '#ffd700', 'goldenrod': '#daa520', 'gray': '#808080', 'green': '#008000',
    'greenyellow': '#adff2f', 'honeydew': '#f0fff0', 'hotpink': '#ff69b4', 'indianred': '#cd5c5c',
    'indigo': '#4b0082', 'ivory': '#fffff0', 'khaki': '#f0e68c', 'lavender': '#e6e6fa',
    'lavenderblush': '#fff0f5', 'lawngreen': '#7cfc00', 'lemonchiffon': '#fffacd', 'lightblue': '#add8e6'
}

class ColorError(Exception):
    """Custom exception for color-related errors."""
    pass

@lru_cache(maxsize=512)
def normalize_hex_color(color: str) -> Optional[str]:
    """
    Attempt to normalize and correct a hex color string.

    Args:
        color (str): Input color string to normalize

    Returns:
        str: Normalized hex color string or None if correction is impossible

    Examples:
        'fff' -> '#FFFFFF'
        'abc' -> '#AABBCC'
        '#1234' -> None
        'rgb(255,255,255)' -> '#FFFFFF'
        'rgba(255,255,255,1)' -> '#FFFFFF'
        'hsl(0,100%,50%)' -> '#FF0000'
        'red' -> '#FF0000'
    """
    if not isinstance(color, str):
        return None

    # Strip whitespace and make lowercase
    color = color.strip().lower()

    # Try different normalization methods in order
    normalized = (
        _normalize_color_name(color) or
        _normalize_rgb_color(color) or
        _normalize_hsl_color(color) or
        _normalize_hex_color(color)
    )

    return normalized

@lru_cache(maxsize=256)
def _normalize_color_name(color: str) -> Optional[str]:
    """Normalize color name to hex."""
    return COLOR_NAMES.get(color)

@lru_cache(maxsize=256)
def _normalize_rgb_color(color: str) -> Optional[str]:
    """Normalize RGB/RGBA format to hex."""
    # Remove all whitespace
    color = re.sub(r'\s+', '', color)

    rgb_patterns = [
        r'rgb\((\d{1,3}),(\d{1,3}),(\d{1,3})\)',
        r'rgba\((\d{1,3}),(\d{1,3}),(\d{1,3}),[\d.]+\)',
        r'^(\d{1,3}),(\d{1,3}),(\d{1,3})$'
    ]

    for pattern in rgb_patterns:
        rgb_match = re.match(pattern, color)
        if rgb_match:
            try:
                rgb = [min(255, max(0, int(x))) for x in rgb_match.groups()]
                return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
            except ValueError:
                continue

    return None

@lru_cache(maxsize=256)
def _normalize_hsl_color(color: str) -> Optional[str]:
    """
    Normalize HSL format to hex color.

    Accepts HSL colors in formats:
    - hsl(360, 100%, 100%)
    - hsl(360,100%,100%)
    - hsl(360, 100, 100)
    - hsl(360,100,100)

    Args:
        color (str): HSL color string

    Returns:
        Optional[str]: Normalized hex color or None if invalid

    Examples:
        >>> _normalize_hsl_color('hsl(0,100%,50%)')
        '#ff0000'
        >>> _normalize_hsl_color('hsl(120, 100%, 50%)')
        '#00ff00'
    """
    if not isinstance(color, str):
        return None

    # Remove all whitespace and make lowercase
    color = re.sub(r'\s+', '', color.lower())

    # More flexible pattern matching
    hsl_pattern = r'hsl\((\d+\.?\d*),(\d+\.?\d*)%?,(\d+\.?\d*)%?\)'
    hsl_match = re.match(hsl_pattern, color)

    if not hsl_match:
        return None

    try:
        # Convert values to float, handling percentage signs
        h, s, l = [float(x.rstrip('%')) for x in hsl_match.groups()]

        # Normalize values to proper ranges
        h = h % 360  # Wrap hue to 0-360
        h /= 360  # Convert to 0-1
        s = min(100, max(0, s)) / 100  # Convert to 0-1
        l = min(100, max(0, l)) / 100  # Convert to 0-1

        # Handle grayscale case
        if s == 0:
            rgb_val = int(l * 255)
            return f"#{rgb_val:02x}{rgb_val:02x}{rgb_val:02x}"

        def hue_to_rgb(p: float, q: float, t: float) -> float:
            """Helper function to convert hue to RGB component."""
            if t < 0:
                t += 1
            if t > 1:
                t -= 1
            if t < 1 / 6:
                return p + (q - p) * 6 * t
            if t < 1 / 2:
                return q
            if t < 2 / 3:
                return p + (q - p) * (2 / 3 - t) * 6
            return p

        # Calculate helper values
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q

        # Convert to RGB
        r = int(max(0, min(255, round(hue_to_rgb(p, q, h + 1 / 3) * 255))))
        g = int(max(0, min(255, round(hue_to_rgb(p, q, h) * 255))))
        b = int(max(0, min(255, round(hue_to_rgb(p, q, h - 1 / 3) * 255))))

        return f"#{r:02x}{g:02x}{b:02x}"

    except (ValueError, TypeError, ZeroDivisionError):
        return None

@lru_cache(maxsize=256)
def _normalize_hex_color(color: str) -> Optional[str]:
    """Normalize hex format."""
    # Remove hash if present
    color = color.lstrip('#')

    if not all(c in '0123456789abcdef' for c in color):
        return None

    # Handle different hex formats
    if len(color) == 3:
        return f"#{color[0] * 2}{color[1] * 2}{color[2] * 2}"
    elif len(color) == 6:
        return f"#{color}"
    elif len(color) == 4:
        return f"#{color[0] * 2}{color[1] * 2}{color[2] * 2}"
    elif len(color) == 8:
        return f"#{color[:6]}"

    return None

@lru_cache(maxsize=256)
def is_hex_color(color: str) -> bool:
    """
    Check if the color is a valid hex color.

    Args:
        color: Color string to validate

    Returns:
        bool: True if valid hex color, False otherwise
    """
    if not isinstance(color, str):
        return False

    normalized = normalize_hex_color(color)
    return normalized is not None

@lru_cache(maxsize=256)
def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """
    Convert hex color to RGB tuple.

    Args:
        hex_color (str): Hex color code

    Returns:
        Tuple[int, int, int]: RGB values

    Raises:
        ColorError: If hex_color is invalid
    """
    normalized = normalize_hex_color(hex_color)
    if not normalized:
        raise ColorError(f"Invalid hex color: {hex_color}")

    hex_str = normalized.lstrip('#')
    return tuple(int(hex_str[i:i + 2], 16) for i in (0, 2, 4))

@lru_cache(maxsize=256)
def rgb_to_hex(r: int, g: int, b: int) -> str:
    """
    Convert RGB values to hex color.

    Args:
        r (int): Red value (0-255)
        g (int): Green value (0-255)
        b (int): Blue value (0-255)

    Returns:
        str: Hex color code

    Raises:
        ColorError: If RGB values are invalid
    """
    try:
        r, g, b = [min(255, max(0, int(x))) for x in (r, g, b)]
        return f"#{r:02x}{g:02x}{b:02x}"
    except (ValueError, TypeError) as e:
        raise ColorError(f"Invalid RGB values: {e}")

@lru_cache(maxsize=256)
def darken_color(hex_color: str, factor: float = 0.1) -> str:
    """
    Darken a hex color by a given factor.

    Args:
        hex_color (str): Hex color code, e.g., '#RRGGBB'
        factor (float): Factor by which to darken the color (0 to 1)

    Returns:
        str: Darkened hex color

    Raises:
        ColorError: If hex_color is invalid or factor is out of range
    """
    if not 0 <= factor <= 1:
        raise ColorError("Factor must be between 0 and 1")

    normalized = normalize_hex_color(hex_color)
    if not normalized:
        raise ColorError(f"Invalid hex color: {hex_color}")

    rgb = hex_to_rgb(normalized)
    darkened_rgb = [max(0, int(c * (1 - factor))) for c in rgb]
    return rgb_to_hex(*darkened_rgb)

@lru_cache(maxsize=256)
def lighten_color(hex_color: str, factor: float = 0.1) -> str:
    """
    Lighten a hex color by a given factor.

    Args:
        hex_color (str): Hex color code, e.g., '#RRGGBB'
        factor (float): Factor by which to lighten the color (0 to 1)

    Returns:
        str: Lightened hex color

    Raises:
        ColorError: If hex_color is invalid or factor is out of range
    """
    if not 0 <= factor <= 1:
        raise ColorError("Factor must be between 0 and 1")

    normalized = normalize_hex_color(hex_color)
    if not normalized:
        raise ColorError(f"Invalid hex color: {hex_color}")

    rgb = hex_to_rgb(normalized)
    lightened_rgb = [min(255, int(c + (255 - c) * factor)) for c in rgb]
    return rgb_to_hex(*lightened_rgb)