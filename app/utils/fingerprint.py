import hashlib, re

def norm(value: str) -> str:
    value = (value or "").lower().strip()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    return re.sub(r"\s+", " ", value).strip()

def job_fingerprint(company: str, title: str, location: str) -> str:
    raw = "|".join([norm(company), norm(title), norm(location)])
    return hashlib.sha256(raw.encode()).hexdigest()
