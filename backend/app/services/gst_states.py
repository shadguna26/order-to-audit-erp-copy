import re
from typing import Optional

GSTIN_REGEX = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")

INDIAN_STATES = {
    "Jammu and Kashmir": "01",
    "Himachal Pradesh": "02",
    "Punjab": "03",
    "Chandigarh": "04",
    "Uttarakhand": "05",
    "Haryana": "06",
    "Delhi": "07",
    "Rajasthan": "08",
    "Uttar Pradesh": "09",
    "Bihar": "10",
    "Sikkim": "11",
    "Arunachal Pradesh": "12",
    "Nagaland": "13",
    "Manipur": "14",
    "Mizoram": "15",
    "Tripura": "16",
    "Meghalaya": "17",
    "Assam": "18",
    "West Bengal": "19",
    "Jharkhand": "20",
    "Odisha": "21",
    "Chhattisgarh": "22",
    "Madhya Pradesh": "23",
    "Gujarat": "24",
    "Dadra and Nagar Haveli and Daman and Diu": "26",
    "Maharashtra": "27",
    "Andhra Pradesh": "37",
    "Karnataka": "29",
    "Goa": "30",
    "Lakshadweep": "31",
    "Kerala": "32",
    "Tamil Nadu": "33",
    "Puducherry": "34",
    "Andaman and Nicobar Islands": "35",
    "Telangana": "36",
    "Ladakh": "38",
}

_STATE_LOWER_MAP = {k.lower(): (k, v) for k, v in INDIAN_STATES.items()}


def resolve_state_and_code(state_name: str) -> tuple[str, str]:
    clean = (state_name or "").strip()
    hit = _STATE_LOWER_MAP.get(clean.lower())
    if not hit:
        raise ValueError(f"Unsupported Indian state: '{state_name}'")
    return hit


def validate_gstin_for_state(gstin: Optional[str], state_code: str) -> Optional[str]:
    if not gstin or not gstin.strip():
        return None
    clean = gstin.strip().upper()
    if not GSTIN_REGEX.match(clean):
        raise ValueError("Invalid GSTIN format (expected 15-character GSTIN like 33AAAAA0000A1Z5)")
    if clean[:2] != state_code:
        raise ValueError(f"GSTIN state prefix '{clean[:2]}' does not match chosen state code '{state_code}'")
    return clean
