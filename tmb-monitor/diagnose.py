"""Read-only diagnostics for the TMB calendar; never assert availability."""
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
        print(f"{name}: HTTP {response.status_code}; calendar heading={'Calendrier des disponibilités' in text}; July 2027={'Juillet 2027' in text}")
        # Inspect DOM semantics around the month rather than treating visible dashes as counts.
        match = soup.find(string=lambda s: bool(s and 'Juillet 2027' in s))
        if match:
            node = match.parent
            for depth in range(4):
                if node is None:
                    break
                raw = str(node)
                if len(raw) > 1500:
                    raw = raw[:1500] + ' [truncated]'
                print(f"  July DOM ancestor {depth}: {raw}")
                node = node.parent
        print("  Availability-related markup attributes (sample):")
        candidates = soup.select('[data-date], [data-availability], [data-places], [class*=disponib], [class*=calendar], [class*=calendrier]')
        for tag in candidates[:8]:
            attrs = {k: v for k, v in tag.attrs.items() if k in ('class','data-date','data-availability','data-places','title','aria-label')}
            print(f"   <{tag.name}> attrs={attrs} text={tag.get_text(' ', strip=True)[:80]!r}")
        print(f"  Candidate elements: {len(candidates)}")
    except Exception as exc:
        print(f"{name}: failed ({type(exc).__name__}: {exc})")
print("DIAGNOSTIC ONLY: no availability assertions, no email, no reservations.")
