"""
Data Cleaner Module for Bengaluru Traffic Signal Dataset.
Handles AutoCAD text drafting anomalies such as double-struck bold characters
and reversed vertical approach labels.
"""

import re

REVERSED_TERMS = {
    "NAIRTSEDEP EVISULCXE": "EXCLUSIVE PEDESTRIAN",
    "EVISULCXE NAIRTSEDEP": "EXCLUSIVE PEDESTRIAN",
    "NAIRTSEDEP": "PEDESTRIAN",
    "EVISULCXE": "EXCLUSIVE",
    "ATTAHGARENNAB": "BANNERGHATTA",
    "ATTAHGARENNAB DAOR": "BANNERGHATTA ROAD",
    "DAOR": "ROAD",
    "TWEES": "SWEET",
}

KNOWN_ACRONYMS = {
    "BDA": "BDA",
    "BHEL": "BHEL",
    "BMTC": "BMTC",
    "IOC": "IOC",
    "UCO": "UCO",
    "CMP": "CMP",
    "ESI": "ESI",
    "CMH": "CMH",
    "WCR": "WCR",
    "BEL": "BEL",
    "BTP": "BTP",
    "TPS": "TPS",
    "VAC": "VAC",
}

def dedup_token(token: str) -> str:
    """
    Condense AutoCAD faux-bold doubled characters in a token.
    Uses pairwise double detection so legitimate numbers like '08:00' or '100'
    are preserved, while '9900((7700))' -> '90(70)' and 'BBAANNGGAALLOORREE' -> 'BANGALORE'.
    """
    if not token or len(token) < 4:
        return token

    # Never modify standard time patterns like 08:00
    if re.match(r"^\d{2}:\d{2}$", token):
        return token

    # Check pairwise character doubling
    pairs = [token[i:i+2] for i in range(0, len(token) - 1, 2)]
    matching_pairs = sum(1 for p in pairs if len(p) == 2 and p[0] == p[1])
    
    # If at least 70% of pairs are identical consecutive characters
    if matching_pairs >= max(2, int(len(pairs) * 0.7)):
        res = []
        i = 0
        while i < len(token):
            if i + 1 < len(token) and token[i] == token[i + 1]:
                res.append(token[i])
                i += 2
            else:
                res.append(token[i])
                i += 1
        return "".join(res)

    return token

def clean_cad_string(text: str) -> str:
    """
    Normalizes a CAD extracted string by fixing reversed vertical text
    and condensing double-struck glyphs.
    """
    if not text:
        return ""

    s = text.strip()

    # Check for known reversed strings
    for rev_key, corrected in REVERSED_TERMS.items():
        if rev_key in s:
            s = s.replace(rev_key, corrected)

    # If general reversed pedestrian indicator remains
    if "NAIRTSEDEP" in s:
        s = s[::-1]

    # Clean tokens
    tokens = s.split()
    cleaned_tokens = [dedup_token(t) for t in tokens]
    cleaned = " ".join(cleaned_tokens)

    # Collapse multiple whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned

def parse_time_window(time_str: str) -> tuple[str, str]:
    """
    Extracts start and end times from strings like '07:00 09:00' or '08:30-11:30'.
    """
    match = re.search(r"(\d{2}:\d{2})\s*[-to\s]\s*(\d{2}:\d{2})", time_str)
    if match:
        return match.group(1), match.group(2)
    return "", ""
