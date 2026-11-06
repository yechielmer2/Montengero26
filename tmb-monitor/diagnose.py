"""Read-only diagnostic. Never interprets or announces booking availability."""
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
        text = soup.get_text(" ", strip=True)
        month = "Juillet 2027"
        print(f"{name}: HTTP {response.status_code}; calendar heading={('Calendrier des disponibilités' in text)}; July 2027={month in text}")
        if month in text:
            snippet = text.split(month, 1)[1][:350]
            print("  Calendar excerpt (unverified):", re.sub(r"\\s+", " ", snippet))
        else:
            print("  No July calendar; no availability inference")
    except Exception as exc:
        print(f"{name}: failed ({type(exc).__name__}: {exc})")
print("DIAGNOSTIC ONLY: no availability assertions, no email, no reservations.")
