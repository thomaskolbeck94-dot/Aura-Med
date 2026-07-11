def generate_refill_link(pzn: str, partner: str = "shop_apotheke") -> str:
    """
    Generates an affiliate link for a given medication (PZN).
    This enables Pillar 3 (Smart Refill) monetization without external API calls.
    """
    
    # Strip any potential 'PZN' prefix and spaces, just to be safe
    clean_pzn = "".join(filter(str.isdigit, pzn))
    
    # Example Affiliate ID. In production, this would be an env variable.
    affiliate_id = "auramed_smart_refill_01"
    
    if partner == "shop_apotheke":
        # Example URL structure for Shop-Apotheke
        return f"https://www.shop-apotheke.com/search.htm?i={clean_pzn}&affiliate={affiliate_id}"
    elif partner == "docmorris":
        # Example URL structure for DocMorris
        return f"https://www.docmorris.de/search?query={clean_pzn}&partner={affiliate_id}"
    else:
        # Fallback to a generic Google search or a custom AuraMed landing page
        return f"https://www.google.com/search?q=PZN+{clean_pzn}"
