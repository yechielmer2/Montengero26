"""Read-only July 2027 calendar inspection. No alerts or booking assertions."""
import collections
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
        if not calendar:
            raise ValueError("Calendar not found")
        cells = calendar.select(".cal-cell[title]")
        july = []
        for cell in cells:
            title = cell.get("title", "")
            if re.search(r"\\b\\d{2}/07/2027\\b", title):
                classes = [c for c in cell.get("class", []) if c.startswith("cal-cell--")]
                places = cell.select_one(".cal-cell__places")
                july.append((title, ",".join(classes), places.get_text(" ", strip=True) if places else None, cell.name))
        print(f"{name}: HTTP {response.status_code}; July dated cells={len(july)}")
        print("  Class counts:", dict(collections.Counter(x[1] for x in july)))
        for row in july:
            print("  ", repr(row))
        if len(july) != 31:
            print("  WARNING: not all 31 dates found; parser cannot verify July")
        print("  Other available examples (not July):", [(x.get("title"), (x.select_one(".cal-cell__places").get_text(" ",strip=True) if x.select_one(".cal-cell__places") else None)) for x in calendar.select(".cal-cell--dispo[title]")[:3]])
    except Exception as exc:
        print(f"{name}: ERROR {type(exc).__name__}: {exc}")
print("READ ONLY. No notifications. Counts alone do not guarantee booking for two.")
