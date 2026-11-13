import re

VALID_TYPES = {
    "H": "Home",
    "V": "Vehicle",
    "P": "Personal",
    "E": "Education",
}


def dfa_validate(code):
    code = (code or "").strip().upper()
    if len(code) != 11:
        return False
    if code[:4] != "LOAN":
        return False
    if code[4] not in VALID_TYPES:
        return False
    if not code[5:].isdigit():
        return False
    return True


def regex_validate(code):
    pattern = r"^LOAN[HVPE][0-9]{6}$"
    return bool(re.fullmatch(pattern, (code or "").strip().upper()))


def classify_loan_type(code):
    code = (code or "").strip().upper()
    if not dfa_validate(code):
        return "Invalid"
    return VALID_TYPES.get(code[4], "Invalid")
