"""Read-only HTML structure diagnostics. Never announce bookability."""
import re
import requests
from bs4 import BeautifulSoup

HUTS = {
    "nova": "https://montourdumontblanc.com/fr/refuges/auberge-refuge-de-la-nova",
    "soleil": "https://montourdumontblanc.com/fr/refuges/les-chambres-du-soleil",
    "mottets": "https://montourdumontblanc.com/fr/refuges/refuge-des-mottets",
}
for name, url in HUTS.items():
    try:
        response = requests.get(url, timeout=25, headers={"User-Agent": "TMB-personal-availability-diagnostic/1.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        calendar = soup.select_one(".calendar-dispo")
        print(f"{name}: HTTP {response.status_code}; calendar={bool(calendar)}")
        if not calendar:
            continue
        # Print a small sanitized excerpt of calendar markup and class names.
        markup = str(calendar)
        markup = re.sub(r'(?i)(token|key|secret|password|authorization)([=:"\\s]+)[^\\s"<>]+', r'\\1=[redacted]', markup)
        print("  Calendar HTML prefix:", markup[:3500])
        print("  Calendar tag classes:", sorted({x for tag in calendar.find_all(True) for x in (tag.get("class") or []) if "day" in x or "dispo" in x or "calendar" in x})[:60])
        print("  Calendar data attrs:", [(tag.name, {k:v for k,v in tag.attrs.items() if k.startswith("data-")}) for tag in calendar.find_all(True) if any(k.startswith("data-") for k in tag.attrs)][:12])
        print("  Script src paths:", [s.get("src") for s in soup.select("script[src]") if re.search("calend|dispo|reserv", s.get("src",""), re.I)][:8])
        print("  July 2027 text excerpt:", calendar.get_text(" ",strip=True).split("Juillet 2027",1)[-1][:170] if "Juillet 2027" in calendar.get_text(" ",strip=True) else "not found")
    except Exception as exc:
        print(f"{name}: failed ({type(exc).__name__}: {exc})")
print("DIAGNOSTIC ONLY: no availability assertions, no email, no reservations.")
