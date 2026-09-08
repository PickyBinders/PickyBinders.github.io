#!/usr/bin/env python3
"""Refresh the website's publication snapshot from a public Google Scholar profile.

A failed/partial fetch never replaces the last complete Scholar snapshot.
Stable IDs survive publication updates; abstracts belong to a specific version.
Local Jekyll builds only read the committed snapshot and need no network.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import subprocess
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
PROFILE = "PQ-my-kAAAAJ"
BASE = "https://scholar.google.com"
CACHE = ROOT / "bibliography/scholar.json"
OUTPUT = ROOT / "_data/publications.json"
STATE = ROOT / "_data/publication_sync.json"
CONFIG = ROOT / "bibliography/scholar_config.json"
METADATA = ROOT / "bibliography/metadata.json"


def read_json(path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def save_json(path, value):
    # Replace only once complete JSON has been serialized and written.
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def normalized(title):
    text = unicodedata.normalize("NFKD", title).casefold()
    return "".join(c for c in text if c.isalnum())


def safe_url(value):
    return value if urlparse(value or "").scheme in ("https", "http") else ""


def plain(value):
    return BeautifulSoup(str(value or ""), "html.parser").get_text(" ", strip=True)


def clean_venue(item):
    """Strip only known bibliographic suffixes from Scholar's fallback venue."""
    venue = item.get("venue", "").strip()
    year = item.get("year")
    if year:
        venue = re.sub(r",\s*" + str(year) + r"\s*$", "", venue).strip()
    pages = item.get("pages", "")
    if pages:
        venue = re.sub(r",\s*" + re.escape(pages) + r"\s*$", "", venue).strip()
    volume = item.get("volume", "")
    if volume:
        issue = r"(?:\s*\([^)]*\))?"
        venue = re.sub(r"\s+" + re.escape(volume) + issue + r"\s*$", "", venue).strip()
    item["venue"] = venue
    # Preprint identifiers are not page ranges.
    if "preprint" in venue.casefold() or "biorxiv" in venue.casefold() or "medrxiv" in venue.casefold():
        item["pages"] = ""
    return item


def paper_doi(item):
    if item.get("doi"):
        return item["doi"].lower()
    url = unquote(item.get("url", ""))
    match = re.search(r"10\.\d{4,9}/[^?#\s]+", url)
    if match:
        return re.sub(r"(?:v\d+)?(?:\.abstract|\.full|\.pdf)?$", "", match[0]).lower()
    parsed = urlparse(url)
    if parsed.hostname in ("www.nature.com", "nature.com") and "/articles/" in parsed.path:
        return "10.1038/" + parsed.path.split("/articles/", 1)[1].rstrip("/")
    if parsed.hostname == "academic.oup.com":
        parts = parsed.path.strip("/").split("/")
        if len(parts) >= 3:
            return "10.1093/" + parts[0] + "/" + parts[-2]
    return ""


def metadata_signature(item):
    return [normalized(item["title"]), item.get("url", ""), item.get("doi", ""), item.get("metadata_id", "")]


def get_json(session, url, **params):
    response = session.get(url, params=params, timeout=15)
    response.raise_for_status()
    return response.json()


def manubot_metadata(identifier):
    # Isolate the library's network calls so an unresponsive provider cannot
    # stall the weekly build. Use this interpreter's installed Manubot version.
    result = subprocess.run([
        sys.executable, "-c", "from manubot.command import main; main()",
        "cite", "--format", "csljson", "--log-level", "ERROR", identifier,
    ], capture_output=True, text=True, encoding="utf-8", timeout=35, check=True)
    items = json.loads(result.stdout)
    if not isinstance(items, list) or len(items) != 1:
        raise ValueError("Manubot did not return one citation")
    return items[0]


def fetch_metadata(session, item):
    """Resolve exact identifiers; title discovery requires an exact normalized match.

    Fetch full source abstracts, never search snippets or Scholar descriptions.
    A provider outage must not erase a previously saved abstract.
    """
    metadata = {}
    doi = paper_doi(item)
    errors = []

    def request(url, **params):
        try:
            return get_json(session, url, **params)
        except (requests.RequestException, ValueError) as error:
            errors.append(str(error))
            return {}

    if urlparse(item.get("url", "")).hostname == "openreview.net":
        note_id = parse_qs(urlparse(item["url"]).query).get("id", [""])[0]
        url = "https://api2.openreview.net/notes"
        for note in request(url, id=note_id).get("notes", []):
            content = note.get("content", {})
            title = content.get("title", {}).get("value", "")
            abstract = content.get("abstract", {}).get("value", "")
            if note.get("id") == note_id and normalized(title) == normalized(item["title"]) and abstract:
                return {"abstract": plain(abstract), "abstract_source": item["url"], "metadata_provider": "OpenReview"}

    if not doi:
        data = request("https://api.crossref.org/works", **{"query.bibliographic": item["title"], "rows": 3})
        for candidate in data.get("message", {}).get("items", []):
            titles = candidate.get("title", [])
            if titles and normalized(plain(titles[0])) == normalized(item["title"]):
                doi = candidate.get("DOI", "").lower()
                break
    if doi:
        metadata["doi"] = doi
    identifier = item.get("metadata_id") or ("doi:" + doi if doi else item.get("url", ""))
    if identifier:
        try:
            candidate = manubot_metadata(identifier)
            abstract = plain(candidate.get("abstract"))
            # Do not substitute a generic webpage description or truncated snippet.
            if normalized(plain(candidate.get("title"))) == normalized(item["title"]) and len(abstract) > 100 and not abstract.endswith(("…", "...")):
                metadata.update(abstract=abstract, abstract_source=candidate.get("URL") or item["url"], metadata_provider="Manubot")
        except (subprocess.SubprocessError, OSError, ValueError, TypeError) as error:
            errors.append(f"Manubot: {type(error).__name__}")
    if doi and not metadata.get("abstract"):
        url = "https://api.crossref.org/works/" + quote(doi, safe="")
        candidate = request(url).get("message", {})
        if candidate.get("DOI", "").lower() == doi:
            abstract = plain(candidate.get("abstract"))
            if abstract:
                metadata.update(abstract=abstract, abstract_source=url, metadata_provider="Crossref")
        if not metadata.get("abstract"):
            url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
            data = request(url, query='DOI:"' + doi + '"', format="json", resultType="core", pageSize=10)
            for candidate in data.get("resultList", {}).get("result", []):
                if candidate.get("doi", "").lower() == doi and candidate.get("abstractText"):
                    source = "https://europepmc.org/article/" + candidate["source"] + "/" + candidate["id"]
                    metadata.update(abstract=plain(candidate["abstractText"]), abstract_source=source, metadata_provider="Europe PMC")
                    break
    if errors and not metadata.get("abstract"):
        raise ValueError("; ".join(errors))
    return metadata


def enrich_records(records, cache, session=None, force=False):
    """Offline by default. Cache is keyed by stable ID and source fingerprint."""
    today = datetime.now(timezone.utc).date()
    for item in records:
        signature = metadata_signature(item)
        saved = cache.get(item["id"], {})
        current = saved.get("signature") == signature
        age = 9999
        if current and saved.get("checked"):
            age = (today - datetime.strptime(saved["checked"], "%Y-%m-%d").date()).days
        # Curated full abstracts take precedence; don't refetch them.
        if session and not item.get("abstract") and (force or not current or age >= (90 if saved.get("abstract") else 7)):
            try:
                fetched = fetch_metadata(session, item)
                saved = {**(saved if current else {}), **fetched, "signature": signature, "checked": today.isoformat()}
                cache[item["id"]] = saved
                current = True
                print(f"Metadata {item['id']}: {'abstract saved' if saved.get('abstract') else 'no abstract available'}", flush=True)
            except (requests.RequestException, ValueError, KeyError, TypeError) as error:
                print(f"::warning::Metadata for {item['id']}: {error}. Keeping saved metadata.", flush=True)
        if current:
            for field in ("doi", "abstract", "abstract_source"):
                if saved.get(field) and not item.get(field):
                    item[field] = saved[field]
    return records


def parse_profile(content):
    soup = BeautifulSoup(content, "html.parser")
    if not soup.select_one("#gsc_prf_in"):
        raise ValueError("Scholar returned a challenge or an unexpected page")
    rows = []
    for element in soup.select(".gsc_a_tr"):
        title = element.select_one(".gsc_a_at")
        year = element.select_one(".gsc_a_y")
        if not title or not title.get("href"):
            raise ValueError("Scholar returned an incomplete publication row")
        url = urljoin(BASE, title["href"])
        citation = parse_qs(urlparse(url).query).get("citation_for_view", [""])[0]
        if not citation.startswith(PROFILE + ":"):
            raise ValueError("Unexpected Scholar citation identifier")
        gray = element.select(".gs_gray")
        rows.append({
            "id": "scholar_" + citation.split(":")[1],
            "scholar_id": citation.split(":")[1],
            "title": title.get_text(" ", strip=True),
            "authors": gray[0].get_text(" ", strip=True) if gray else "",
            "venue": gray[1].get_text(" ", strip=True) if len(gray) > 1 else "",
            "year": int(year.get_text(strip=True)) if year and year.get_text(strip=True).isdigit() else 0,
            "url": url,
            "scholar_url": url,
        })
    if not rows:
        raise ValueError("Scholar returned no publications")
    more = soup.select_one("#gsc_bpf_more")
    if more is None:
        raise ValueError("Scholar pagination control is missing")
    return rows, not more.has_attr("disabled")


def parse_detail(content, row):
    soup = BeautifulSoup(content, "html.parser")
    title = soup.select_one("#gsc_oci_title")
    if not title:
        raise ValueError("Scholar citation details unavailable")
    fields = {}
    for label in soup.select(".gsc_oci_field"):
        value = label.find_next_sibling(class_="gsc_oci_value")
        if value:
            fields[label.get_text(strip=True)] = value.get_text(" ", strip=True)
    result = dict(row)
    result["title"] = title.get_text(" ", strip=True)
    result["authors"] = fields.get("Authors", row["authors"])
    result["venue"] = next((fields[k] for k in ("Journal", "Conference", "Book") if k in fields), row["venue"])
    date = fields.get("Publication date", "")
    if re.match(r"^\d{4}", date):
        result["year"] = int(date[:4])
        result["date"] = "-".join(part.zfill(2) for part in date.split("/"))
    link = title.select_one("a[href]")
    if link and safe_url(link["href"]):
        result["url"] = link["href"]
    # Scholar often truncates descriptions; do not present them as full abstracts.
    for source, destination in (("Volume", "volume"), ("Issue", "issue"), ("Pages", "pages")):
        if fields.get(source):
            result[destination] = fields[source]
    result["detail_fetched"] = True
    return result


def fetch_scholar(session, previous, profile_html=None):
    old = {item["scholar_id"]: item for item in previous}
    publications = []
    seen = set()
    for page in range(20):
        if page == 0 and profile_html:
            content = profile_html.read_bytes()
        else:
            response = session.get(BASE + "/citations", params={
                "user": PROFILE, "hl": "en", "pagesize": 100, "cstart": page * 100,
            }, timeout=20)
            response.raise_for_status()
            content = response.content
        rows, more = parse_profile(content)
        for row in rows:
            if row["scholar_id"] in seen:
                raise ValueError("Scholar repeated a page; keeping the previous snapshot")
            seen.add(row["scholar_id"])
            cached = old.get(row["scholar_id"])
            # Refetch details when the row changes (e.g. a preprint becomes published).
            if cached and cached.get("profile_signature") == [row["title"], row["venue"], row["year"]]:
                publications.append(cached)
                continue
            signature = [row["title"], row["venue"], row["year"]]
            response = session.get(row["scholar_url"], timeout=20)
            response.raise_for_status()
            enriched = parse_detail(response.content, row)
            enriched["profile_signature"] = signature
            publications.append(enriched)
            time.sleep(0.15)
        if not more:
            if len(publications) < len(previous):
                raise ValueError("Scholar returned fewer records; check removals manually before replacing the cache")
            return publications
    raise ValueError("Scholar exceeded the pagination limit; snapshot not replaced")


def from_csl(item):
    date = item.get("issued", {}).get("date-parts", [[]])[0]
    authors = ", ".join(" ".join(filter(None, (a.get("given"), a.get("family")))) or a.get("literal", "")
                        for a in item.get("author", []))
    venue = item.get("container-title") or ("Preprint" if item.get("type") == "manuscript" else "")
    if isinstance(venue, list):
        venue = venue[0] if venue else ""
    return {
        "id": item["id"], "title": plain(item.get("title")), "authors": authors,
        "venue": plain(venue), "year": date[0] if date else 0,
        "date": "-".join(str(v).zfill(2) for v in date),
        "url": safe_url(item.get("URL")), "doi": item.get("DOI", ""),
        "abstract": plain(item.get("abstract")), "volume": item.get("volume", ""),
        "pages": item.get("page", ""),
    }


def update_version(record, updates):
    """Carry metadata forward only when the source still identifies this version.

    Compare incoming identifiers before merging: otherwise an old curated DOI
    masks a new publisher URL. Equivalent DOI and publisher URLs are harmless.
    Explicit manual metadata is applied after clearing any previous version.
    """
    old_doi = paper_doi(record)
    new_doi = paper_doi(updates)
    old_url = record.get("url", "").rstrip("/")
    new_url = updates.get("url", "").rstrip("/")
    # Scholar's detail-page fallback is not evidence of a new paper version.
    source_changed = bool(old_url and new_url and old_url != new_url
                          and urlparse(new_url).hostname != "scholar.google.com")
    version_changed = (bool(old_doi and new_doi and old_doi != new_doi)
                       or (source_changed and not (old_doi and old_doi == new_doi)))
    if version_changed:
        for field in ("doi", "abstract", "abstract_source", "metadata_id", "volume", "issue", "pages", "date"):
            record.pop(field, None)
    record.update(updates)
    if new_doi:
        record["doi"] = new_doi


def merge_records(scholar, curated, config):
    aliases = config["aliases"]
    overrides = config.get("overrides", {})
    excluded = set(config.get("exclude_scholar_ids", []))
    result = {}
    # Curated records preserve complete DOI metadata and existing project IDs.
    for item in curated:
        result[item["id"]] = from_csl(item)
    by_title = {normalized(p["title"]): key for key, p in result.items()}
    for item in scholar:
        if item["scholar_id"] in excluded:
            continue
        item = copy.deepcopy(item)
        key = aliases.get(item["scholar_id"]) or by_title.get(normalized(item["title"])) or item["id"]
        if key in result:
            # Scholar supplies publication updates; keep the stable key, not stale metadata.
            update_version(result[key], {k: v for k, v in item.items() if v and k not in ("id", "profile_signature")})
        else:
            item["id"] = key
            result[key] = item
        by_title[normalized(item["title"])] = key
    for key, values in overrides.items():
        if key in result:
            expected = values.get("when_venue_contains")
            if expected and not any(term.casefold() in result[key].get("venue", "").casefold() for term in expected):
                continue
            update_version(result[key], {k: v for k, v in values.items() if k != "when_venue_contains"})
    for item in result.values():
        if item.get("date"):
            item["date"] = "-".join(part.zfill(2) for part in item["date"].split("-"))
        clean_venue(item)
    # Exact normalized-title duplicates collapse, preferring dated records.
    unique = {}
    for item in sorted(result.values(), key=lambda p: p.get("year", 0), reverse=True):
        key = normalized(item["title"])
        if key not in unique:
            unique[key] = item
    # Keep the full source cache, but only publish records within the site's scope.
    # Apply the cutoff after metadata overrides so corrected dates are respected.
    minimum_year = config.get("min_year", 0)
    visible = [item for item in unique.values() if item.get("year", 0) >= minimum_year]
    return sorted(visible, key=lambda p: (p.get("year", 0), p.get("date", ""), p["title"]), reverse=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="Rebuild from saved metadata only")
    parser.add_argument("--metadata-only", action="store_true", help="Fill missing abstracts without contacting Scholar")
    parser.add_argument("--refresh-metadata", action="store_true", help="Recheck metadata even if recently cached")
    parser.add_argument("--profile-html", type=Path, help="Use a saved public profile for the first page")
    args = parser.parse_args()
    config = read_json(CONFIG, {})
    previous = read_json(CACHE, [])
    state = read_json(STATE, {})
    scholar = previous
    refreshed = False
    session = requests.Session()
    session.headers["User-Agent"] = "Mozilla/5.0 (compatible; AcademicWebsitePublicationSync/1.0; +https://pickybinders.github.io)"
    if not args.offline and not args.metadata_only:
        try:
            scholar = fetch_scholar(session, previous, args.profile_html)
            refreshed = True
            print(f"Refreshed {len(scholar)} Scholar records.")
        except (requests.RequestException, ValueError) as error:
            print(f"::warning::Scholar refresh failed: {error}. Keeping the saved bibliography.")
            if not previous and OUTPUT.exists():
                return
            if not previous:
                raise SystemExit("No Scholar snapshot exists; retry the initial import.")
    curated = read_json(ROOT / "bibliography/publications.csl.json", [])
    records = merge_records(scholar, curated, config)
    if not records:
        raise SystemExit("No publication metadata available")
    required = set(config.get("required_ids", []))
    if not required.issubset({p["id"] for p in records}):
        raise SystemExit("Required featured publications missing; output left untouched")
    metadata = read_json(METADATA, {})
    records = enrich_records(records, metadata, None if args.offline else session, args.refresh_metadata)
    if not args.offline:
        save_json(METADATA, metadata)
    if refreshed:
        save_json(CACHE, scholar)
        state = {"updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "source": BASE + "/citations?user=" + PROFILE}
        save_json(STATE, state)
    save_json(OUTPUT, records)
    print(f"Wrote {len(records)} publications to {OUTPUT.relative_to(ROOT)}.")


if __name__ == "__main__":
    main()
