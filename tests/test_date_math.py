import pytest
from auramed.core.date_math import parse_gs1_expiry_date, is_leap_year

def test_parse_exact_date():
    assert parse_gs1_expiry_date("280515") == "2028-05-15"

def test_parse_month_end_regular():
    # May has 31 days
    assert parse_gs1_expiry_date("280500") == "2028-05-31"
    # June has 30 days
    assert parse_gs1_expiry_date("280600") == "2028-06-30"

def test_parse_month_end_february_leap_year():
    # 2028 is a leap year (2028 % 4 == 0)
    assert is_leap_year(28) is True
    assert parse_gs1_expiry_date("280200") == "2028-02-29"

def test_parse_month_end_february_non_leap_year():
    # 2029 is not a leap year (2029 % 4 != 0)
    assert is_leap_year(29) is False
    assert parse_gs1_expiry_date("290200") == "2029-02-28"

def test_invalid_length():
    with pytest.raises(ValueError):
        parse_gs1_expiry_date("28050")
