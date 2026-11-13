"""Vietnamese display numbers, independent of the process locale."""

from decimal import Decimal


def number_vi(value: int | float, decimals: int | None = None) -> str:
    if decimals is None:
        text = format(Decimal(str(value)), ",f")
        if "." in text:
            text = text.rstrip("0").rstrip(".")
    else:
        text = format(value, f",.{decimals}f")
    return text.translate(str.maketrans({",": ".", ".": ","}))
