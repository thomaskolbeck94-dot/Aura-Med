def is_valid_pzn(pzn_string: str) -> bool:
    """
    Validates a German PZN (Pharmazentralnummer) using the modulo 11 algorithm.
    A valid PZN is an 8-digit number where the 8th digit is the check digit.
    
    The check digit is calculated as:
    (d1*1 + d2*2 + d3*3 + d4*4 + d5*5 + d6*6 + d7*7) % 11
    
    If the modulo operation results in 10, the PZN is invalid (never issued).
    """
    # Remove any potential prefixes like "PZN-" or "PZN " or just whitespaces
    cleaned = pzn_string.upper().replace("PZN", "").replace("-", "").strip()
    
    if len(cleaned) != 8 or not cleaned.isdigit():
        return False
        
    digits = [int(d) for d in cleaned]
    weights = [1, 2, 3, 4, 5, 6, 7]
    
    # Calculate weighted sum of the first 7 digits
    weighted_sum = sum(d * w for d, w in zip(digits[:7], weights))
    
    check_digit = weighted_sum % 11
    
    # Check digit of 10 is invalid according to IFA rules
    if check_digit == 10:
        return False
        
    # The calculated check digit must match the 8th digit
    return check_digit == digits[7]

