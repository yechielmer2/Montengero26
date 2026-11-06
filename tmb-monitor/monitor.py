"""Monitor official TMB calendar for >=2 displayed beds; never claim bookability."""
import datetime as dt
import os
import re
import sys
import requests
from bs4 import BeautifulSoup

HUTS = {
    "nova": ("Auberge-Refuge de la Nova", "https://montourdumontblanc.com/fr/refuges/auberge-refuge-de-la-nova"),
    "soleil": ("Les Chambres du Soleil", "https://montourdumontblanc.com/fr/refuges/les-chambres-du-soleil"),
    "mottets": ("Refuge des Mottets", "https://montourdumontblanc.com/fr/refuges/refuge-des-mottets"),
}
DATE_RE = re.compile(r"^(\d{2})/07/2027\s+—\s+(.+)$")

def extract(html):
    calendar = BeautifulSoup(html, "html.parser").select_one(".calendar-dispo")
    if calendar is None:
        raise ValueError("Official calendar missing")
    results = {}
    for cell in calendar.select(".cal-cell[title]"):
        match = DATE_RE.match(cell.get("title", ""))
        if not match:
            continue
        day = int(match.group(1))
        dt.date(2027, 7, day)
        if day in results:
            raise ValueError("Duplicate July date")
        classes = set(cell.get("class", []))
        status = classes & {"cal-cell--dispo", "cal-cell--full", "cal-cell--closed"}
        if len(status) != 1:
            raise ValueError(f"Unknown calendar status on July {day}")
        places_node = cell.select_one(".cal-cell__places")
        places = places_node.get_text(strip=True) if places_node else ""
        if "cal-cell--dispo" in status:
            if not places.isdecimal() or int(places) < 1:
                raise ValueError(f"Invalid available count on July {day}")
            count = int(places)
            # Require agreement between the number displayed and the title.
            if not re.search(rf"\b{count}\s+disponibles?\b", match.group(2), re.I):
                raise ValueError(f"Count/title mismatch on July {day}")
            results[day] = count
        else:
            if places not in ("–", "-", ""):
                raise ValueError(f"Unexpected unavailable count on July {day}")
            results[day] = 0
    if set(results) != set(range(1, 32)):
        raise ValueError(f"Incomplete July 2027 calendar: {len(results)}/31")
    return {day: count for day, count in results.items() if count >= 2}

def main():
    found = []
    errors = []
    for slug, (name, url) in HUTS.items():
        try:
            r = requests.get(url, timeout=30, headers={"User-Agent": "Personal TMB accommodation availability monitor (GitHub Actions)"})
            r.raise_for_status()
            days = extract(r.text)
            print(f"{name}: verified July cells=31; days with >=2 displayed places={len(days)}")
            for day, count in sorted(days.items()):
                found.append((slug, name, url, day, count))
        except (requests.RequestException, ValueError) as exc:
            errors.append(f"{name}: {exc}")
    # Fail closed: do not send any alert when any source fails validation.
    if errors:
        for error in errors:
            print("ERROR", error, file=sys.stderr)
        return 1
    if not found:
        print("No July 2027 dates with >=2 displayed places in the official calendars.")
        return 0
    token = os.environ.get("GH_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo:
        print("Missing GitHub issue credentials; no alerts sent", file=sys.stderr)
        return 1
    api = f"https://api.github.com/repos/{repo}/issues"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    # Open issue per date, deduplicated by exact marker in title; close when no longer available.
    response = requests.get(api, headers=headers, params={"state":"open","per_page":100}, timeout=30)
    response.raise_for_status()
    existing = {issue["title"]: issue for issue in response.json() if "pull_request" not in issue}
    desired = {}
    for slug, name, url, day, count in found:
        date = f"2027-07-{day:02d}"
        title = f"[TMB July 2027] {slug} {date} (>=2 displayed places)"
        desired[title] = (name, url, date, count)
    for title, issue in existing.items():
        if title not in desired:
            response = requests.patch(issue["url"], headers=headers, json={"state":"closed","state_reason":"completed"}, timeout=30)
            response.raise_for_status()
            print("Closed no-longer-current alert:", title)
    for title, (name, url, date, count) in desired.items():
        if title in existing:
            continue
        body = (f"Official calendar for **{name}** currently displays **{count} places** on **{date}**.\n\n"
                f"Source: {url}\n\n"
                "**Not a confirmed reservation for two guests.** Inventory can change, and a booking must be verified in the reservation flow. "
                "Check the official booking page promptly.\n\n"
                "This issue was created automatically after validating all 31 July dates for each of three huts.")
        response = requests.post(api, headers=headers, json={"title":title,"body":body,"assignees":[repo.split("/")[0]]}, timeout=30)
        response.raise_for_status()
        print("Created calendar availability issue:", title)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
