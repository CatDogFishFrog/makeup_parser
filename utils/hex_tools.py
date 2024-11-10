import re
from functools import lru_cache


@lru_cache(maxsize=128)
def darken_color(hex_color: str, factor: float = 0.1) -> str:
    """
    Darken a hex color by a given factor.
    Args:
        hex_color (str): Hex color code, e.g., '#RRGGBB'.
        factor (float): Factor by which to darken the color (0 to 1).
    Returns:
        str: Darkened hex color.
    """
    hex_color = hex_color.lstrip('#')
    rgb = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
    darkened_rgb = [max(0, int(c * (1 - factor))) for c in rgb]
    return f"#{''.join(f'{c:02x}' for c in darkened_rgb)}"

@lru_cache(maxsize=128)
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

    hex_pattern = re.compile(r'^#[0-9A-Fa-f]{6}$')
    return bool(hex_pattern.match(color))