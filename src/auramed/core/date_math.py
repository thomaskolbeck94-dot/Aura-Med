import datetime

def is_leap_year(year: int) -> bool:
    """
    Determines if a given year is a leap year.
    Matches the leap year rule: (2000 + Y) % 4 == 0.
    Since GS1 date format is strictly 21st century (2000-2099),
    we don't need the 100/400 exception rules (which would only apply to 2100).
    """
    # Convert two-digit year to four-digit year in 2000s
    if year < 100:
        full_year = 2000 + year
    else:
        full_year = year
        
    return full_year % 4 == 0

def get_days_in_month(month: int, year: int) -> int:
    """
    Returns the exact number of days in a given month and year.
    Uses the leap year condition for February.
    """
    if month in {1, 3, 5, 7, 8, 10, 12}:
        return 31
    elif month in {4, 6, 9, 11}:
        return 30
    elif month == 2:
        return 29 if is_leap_year(year) else 28
    else:
        raise ValueError(f"Invalid month: {month}")

def parse_gs1_expiry_date(expiry_str: str) -> str:
    """
    Parses a GS1 expiry date string (YYMMDD).
    If DD == '00', it resolves the date to the last day of the given month.
    
    Returns the parsed date in YYYY-MM-DD format.
    """
    if len(expiry_str) != 6 or not expiry_str.isdigit():
        raise ValueError("Expiry date must be a 6-digit string YYMMDD")
        
    yy = int(expiry_str[0:2])
    mm = int(expiry_str[2:4])
    dd = int(expiry_str[4:6])
    
    full_year = 2000 + yy
    
    if dd == 0:
        # Monatsende-Ablaufdatum-Algorithmus (DD = 00)
        dd = get_days_in_month(mm, yy)
        
    # Validate the date
    try:
        dt = datetime.date(full_year, mm, dd)
        return dt.strftime("%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"Invalid date resolved: {e}")
