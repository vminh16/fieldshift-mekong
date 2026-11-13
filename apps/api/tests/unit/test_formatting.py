import pytest

from fieldshift.domain.formatting import number_vi


@pytest.mark.parametrize(
    "value,decimals,expected",
    [
        (8560, None, "8.560"),
        (1234567.89, None, "1.234.567,89"),
        (-1234.5, None, "-1.234,5"),
        (3.33, None, "3,33"),
        (2.0, None, "2"),
        (0, None, "0"),
        (1.2e20, None, "120.000.000.000.000.000.000"),
        (1e-7, None, "0,0000001"),
        (1.28, 1, "1,3"),
        (2, 1, "2,0"),
    ],
)
def test_number_vi(value, decimals, expected):
    assert number_vi(value, decimals) == expected
