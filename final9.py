# final_streamlit_extractor_optionB.py

import streamlit as st
import os
import re
import io
import zipfile
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

# -------------------------
# CONFIG
# -------------------------
MAX_PAGES_TO_CRAWL = 10
MAX_THREADS = 10

# Core site list
NEET_SITES = {
    # AACCC
    "AACCC CURRENT EVENTS (UG)": "https://aaccc.gov.in/current-events-ug/",
    "AACCC NEWS & EVENTS (UG)": "https://aaccc.gov.in/news-events-ug/",
    "AACCC CURRENT EVENTS (PG)": "https://aaccc.gov.in/current-events-pg/",
    "AACCC NEWS & EVENTS (PG)": "https://aaccc.gov.in/news-events-pg/",

    # Bihar
    "BIHAR HOME": "https://bceceboard.bihar.gov.in/index.php",
    "BIHAR UGMAC NOTICE": "https://bceceboard.bihar.gov.in/UGMACIndex.php",
    "BIHAR UGAYUSH NOTICE": "https://bceceboard.bihar.gov.in/UGAACIndex.php",
    "BIHAR PGMAC NOTICE": "https://bceceboard.bihar.gov.in/PGMACIndex.php",
    "BIHAR PGAYUSH NOTICE": "https://bceceboard.bihar.gov.in/PGAACIndex.php",

    # States & others
    "RAJASTHAN": "https://rajugneet2025.in/",
    "TELANGANA (KNRUHS)": "https://www.knruhs.telangana.gov.in/all-notifications/?cpage=1",
    "HIMACHAL PRADESH (AMRUHP)": "https://amruhp.ac.in/notices/",
    "JHARKHAND": "https://neetug.jceceb.org.in/Public/Home#parentHorizontalTab2",
    "SIKKIM NOTICES": "https://smu.edu.in/smu-notice-board.php",

    # Tripura
    "TRIPURA UG COUNSELLING": "https://trmcc.admissions.nic.in/ug-counselling/",
    "TRIPURA PG COUNSELLING": "https://trmcc.admissions.nic.in/pg-counselling/",

    # Andhra Pradesh
    "ANDHRA PRADESH MBBS CQ": "https://apuhs-ugadmissions.aptonline.in/MBBS/Home/Home",
    "ANDHRA PRADESH MBBS MQ": "https://apuhs-ugadmissions.aptonline.in/MBBSMQ/Home/Home",
    "ANDHRA PRADESH MEDICAL PG CQ": "https://apuhs-pgadmissions.aptonline.in/pgmedcq",
    "ANDHRA PRADESH AYUSH CQ": "https://apuhs-ugadmissions.aptonline.in/UGAYUSH/Home/Home",
    "ANDHRA PRADESH AYUSH AIQ": "https://apuhs-ugadmissions.aptonline.in/UGAYUSHAIQ",
    "ANDHRA PRADESH AYUSH MQ": "https://apuhs-ugadmissions.aptonline.in/UGAYUSHMQ",

    # MCC
    "MCC SCHEDULES (UG)": "https://mcc.nic.in/eservices-schedule-ug/",
    "MCC NEWS & EVENTS (UG)": "https://mcc.nic.in/news-events-ug-medical/",
    "MCC CURRENT EVENTS (UG)": "https://mcc.nic.in/current-events-ug/",
    "MCC MDS SCHEDULE": "https://mcc.nic.in/eservices-schedule-mds/",
    "MCC MDS NEWS AND EVENTS": "https://mcc.nic.in/news-events-mds/",
    "MCC MDS CURRENT EVENTS": "https://mcc.nic.in/current-events-mds/",
    "MCC PG SCHEDULE": "https://mcc.nic.in/eservices-schedule-pg/",
    "MCC PG NEWS AND EVENTS": "https://mcc.nic.in/news-events-pg/",
    "MCC PG CURRENT EVENTS": "https://mcc.nic.in/current-events-pg/",

    # Odisha
    "ODISHA BAMS & BHMS": "https://odishajee.com/info.php?crs=BAMS-BHMS",
    "ODISHA PUBLIC NOTICE (MBBS & BDS)": "https://ojee.nic.in/medical-notice/",
    "ODISHA MBBS & BDS INFORMATION": "https://ojee.nic.in/medical-information/",

    # Kerala KEAM Allotment
    "KERALA ALLOTMENT LISTS": "https://cee.kerala.gov.in/keam2025/allotlist",

        # Maharashtra
    "MAHARASHTRA UG": "https://medicalug2025.mahacet.org/NEET-UG-2025/login",
    "MAHARASHTRA PG": "https://medicalug2025.mahacet.org/NEET-PGM-2025/login",
    "HARYANA UG": "https://uhsrugcounselling.com/Notice",
    "PONDICHERRY": "https://www.centacpuducherry.in/",
    "PUNJAB MBBS & BDS": "https://bfuhs.ac.in/mbbs_bds/mbbsbds.asp",
    "TAMIL NADU AYUSH": "https://tnayushselection.org/#"

}

# Chhattisgarh main + AYUSH endpoints
CHHATTISGARH_URLS = {
    "CH_GH_OR_CR": "https://cgdme.admissions.nic.in/or-cr/",
    "CH_GH_SEAT_MATRIX": "https://cgdme.admissions.nic.in/seat-matrix/",
    "CH_GH_MERIT_LISTS": "https://cgdme.admissions.nic.in/merit-list/",
    "CH_GH_ALLOTMENT_LISTS": "https://cgdme.admissions.nic.in/allotment-result/",
    "CH_GH_SCHEDULE": "https://cgdme.admissions.nic.in/schedule/",
    "CH_GH_NOTICES": "https://cgdme.admissions.nic.in/notices/",
    # AYUSH
    "CH_AYUSH_OR_CR": "https://cgayush.admissions.nic.in/or-cr/",
    "CH_AYUSH_SEAT_MATRIX": "https://cgayush.admissions.nic.in/seat-matrix/",
    "CH_AYUSH_MERIT_LISTS": "https://cgayush.admissions.nic.in/merit-list/",
    "CH_AYUSH_SCHEDULE": "https://cgayush.admissions.nic.in/schedule/",
    "CH_AYUSH_NOTICES": "https://cgayush.admissions.nic.in/notices/",
}

# WBMCC endpoints
WBMCC_URLS = {
    "WBMCC_MBBS_BDS_SCHEDULE": "https://wbmcc.nic.in/ug-medical-dental-eservices-schedule/",
    "WBMCC_MBBS_BDS_NOTICE": "https://wbmcc.nic.in/ug-medical-dental-notice-events/",
    "WBMCC_DOWNLOAD_SECTION": "https://wbmcc.nic.in/ug-medical-dental-counselling/",
    # AYUSH
    "WBMCC_AYUSH_SCHEDULE": "https://wbmcc.nic.in/ug-ayush-eservices-schedule/",
    "WBMCC_AYUSH_NOTICE": "https://wbmcc.nic.in/ug-ayush-notice-events/",
    "WBMCC_AYUSH_DOWNLOAD": "https://wbmcc.nic.in/ug-ayush-counselling/",
        # PG Medical (added)
    "WBMCC_PG_MEDICAL_SCHEDULE": "https://wbmcc.nic.in/pg-medical-counselling/",
    "WBMCC_PG_MEDICAL_NOTICE": "https://wbmcc.nic.in/pg-medical-notice-events/",
    "WBMCC_PG_MEDICAL_DOWNLOAD": "https://wbmcc.nic.in/pg-medical-counselling/",
    # PG Dental
    "WBMCC_PG_DENTAL_SCHEDULE": "https://wbmcc.nic.in/pg-dental-eservices-schedule/",
    "WBMCC_PG_DENTAL_NOTICE": "https://wbmcc.nic.in/pg-dental-notice-events/",
    "WBMCC_PG_DENTAL_DOWNLOAD": "https://wbmcc.nic.in/pg-dental-counselling/",

}

# -------------------------
# HELPERS
# -------------------------
def clean_filename(name: str) -> str:
    if not name:
        name = "unnamed_file"
    name = str(name).strip()
    name = re.sub(r'[<>:"/\\|?*]', "", name)
    name = re.sub(r"\s+", " ", name).strip()
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    return name


def best_anchor_name(a_tag, base_url=None) -> str:
    text = a_tag.get_text(" ", strip=True) or ""
    lower_text = text.lower()
    unhelpful_patterns = [
        "external site",
        "opens in a new window",
        "view pdf",
        "click here",
        "download",
    ]
    helpful = True
    for p in unhelpful_patterns:
        if p in lower_text:
            helpful = False
            break
    if text and helpful and len(text) > 2:
        return text.strip()

    b = a_tag.find("b")
    if b and b.get_text(strip=True):
        return b.get_text(" ", strip=True)

    td = a_tag.find_parent("td")
    if td:
        tdtxt = td.get_text(" ", strip=True)
        if tdtxt and len(tdtxt) > 3 and "external site" not in tdtxt.lower():
            return tdtxt.strip()

    prev_head = a_tag.find_previous(["h1", "h2", "h3", "h4"])
    if prev_head and prev_head.get_text(strip=True):
        return prev_head.get_text(" ", strip=True)

    href = a_tag.get("href", "") or ""
    if href:
        return os.path.basename(urlparse(href).path) or href

    return "unnamed_file"


def get_best_link_name(a_tag, base_url=None) -> str:
    title = a_tag.get("title") or a_tag.get("aria-label")
    if title and len(title.strip()) > 2 and "external site" not in title.lower():
        return title.strip()
    return best_anchor_name(a_tag, base_url=base_url)


# Old MCC-style naming
def get_best_link_name_mcc(a_tag, base_url=None) -> str:
    label = a_tag.get("aria-label") or a_tag.get("title")
    if label and label.strip():
        return label.strip()

    visible_text = a_tag.get_text(" ", strip=True)
    if visible_text and visible_text.strip():
        lower = visible_text.lower()
        if lower not in ["click here", "download", "view", "view pdf"]:
            return visible_text.strip()

    parent = a_tag.find_parent(["td", "div", "p", "li"])
    if parent:
        text = parent.get_text(" ", strip=True)
        if text:
            lower = text.lower()
            if lower not in ["click here", "download", "view", "view pdf"]:
                return text.strip()

    prev = a_tag.find_previous(string=True)
    if prev and prev.strip():
        return prev.strip()

    href = a_tag.get("href", "") or ""
    if href:
        return os.path.basename(urlparse(href).path) or "unnamed_file"

    return "unnamed_file"


# -------------------------
# PAGINATION
# -------------------------
@st.cache_data(ttl=3600)
def collect_paginated_urls(start_url, max_pages=MAX_PAGES_TO_CRAWL):
    try:
        parsed = urlparse(start_url)
        base = parsed.netloc
    except Exception:
        base = None
    seen = set()
    pages = []

    def fetch(u):
        try:
            r = requests.get(u, timeout=10)
            r.raise_for_status()
            return BeautifulSoup(r.text, "html.parser")
        except Exception:
            return None

    current = start_url
    for _ in range(max_pages):
        if not current or current in seen:
            break
        seen.add(current)
        pages.append(current)
        soup = fetch(current)
        if not soup:
            break
        next_a = soup.find("a", string=re.compile(r"next", re.I))
        if next_a and next_a.get("href"):
            nxt = urljoin(current, next_a["href"])
            if urlparse(nxt).netloc == base:
                current = nxt
                continue
        break
    return pages


# -------------------------
# GENERIC SCRAPERS
# -------------------------
def scrape_pdfs_from_pages(page_urls):
    file_links = []
    seen = set()

    def scrape_one(url):
        try:
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            out = []
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                if href.lower().endswith(".pdf") or "drive.google.com" in href.lower():
                    full = urljoin(url, href)
                    name = get_best_link_name(a, base_url=url)
                    out.append((full, name))
            return out
        except Exception:
            return []

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as ex:
        batches = ex.map(scrape_one, page_urls)

    for batch in batches:
        for full, name in batch:
            if full not in seen:
                seen.add(full)
                file_links.append((full, clean_filename(name)))
    return file_links


def scrape_pdfs_mcc(page_urls):
    file_links = []
    seen = set()

    def scrape_one(url):
        try:
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            out = []
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                if href.lower().endswith(".pdf") or "drive.google.com" in href.lower():
                    full = urljoin(url, href)
                    name = get_best_link_name_mcc(a, base_url=url)
                    out.append((full, name))
            return out
        except Exception:
            return []

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as ex:
        batches = ex.map(scrape_one, page_urls)

    for batch in batches:
        for full, name in batch:
            if full not in seen:
                seen.add(full)
                file_links.append((full, clean_filename(name)))
    return file_links


# -------------------------
# TELANGANA TABLE SCRAPER
# -------------------------
def scrape_pdfs_telangana(base_url, max_pages=MAX_PAGES_TO_CRAWL):
    out = []
    for p in range(1, max_pages + 1):
        page_url = re.sub(r"cpage=\d+", f"cpage={p}", base_url)
        try:
            r = requests.get(page_url, timeout=15)
            if r.status_code != 200:
                break
            soup = BeautifulSoup(r.text, "html.parser")

            tbodies = soup.find_all("tbody")
            if not tbodies:
                rows = soup.find_all("tr")
            else:
                rows = []
                for tb in tbodies:
                    rows.extend(tb.find_all("tr"))

            if not rows:
                break

            page_has_any = False

            for tr in rows:
                tds = tr.find_all("td")
                if len(tds) < 4:
                    continue

                title_td = tds[2]
                title_text = title_td.get_text(" ", strip=True)
                if not title_text:
                    continue

                dl_td = tds[3]
                a = dl_td.find("a", href=True)
                if not a:
                    continue
                href = a["href"].strip()
                if not href:
                    continue

                full_url = urljoin(page_url, href)
                out.append((full_url, clean_filename(title_text)))
                page_has_any = True

            if not page_has_any:
                break

        except Exception:
            continue

    seen = set()
    dedup = []
    for u, n in out:
        if u not in seen:
            seen.add(u)
            dedup.append((u, n))
    return dedup


# -------------------------
# Himachal
# -------------------------
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def _requests_session_with_retries(retries=3, backoff=0.5, status_forcelist=(429, 500, 502, 503, 504)):
    s = requests.Session()
    retries = Retry(total=retries, backoff_factor=backoff, status_forcelist=status_forcelist, allowed_methods=frozenset(['GET','HEAD']))
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.mount("http://", HTTPAdapter(max_retries=retries))
    # polite browser-like UA
    s.headers.update({"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"})
    return s

def scrape_pdfs_himachal_paginated(base_url, max_pages=41, pause=0.25):
    """
    Robust paginated scraper for amruhp.ac.in/notices using patterns like:
      /notices/page/1/, /notices/page/2/, ... /notices/page/N/
    Falls back to ?page=N and /?page=N patterns if needed.
    - max_pages: maximum pages to attempt (set to 41)
    - pause: seconds to sleep between requests (small polite delay)
    Returns list of (full_url, clean_filename)
    """
    session = _requests_session_with_retries()
    out = []
    seen = set()

    # Normalize base (ensure it doesn't end with a trailing slash for consistent formatting)
    base = base_url.rstrip('/')

    # candidate URL patterns in priority order
    patterns = [
        base + "/page/{p}/",    # https://amruhp.ac.in/notices/page/2/
        base + "/?page={p}",    # fallback
        base + "?page={p}",     # fallback
    ]

    for p in range(1, max_pages + 1):
        page_fetched = False
        page_html = None
        page_url_used = None

        for pat in patterns:
            url = pat.format(p=p)
            try:
                r = session.get(url, timeout=12)
                # treat 200 as success; 404 means stop trying this pattern for further pages only if early pages are 404
                if r.status_code == 200 and r.text:
                    page_html = r.text
                    page_url_used = url
                    page_fetched = True
                    break
                # if 403/429 etc, still try other patterns, but don't immediately bail
            except Exception:
                # keep trying other patterns
                continue

        if not page_fetched:
            # if page 1 not found, try base_url itself once (covers case where base page contains content)
            if p == 1:
                try:
                    r = session.get(base, timeout=12)
                    if r.status_code == 200 and r.text:
                        page_html = r.text
                        page_url_used = base
                        page_fetched = True
                except Exception:
                    pass

        if not page_fetched:
            # If we hit a sequence of missing pages (404s), it's safe to stop early.
            # We'll stop if this page and the previous page both had no content.
            # (You could relax this if the site has intermittent 404s.)
            # Here we simply break when we can't fetch current page.
            break

        # parse and extract PDFs from page_html
        try:
            soup = BeautifulSoup(page_html, "html.parser")

            # Primary heuristic: site uses blocks with class "et_pb_text_inner" (keeps previous logic)
            found_any = False
            for block in soup.find_all("div", class_="et_pb_text_inner"):
                for a in block.find_all("a", href=True):
                    href = a["href"].strip()
                    if not href:
                        continue
                    if href.lower().endswith(".pdf") or ".pdf" in href.lower() or "drive.google.com" in href.lower():
                        full = urljoin(page_url_used, href)
                        if full in seen:
                            continue
                        seen.add(full)
                        name = a.get_text(" ", strip=True) or get_best_link_name(a, base_url=page_url_used)
                        out.append((full, clean_filename(name)))
                        found_any = True

            # Secondary pass: collect PDFs in table rows or generic anchors (covers other layouts)
            if not found_any:
                for a in soup.find_all("a", href=True):
                    href = a["href"].strip()
                    if not href:
                        continue
                    if href.lower().endswith(".pdf") or ".pdf" in href.lower() or "drive.google.com" in href.lower():
                        full = urljoin(page_url_used, href)
                        if full in seen:
                            continue
                        seen.add(full)
                        name = a.get_text(" ", strip=True) or get_best_link_name(a, base_url=page_url_used)
                        out.append((full, clean_filename(name)))
                        found_any = True

        except Exception:
            # ignore parse errors for this page
            pass

        # polite pause
        time.sleep(pause)

    # final dedupe & return preserving order
    return out



# -------------------------
# JHARKHAND 2
# -------------------------


# -------------------------
# Bihar download-section
# -------------------------
def scrape_pdfs_bihar_download_section(base_url):
    out = []
    try:
        r = requests.get(base_url, timeout=12)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for h in soup.find_all("h3"):
            if "download section" in h.get_text(" ", strip=True).lower():
                parent = h.find_parent()
                if parent:
                    ul = parent.find("ul")
                    if ul:
                        for li in ul.find_all("li"):
                            a = li.find("a", href=True)
                            if a:
                                href = a["href"].strip()
                                name = a.get_text(" ", strip=True) or li.get_text(
                                    " ", strip=True
                                )
                                out.append(
                                    (urljoin(base_url, href), clean_filename(name))
                                )
                sib = h.find_next_sibling()
                while sib:
                    uls = sib.find_all("ul")
                    if uls:
                        for ul in uls:
                            for li in ul.find_all("li"):
                                a = li.find("a", href=True)
                                if a:
                                    href = a["href"].strip()
                                    name = a.get_text(
                                        " ", strip=True
                                    ) or li.get_text(" ", strip=True)
                                    out.append(
                                        (urljoin(base_url, href), clean_filename(name))
                                    )
                        break
                    sib = sib.find_next_sibling()
        if not out:
            td = soup.find(
                "td", attrs={"valign": "top", "width": re.compile(r"40%")}
            )
            if td:
                for a in td.find_all("a", href=True):
                    href = a["href"].strip()
                    name = a.get_text(" ", strip=True) or td.get_text(" ", strip=True)
                    out.append((urljoin(base_url, href), clean_filename(name)))
        seen = set()
        dedup = []
        for u, n in out:
            if u not in seen:
                seen.add(u)
                dedup.append((u, n))
        return dedup
    except Exception:
        return []


# -------------------------
# Chhattisgarh
# -------------------------
def scrape_pdfs_chhattisgarh_from_url(url):
    found = []
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for t in soup.find_all("table", class_="table"):
            h2 = t.find("h2")
            a = t.find("a", href=True)
            if a and (".pdf" in a["href"].lower() or "drive.google.com" in a["href"].lower()):
                name = (
                    h2.get_text(" ", strip=True)
                    if h2
                    else best_anchor_name(a, base_url=url)
                )
                found.append(
                    (urljoin(url, a["href"].strip()), clean_filename(name))
                )
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.lower().endswith(".pdf") or "drive.google.com" in href.lower():
                name = best_anchor_name(a, base_url=url)
                found.append((urljoin(url, href), clean_filename(name)))
    except Exception:
        return []
    seen = set()
    out = []
    for u, n in found:
        if u not in seen:
            seen.add(u)
            out.append((u, n))
    return out


def scrape_pdfs_chhattisgarh_combined():
    urls = [
        CHHATTISGARH_URLS["CH_GH_OR_CR"],
        CHHATTISGARH_URLS["CH_GH_SEAT_MATRIX"],
        CHHATTISGARH_URLS["CH_GH_MERIT_LISTS"],
        CHHATTISGARH_URLS["CH_GH_ALLOTMENT_LISTS"],
    ]
    results = []
    for u in urls:
        results.extend(scrape_pdfs_chhattisgarh_from_url(u))
    seen = set()
    out = []
    for u, n in results:
        if u not in seen:
            seen.add(u)
            out.append((u, n))
    return out


def scrape_pdfs_chhattisgarh_ayush_combined():
    urls = [
        CHHATTISGARH_URLS["CH_AYUSH_OR_CR"],
        CHHATTISGARH_URLS["CH_AYUSH_SEAT_MATRIX"],
        CHHATTISGARH_URLS["CH_AYUSH_MERIT_LISTS"],
    ]
    results = []
    for u in urls:
        results.extend(scrape_pdfs_chhattisgarh_from_url(u))
    seen = set()
    out = []
    for u, n in results:
        if u not in seen:
            seen.add(u)
            out.append((u, n))
    return out


# -------------------------
# WBMCC scrapers
# -------------------------
def scrape_pdfs_wbmcc_table_style(url):
    out = []
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        tables = soup.find_all("table")
        for t in tables:
            for a in t.find_all("a", href=True):
                href = a["href"].strip()
                if href.lower().endswith(".pdf") or "drive.google.com" in href.lower():
                    name = a.get_text(" ", strip=True)
                    if not name or "external site" in name.lower():
                        name = best_anchor_name(a, base_url=url)
                    out.append((urljoin(url, href), clean_filename(name)))
        seen = set()
        dedup = []
        for u, n in out:
            if u not in seen:
                seen.add(u)
                dedup.append((u, n))
        return dedup
    except Exception:
        return []
def scrape_pdfs_wbmcc_table_headers(url):
    """
    Look for tables that have headers like 'Title' and 'View / Download' and
    extract the PDF link and a user-friendly name (prefer the Title cell text).
    """
    out = []
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        tables = soup.find_all("table")
        for t in tables:
            # collect header text to identify target tables
            headers = " ".join([th.get_text(" ", strip=True).lower() for th in t.find_all("th")])
            if "title" in headers and ("view" in headers or "download" in headers):
                # iterate table rows
                for tr in t.find_all("tr"):
                    # prefer the first <a> in the row
                    a = tr.find("a", href=True)
                    if not a:
                        continue
                    href = a["href"].strip()
                    # only pdf-like targets
                    if not (href.lower().endswith(".pdf") or "drive.google.com" in href.lower() or href.startswith("http")):
                        continue
                    # get a user-friendly name: prefer the first <td> text (Title column)
                    td_title = tr.find("td")
                    name = td_title.get_text(" ", strip=True) if td_title else a.get_text(" ", strip=True)
                    # sanitize cases where aria/title says "External site..."
                    if not name or "external site" in name.lower() or len(name) < 3:
                        name = a.get("title") or a.get("aria-label") or os.path.basename(urlparse(href).path)
                    # strip trailing 'PDF 123 KB' noise
                    name = re.sub(r"\s*PDF\s*\d*\s*KB.*$", "", name, flags=re.I).strip()
                    out.append((urljoin(url, href), clean_filename(name)))
                # if we found any in this table, no need to scan further tables
                if out:
                    break
    except Exception:
        return []
    # dedupe preserving order
    seen = set()
    dedup = []
    for u, n in out:
        if u not in seen:
            seen.add(u)
            dedup.append((u, n))
    return dedup


def scrape_pdfs_wbmcc_download_section(url):
    out = []
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        candidates = []
        for h in soup.find_all("h3"):
            if "download" in h.get_text(" ", strip=True).lower():
                parent = h.find_parent()
                if parent:
                    candidates.append(parent)
                sib = h.find_next_sibling()
                steps = 0
                while sib and steps < 6:
                    candidates.append(sib)
                    sib = sib.find_next_sibling()
                    steps += 1
        if not candidates:
            candidates = [soup]
        for block in candidates:
            for a in block.find_all("a", href=True):
                href = a["href"].strip()
                if not (
                    href.lower().endswith(".pdf")
                    or "drive.google.com" in href.lower()
                ):
                    continue
                b = a.find("b")
                if b and b.get_text(strip=True):
                    name = b.get_text(" ", strip=True)
                else:
                    name = a.get_text(" ", strip=True) or best_anchor_name(
                        a, base_url=url
                    )
                    name = re.sub(r'^[\u2013\u2014\-\–\—\s]+', "", name).strip()
                out.append((urljoin(url, href), clean_filename(name)))
        seen = set()
        dedup = []
        for u, n in out:
            if u not in seen:
                seen.add(u)
                dedup.append((u, n))
        return dedup
    except Exception:
        return []


# -------------------------
# TRIPURA scrapers
# -------------------------
def scrape_pdfs_tripura_notice(url):
    out = []
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for tr in soup.find_all("tr"):
            a = tr.find("a", href=True)
            if not a:
                continue
            href = a["href"].strip()
            if not href.lower().endswith(".pdf"):
                continue
            name = a.get_text(" ", strip=True)
            out.append((urljoin(url, href), clean_filename(name)))
        seen = set()
        dedup = []
        for u, n in out:
            if u not in seen:
                seen.add(u)
                dedup.append((u, n))
        return dedup
    except Exception:
        return []


def scrape_pdfs_tripura_ug(url):
    out = []
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        target_headings = ["important notices", "seat matrix", "information", "schedule"]

        for h2 in soup.find_all("h2"):
            heading_text = h2.get_text(" ", strip=True).lower()
            if not any(t in heading_text for t in target_headings):
                continue

            parent_gen = h2.find_parent("div", class_=re.compile(r"\bgen-list\b"))
            container = parent_gen if parent_gen else h2

            for a in container.find_all("a", href=True):
                href = a["href"].strip()
                if not href:
                    continue
                if href.lower().endswith(".pdf") or "cdnbbsr.s3waas.gov.in" in href.lower():
                    name = a.get_text(" ", strip=True)
                    if not name:
                        name = get_best_link_name(a, base_url=url)
                    out.append((urljoin(url, href), clean_filename(name)))

        seen = set()
        dedup = []
        for u, n in out:
            if u not in seen:
                seen.add(u)
                dedup.append((u, n))
        return dedup

    except Exception:
        return []
def scrape_pdfs_tripura_paginated(base_url, max_pages=30):
    """
    Improved paginated scraper for Tripura UG counselling.

    Strategy:
    1. Fetch base_url and look for pagination anchors (nav, ul.pagination, div.pagination, links containing 'page' or digits).
    2. Normalize collected URLs and keep those that are on the same domain (or absolute).
    3. If no pagination anchors found, fall back to guessing ?page=N, ?cpage=N, /page/N/ patterns.
    4. Visit each collected page and extract PDFs (same rules as scrape_pdfs_tripura_ug).
    """
    out = []
    seen_urls = set()
    collected_page_urls = []

    def extract_pdfs_from_soup(soup, page_url):
        found = []
        target_headings = ["important notices", "seat matrix", "information", "schedule"]

        # same logic as scrape_pdfs_tripura_ug but applied to the given soup
        for h2 in soup.find_all("h2"):
            heading_text = h2.get_text(" ", strip=True).lower()
            if not any(t in heading_text for t in target_headings):
                continue

            parent_gen = h2.find_parent("div", class_=re.compile(r"\bgen-list\b"))
            container = parent_gen if parent_gen else h2

            for a in container.find_all("a", href=True):
                href = a["href"].strip()
                if not href:
                    continue
                if href.lower().endswith(".pdf") or "cdnbbsr.s3waas.gov.in" in href.lower():
                    full = urljoin(page_url, href)
                    if full not in seen_urls:
                        seen_urls.add(full)
                        name = a.get_text(" ", strip=True) or get_best_link_name(a, base_url=page_url)
                        found.append((full, clean_filename(name)))
        return found

    # --- Step 1: fetch base page and look for pagination links ---
    try:
        r = requests.get(base_url, timeout=12)
        r.raise_for_status()
        base_soup = BeautifulSoup(r.text, "html.parser")
    except Exception:
        base_soup = None

    if base_soup:
        # gather pagination anchors from likely containers
        candidates = set()

        # 1) explicit nav / pagination lists
        for sel in ["nav", "ul.pagination", "ol.pagination", "div.pagination", "div.paging", "div.paginate"]:
            for node in base_soup.select(sel):
                for a in node.find_all("a", href=True):
                    candidates.add(urljoin(base_url, a["href"].strip()))

        # 2) any anchor whose text looks like a page number or contains 'page' or 'next' / 'prev'
        for a in base_soup.find_all("a", href=True):
            txt = (a.get_text(" ", strip=True) or "").strip().lower()
            href = a["href"].strip()
            if not href:
                continue
            # heuristics: numeric text "1", "2", "3", "page 2", "next", "prev"
            if re.search(r"^\d+$", txt) or "page" in txt or re.search(r"next|prev|older|newer", txt):
                candidates.add(urljoin(base_url, href))
            # sometimes the href contains 'page=' or '/page/'
            elif re.search(r"page=\d+|/page/\d+", href, re.I):
                candidates.add(urljoin(base_url, href))

        # Normalize and filter candidates: same domain and unique
        parsed_base = urlparse(base_url)
        for u in candidates:
            try:
                up = urlparse(u)
                # keep if same netloc OR absolute http(s)
                if not up.scheme:
                    u = urljoin(base_url, u)
                    up = urlparse(u)
                # optionally restrict to same domain to avoid external links
                if up.netloc == parsed_base.netloc:
                    collected_page_urls.append(u)
            except Exception:
                continue

    # Always include the base page itself (first)
    if base_url not in collected_page_urls:
        collected_page_urls.insert(0, base_url)

    # If we didn't find any extra pages, fallback to numeric guesses
    if len(collected_page_urls) <= 1:
        # try candidate patterns and test response status
        tried = []
        for p in range(1, min(max_pages, 12) + 1):
            guesses = [
                f"{base_url.rstrip('/')}/?page={p}",
                f"{base_url.rstrip('/')}/?cpage={p}",
                f"{base_url.rstrip('/')}/page/{p}/",
                f"{base_url.rstrip('/')}/?p={p}",
            ]
            for cand in guesses:
                if cand in tried:
                    continue
                tried.append(cand)
                try:
                    rr = requests.head(cand, timeout=8, allow_redirects=True)
                    status = getattr(rr, "status_code", None)
                    if status == 200:
                        # prefer GET for full HTML later, but keep the URL
                        collected_page_urls.append(cand)
                except Exception:
                    # try GET directly if HEAD fails (some servers don't allow HEAD)
                    try:
                        rr2 = requests.get(cand, timeout=10)
                        if rr2.status_code == 200 and rr2.text:
                            collected_page_urls.append(cand)
                    except Exception:
                        continue
        # ensure base first and dedupe while preserving order
        seen_p = set()
        ordered = []
        for u in ([base_url] + collected_page_urls):
            if u not in seen_p:
                seen_p.add(u)
                ordered.append(u)
        collected_page_urls = ordered

    # Deduplicate and limit pages
    final_pages = []
    seen_p = set()
    for u in collected_page_urls:
        if u and u not in seen_p:
            seen_p.add(u)
            final_pages.append(u)
            if len(final_pages) >= max_pages:
                break

    # DEBUG: show which pages we'll visit (uncomment for debugging)
    # st.write("Tripura pages to visit:", final_pages)

    # --- Step 2: visit each page and collect PDFs ---
    for page_url in final_pages:
        try:
            r = requests.get(page_url, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            found = extract_pdfs_from_soup(soup, page_url)
            # also scan table rows / generic anchors on that page as a secondary pass
            if not found:
                # secondary generic scan for anchors that point to PDFs
                for a in soup.find_all("a", href=True):
                    href = a["href"].strip()
                    if href.lower().endswith(".pdf"):
                        full = urljoin(page_url, href)
                        if full not in seen_urls:
                            seen_urls.add(full)
                            name = a.get_text(" ", strip=True) or get_best_link_name(a, base_url=page_url)
                            found.append((full, clean_filename(name)))
            # append found
            if found:
                out.extend(found)
        except Exception:
            # ignore single page failures; continue with others
            continue

    # final dedupe preserving order
    seen_final = set()
    dedup = []
    for u, n in out:
        if u not in seen_final:
            seen_final.add(u)
            dedup.append((u, n))
    return dedup


# -------------------------
# ANDHRA PRADESH helpers
# -------------------------
def build_andhra_bulletin_url(base_url: str, row_id: str) -> str:
    parsed = urlparse(base_url)
    path = parsed.path or "/"
    lower_path = path.lower()
    if lower_path.endswith("/home/home"):
        new_path = re.sub(r"(?i)/home/home$", "/Home/Bulletinopen", path)
    elif lower_path.endswith("/home"):
        new_path = re.sub(r"(?i)/home$", "/Home/Bulletinopen", path)
    else:
        if path.endswith("/"):
            new_path = path + "Home/Bulletinopen"
        else:
            new_path = path + "/Home/Bulletinopen"
    new_query = f"RowId={row_id}"
    new_url = parsed._replace(path=new_path, query=new_query).geturl()
    return new_url


def scrape_pdfs_andhra_openfile(base_url: str):
    out = []
    try:
        r = requests.get(base_url, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        for a in soup.find_all("a"):
            onclick = a.get("onclick", "") or ""
            m = re.search(r"OpenFile\((\d+)\)", onclick)
            if not m:
                continue
            row_id = m.group(1)
            bulletin_url = build_andhra_bulletin_url(base_url, row_id)
            name = a.get_text(" ", strip=True)
            if not name:
                name = f"Bulletin_{row_id}"
            out.append((bulletin_url, clean_filename(name)))

        seen = set()
        dedup = []
        for u, n in out:
            if u not in seen:
                seen.add(u)
                dedup.append((u, n))
        return dedup

    except Exception:
        return []


# -------------------------
# AACCC scrapers (FIXED SECTION)
# -------------------------
def scrape_pdfs_aaccc(base_url):
    """
    Fixed AACCC scraper: finds the table with Year / View / Download columns and extracts:
      - link href (PDF)
      - link visible text as the PDF name (e.g. 'Final Result of AACCC UG SVR 2 A.Y. 2025-26')
    Returns list of (full_url, clean_name)
    """
    out = []
    try:
        r = requests.get(base_url, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Prefer tables that have 'Year' and 'View / Download' headers nearby
        tables = soup.find_all("table")
        candidate_tables = []
        for t in tables:
            headers = " ".join([th.get_text(" ", strip=True).lower() for th in t.find_all("th")])
            if "year" in headers and ("view" in headers or "download" in headers):
                candidate_tables.append(t)

        # fallback: look for tbody with the pattern shown by user
        if not candidate_tables:
            tbodies = soup.find_all("tbody")
            for tb in tbodies:
                # simple heuristic: does tbody contain <a ... .pdf> links?
                if tb.find("a", href=re.compile(r"\.pdf$", re.I)):
                    candidate_tables.append(tb)

        for container in candidate_tables:
            rows = container.find_all("tr")
            for tr in rows:
                # find anchor in the row (first column)
                a = tr.find("a", href=True)
                if not a:
                    continue
                href = a["href"].strip()
                if not href:
                    continue
                # Make absolute URL
                full = urljoin(base_url, href)
                # Use visible link text as PDF name (exactly as user requested)
                name_text = a.get_text(" ", strip=True)
                # Fallback: try aria-label or title if visible text empty
                if not name_text:
                    name_text = a.get("aria-label") or a.get("title") or os.path.basename(urlparse(href).path)
                # Trim trailing 'PDF' note if present in aria-label/title (keeps readable name)
                name_text = re.sub(r"\s*PDF\s*\d*\s*KB.*$", "", name_text, flags=re.I).strip()
                out.append((full, clean_filename(name_text)))
            if out:
                break  # stop after first good table/container

    except Exception:
        return []

    # dedupe preserving order
    seen = set()
    dedup = []
    for u, n in out:
        if u not in seen:
            seen.add(u)
            dedup.append((u, n))
    return dedup


# -------------------------
# KERALA KEAM ALLOTMENT SCRAPER
# -------------------------
def scrape_pdfs_kerala_allotlist(url):
    """
    Kerala KEAM Allotment Lists page:
    Sections like:
      Medical (MBBS/BDS)
      Medical (AYUSH/Allied)
      B.Pharm
      Engineering
    Each has a bullet list with links like "Stray Vacancy Filling Allotment".
    We name files as:
      "<Course Label> - <Link Text>.pdf"
    """
    out = []
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        course_labels = [
            "Medical (MBBS/BDS)",
            "Medical (AYUSH/Allied)",
            "B.Pharm",
            "Engineering",
        ]

        for label in course_labels:
            pattern = re.compile(re.escape(label), re.I)
            for node in soup.find_all(string=pattern):
                parent = node.parent
                if not parent:
                    continue

                # climb up a little to find container with <ul>
                container = parent
                for _ in range(4):
                    if container.find("ul"):
                        break
                    if container.parent:
                        container = container.parent
                    else:
                        break

                ul = container.find("ul")
                if not ul:
                    ul = parent.find_next("ul")
                if not ul:
                    continue

                for a in ul.find_all("a", href=True):
                    href = a["href"].strip()
                    if not href:
                        continue
                    full = urljoin(url, href)
                    title = a.get_text(" ", strip=True) or "Allotment"
                    name = f"{label} - {title}"
                    out.append((full, clean_filename(name)))

        # dedupe
        seen = set()
        dedup = []
        for u, n in out:
            if u not in seen:
                seen.add(u)
                dedup.append((u, n))
        return dedup

    except Exception:
        return []


# Replace your current download_and_zip(...) with this function

def download_and_zip(selected_links, max_name_len=100):
    """
    Downloads URLs and writes them into an in-memory ZIP.
    Ensures filenames are sanitized, truncated and unique to avoid Windows 'path too long' extraction errors.
    max_name_len: maximum filename length including extension (choose <= 100 for safety).
    """
    buffer = io.BytesIO()
    total = max(len(selected_links), 1)
    progress = st.progress(0)

    def sanitize_and_shorten(name, max_len):
        # remove any path parts and backslashes/slashes
        name = name.split("/")[-1].split("\\")[-1]
        # replace spaces with underscore, remove invalid chars
        name = re.sub(r'[<>:"/\\|?*]', "", name)
        name = re.sub(r"\s+", "_", name).strip()
        if not name:
            name = "file"
        # ensure an extension (if none assume .pdf)
        base, ext = os.path.splitext(name)
        if not ext:
            ext = ".pdf"
        # truncate base if necessary to keep total length <= max_len
        max_base = max_len - len(ext)
        if max_base < 6:
            # extremely small max_len safeguard
            max_base = 6
        if len(base) > max_base:
            base = base[:max_base]
        return f"{base}{ext}"

    used = {}  # map sanitized_name -> count for uniqueness

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for i, (url, name) in enumerate(selected_links):
            # create a safe filename candidate
            candidate = name or f"file_{i+1}.pdf"
            candidate = sanitize_and_shorten(candidate, max_name_len)

            # ensure uniqueness inside zip (append _1, _2 ...)
            if candidate in used:
                used[candidate] += 1
                base, ext = os.path.splitext(candidate)
                # ensure suffix doesn't push over max length
                suffix = f"_{used[candidate]}"
                max_base_len = max_name_len - len(ext) - len(suffix)
                base_short = base[:max_base_len] if len(base) > max_base_len else base
                safe_name = f"{base_short}{suffix}{ext}"
            else:
                used[candidate] = 0
                safe_name = candidate

            try:
                r = requests.get(url, stream=True, timeout=30)
                if r.status_code == 200 and r.content:
                    # Write bytes into zip using only the safe filename (no directories)
                    zipf.writestr(safe_name, r.content)
                else:
                    zipf.writestr(
                        f"{safe_name}_ERROR.txt",
                        f"Failed to download {url} (status {getattr(r, 'status_code', 'N/A')})",
                    )
            except Exception as e:
                zipf.writestr(
                    f"{safe_name}_ERROR.txt",
                    f"Error: {e}\nURL: {url}",
                )

            progress.progress((i + 1) / total)

    buffer.seek(0)
    return buffer



# -------------------------
# STREAMLIT UI + PASSWORD
# -------------------------
st.set_page_config(page_title="⚡NEET PDF Extractor", layout="centered")


def check_password():
    def password_entered():
        if st.session_state["password_input"] == "jarvis":
            st.session_state["password_correct"] = True
            del st.session_state["password_input"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input(
            "Enter password:",
            type="password",
            key="password_input",
            on_change=password_entered,
        )
        return False

    if not st.session_state["password_correct"]:
        st.text_input(
            "Enter password:",
            type="password",
            key="password_input",
            on_change=password_entered,
        )
        st.error("Incorrect password. Try again.")
        return False

    return True


if not check_password():
    st.stop()

st.title("NEET PDF Extractor")

# -------------------------
# WBMCC TOP SECTION
# -------------------------
st.markdown("## 🔷 WBMCC")
w1, w2, w3, w4 = st.columns(4)
selected_site_name = None
selected_site_url = None

with w1:
    if st.button("🕒 WBMCC MBBS & BDS SCHEDULE"):
        selected_site_name = "WBMCC_MBBS_BDS_SCHEDULE"
        selected_site_url = WBMCC_URLS["WBMCC_MBBS_BDS_SCHEDULE"]
    if st.button("📘 WBMCC AYUSH SCHEDULE"):
        selected_site_name = "WBMCC_AYUSH_SCHEDULE"
        selected_site_url = WBMCC_URLS["WBMCC_AYUSH_SCHEDULE"]
with w2:
    if st.button("📰 WBMCC MBBS & BDS NOTICE"):
        selected_site_name = "WBMCC_MBBS_BDS_NOTICE"
        selected_site_url = WBMCC_URLS["WBMCC_MBBS_BDS_NOTICE"]
    if st.button("📰 WBMCC AYUSH NOTICE"):
        selected_site_name = "WBMCC_AYUSH_NOTICE"
        selected_site_url = WBMCC_URLS["WBMCC_AYUSH_NOTICE"]
with w3:
    if st.button("📥 WBMCC DOWNLOAD SECTION"):
        selected_site_name = "WBMCC_DOWNLOAD_SECTION"
        selected_site_url = WBMCC_URLS["WBMCC_DOWNLOAD_SECTION"]
    if st.button("📥 WBMCC AYUSH DOWNLOAD SECTION"):
        selected_site_name = "WBMCC_AYUSH_DOWNLOAD"
        selected_site_url = WBMCC_URLS["WBMCC_AYUSH_DOWNLOAD"]
with w4:
        # put under the existing buttons in whichever column suits your layout
    if st.button("🕒 WBMCC PG MEDICAL SCHEDULE"):
        selected_site_name = "WBMCC_PG_MEDICAL_SCHEDULE"
        selected_site_url = WBMCC_URLS["WBMCC_PG_MEDICAL_SCHEDULE"]
    if st.button("📰 WBMCC PG MEDICAL NOTICE"):
        selected_site_name = "WBMCC_PG_MEDICAL_NOTICE"
        selected_site_url = WBMCC_URLS["WBMCC_PG_MEDICAL_NOTICE"]
    if st.button("📥 WBMCC PG MEDICAL DOWNLOAD SECTION"):
        selected_site_name = "WBMCC_PG_MEDICAL_DOWNLOAD"
        selected_site_url = WBMCC_URLS["WBMCC_PG_MEDICAL_DOWNLOAD"]
    # PG Dental (new)
    if st.button("🕒 WBMCC PG DENTAL SCHEDULE"):
        selected_site_name = "WBMCC_PG_DENTAL_SCHEDULE"
        selected_site_url = WBMCC_URLS["WBMCC_PG_DENTAL_SCHEDULE"]
    if st.button("📰 WBMCC PG DENTAL NOTICE"):
        selected_site_name = "WBMCC_PG_DENTAL_NOTICE"
        selected_site_url = WBMCC_URLS["WBMCC_PG_DENTAL_NOTICE"]
    if st.button("📥 WBMCC PG DENTAL DOWNLOAD SECTION"):
        selected_site_name = "WBMCC_PG_DENTAL_DOWNLOAD"
        selected_site_url = WBMCC_URLS["WBMCC_PG_DENTAL_DOWNLOAD"]


st.markdown("---")

# -------------------------
# AACCC block
# -------------------------
st.markdown("## 🔷 AACCC (UG / PG)")
aac1, aac2 = st.columns(2)
with aac1:
    if st.button("🌐 AACCC CURRENT EVENTS (UG)"):
        selected_site_name = "AACCC CURRENT EVENTS (UG)"
        selected_site_url = NEET_SITES[selected_site_name]
    if st.button("📰 AACCC NEWS & EVENTS (UG)"):
        selected_site_name = "AACCC NEWS & EVENTS (UG)"
        selected_site_url = NEET_SITES["AACCC NEWS & EVENTS (UG)"]
with aac2:
    if st.button("🏥 AACCC CURRENT EVENTS (PG)"):
        selected_site_name = "AACCC CURRENT EVENTS (PG)"
        selected_site_url = NEET_SITES[selected_site_name]
    if st.button("📰 AACCC NEWS & EVENTS (PG)"):
        selected_site_name = "AACCC NEWS & EVENTS (PG)"
        selected_site_url = NEET_SITES["AACCC NEWS & EVENTS (PG)"]

st.markdown("---")

# -------------------------
# BIHAR block
# -------------------------
st.markdown("## 🔶 BIHAR")
b1, b2, b3 = st.columns(3)
with b1:
    if st.button("📥 BIHAR DOWNLOAD SECTION (Home)"):
        selected_site_name = "BIHAR DOWNLOAD"
        selected_site_url = NEET_SITES["BIHAR HOME"]
    if st.button("📘 BIHAR UGMAC NOTICE"):
        selected_site_name = "BIHAR UGMAC NOTICE"
        selected_site_url = NEET_SITES["BIHAR UGMAC NOTICE"]
with b2:
    if st.button("🧾 BIHAR UGAYUSH NOTICE"):
        selected_site_name = "BIHAR UGAYUSH NOTICE"
        selected_site_url = NEET_SITES["BIHAR UGAYUSH NOTICE"]
    if st.button("📄 BIHAR PGMAC NOTICE"):
        selected_site_name = "BIHAR PGMAC NOTICE"
        selected_site_url = NEET_SITES["BIHAR PGMAC NOTICE"]
with b3:
    if st.button("🔔 BIHAR PGAYUSH NOTICE"):
        selected_site_name = "BIHAR PGAYUSH NOTICE"
        selected_site_url = NEET_SITES["BIHAR PGAYUSH NOTICE"]

st.markdown("---")

# -------------------------
# ANDHRA PRADESH block
# -------------------------
st.markdown("## 🟣 ANDHRA PRADESH")
ap_col1, ap_col2 = st.columns(2)
with ap_col1:
    if st.button("🏥 ANDHRA PRADESH MBBS CQ"):
        selected_site_name = "ANDHRA PRADESH MBBS CQ"
        selected_site_url = NEET_SITES["ANDHRA PRADESH MBBS CQ"]
    if st.button("🏥 ANDHRA PRADESH MBBS MQ"):
        selected_site_name = "ANDHRA PRADESH MBBS MQ"
        selected_site_url = NEET_SITES["ANDHRA PRADESH MBBS MQ"]
    if st.button("🎓 ANDHRA PRADESH MEDICAL PG CQ"):
        selected_site_name = "ANDHRA PRADESH MEDICAL PG CQ"
        selected_site_url = NEET_SITES["ANDHRA PRADESH MEDICAL PG CQ"]
with ap_col2:
    if st.button("🌿 ANDHRA PRADESH AYUSH CQ"):
        selected_site_name = "ANDHRA PRADESH AYUSH CQ"
        selected_site_url = NEET_SITES["ANDHRA PRADESH AYUSH CQ"]
    if st.button("🌿 ANDHRA PRADESH AYUSH AIQ"):
        selected_site_name = "ANDHRA PRADESH AYUSH AIQ"
        selected_site_url = NEET_SITES["ANDHRA PRADESH AYUSH AIQ"]
    if st.button("🌿 ANDHRA PRADESH AYUSH MQ"):
        selected_site_name = "ANDHRA PRADESH AYUSH MQ"
        selected_site_url = NEET_SITES["ANDHRA PRADESH AYUSH MQ"]

st.markdown("---")

# -------------------------
# ODISHA
# -------------------------
st.markdown("## 🟠 ODISHA")
od1, od2, od3 = st.columns(3)

with od1:
    if st.button("📢 ODISHA PUBLIC NOTICE (MBBS & BDS)"):
        selected_site_name = "ODISHA PUBLIC NOTICE (MBBS & BDS)"
        selected_site_url = NEET_SITES[selected_site_name]

with od2:
    if st.button("📘 ODISHA MBBS & BDS INFORMATION"):
        selected_site_name = "ODISHA MBBS & BDS INFORMATION"
        selected_site_url = NEET_SITES[selected_site_name]

with od3:
    if st.button("🩺 ODISHA BAMS & BHMS"):
        selected_site_name = "ODISHA BAMS & BHMS"
        selected_site_url = NEET_SITES[selected_site_name]

st.markdown("---")

# -------------------------
# STATES & OTHERS
# -------------------------
st.markdown("## 🏛 States & Others")
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("🏛 RAJASTHAN"):
        selected_site_name = "RAJASTHAN"
        selected_site_url = NEET_SITES["RAJASTHAN"]
    if st.button("🌇 TELANGANA (KNRUHS)"):
        selected_site_name = "TELANGANA (KNRUHS)"
        selected_site_url = NEET_SITES["TELANGANA (KNRUHS)"]
    if st.button("🏥 MAHARASHTRA UG"):
        selected_site_name = "MAHARASHTRA UG"
        selected_site_url = NEET_SITES["MAHARASHTRA UG"]
    if st.button("🏥 MAHARASHTRA PG"):
        selected_site_name = "MAHARASHTRA PG"
        selected_site_url = NEET_SITES["MAHARASHTRA PG"]
    if st.button("🏥 HARYANA UG"):
        selected_site_name = "HARYANA UG"
        selected_site_url = NEET_SITES["HARYANA UG"]
    
with c2:
    if st.button("🏔 HIMACHAL PRADESH (AMRUHP)"):
        selected_site_name = "HIMACHAL PRADESH (AMRUHP)"
        selected_site_url = NEET_SITES["HIMACHAL PRADESH (AMRUHP)"]
    if st.button("📂 JHARKHAND"):
        selected_site_name = "JHARKHAND"
        selected_site_url = NEET_SITES["JHARKHAND"]
    if st.button("PONDICHERRY"):
        selected_site_name = "PONDICHERRY"
        selected_site_url = NEET_SITES["PONDICHERRY"]
    if st.button("PUNJAB MBBS & BDS"):
        selected_site_name = "PUNJAB MBBS & BDS"
        selected_site_url = NEET_SITES["PUNJAB MBBS & BDS"]
    if st.button("TAMIL NADU AYUSH"):
        selected_site_name = "TAMIL NADU AYUSH"
        selected_site_url = NEET_SITES["TAMIL NADU AYUSH"]
with c3:
    if st.button("📝 SIKKIM NOTICES"):
        selected_site_name = "SIKKIM NOTICES"
        selected_site_url = NEET_SITES["SIKKIM NOTICES"]
    if st.button("📊 TRIPURA UG COUNSELLING IMPORTANT NOTICE"):
        selected_site_name = "TRIPURA UG COUNSELLING"
        selected_site_url = NEET_SITES["TRIPURA UG COUNSELLING"]
    if st.button("📜 TRIPURA PG COUNSELLING IMPORTANT NOTICE"):
        selected_site_name = "TRIPURA PG COUNSELLING"
        selected_site_url = NEET_SITES["TRIPURA PG COUNSELLING"]
    if st.button("📋 KERALA ALLOTMENT LISTS"):
        selected_site_name = "KERALA ALLOTMENT LISTS"
        selected_site_url = NEET_SITES["KERALA ALLOTMENT LISTS"]

st.markdown("---")

# -------------------------
# CHHATTISGARH block
# -------------------------
st.markdown("## 🟢 CHHATTISGARH")
ch1, ch2, ch3 = st.columns(3)
with ch1:
    if st.button("🗂 CH_GH Combined (OR-CR / Seat / Merit / Allotment)"):
        selected_site_name = "CH_GH_COMBINED"
        selected_site_url = "CH_GH_COMBINED"
    if st.button("🟢 CH_AYUSH Combined (OR-CR / Seat / Merit)"):
        selected_site_name = "CH_AYUSH_COMBINED"
        selected_site_url = "CH_AYUSH_COMBINED"
with ch2:
    if st.button("🕒 CH_GH SCHEDULE"):
        selected_site_name = "CH_GH_SCHEDULE"
        selected_site_url = CHHATTISGARH_URLS["CH_GH_SCHEDULE"]
    if st.button("🕒 CH_AYUSH SCHEDULE"):
        selected_site_name = "CH_AYUSH_SCHEDULE"
        selected_site_url = CHHATTISGARH_URLS["CH_AYUSH_SCHEDULE"]
with ch3:
    if st.button("📢 CH_GH NOTICES"):
        selected_site_name = "CH_GH_NOTICES"
        selected_site_url = CHHATTISGARH_URLS["CH_GH_NOTICES"]
    if st.button("📢 CH_AYUSH NOTICES"):
        selected_site_name = "CH_AYUSH_NOTICES"
        selected_site_url = CHHATTISGARH_URLS["CH_AYUSH_NOTICES"]

st.markdown("---")

# -------------------------
# MCC block
# -------------------------
st.markdown("## 🔵 MCC")
m1, m2, m3 = st.columns(3)
with m1:
    if st.button("📘 MCC UG SCHEDULE"):
        selected_site_name = "MCC SCHEDULES (UG)"
        selected_site_url = NEET_SITES["MCC SCHEDULES (UG)"]
    if st.button("📰 MCC UG NEWS"):
        selected_site_name = "MCC NEWS & EVENTS (UG)"
        selected_site_url = NEET_SITES["MCC NEWS & EVENTS (UG)"]
    if st.button("📢 MCC UG CURRENT EVENTS"):
        selected_site_name = "MCC CURRENT EVENTS (UG)"
        selected_site_url = NEET_SITES["MCC CURRENT EVENTS (UG)"]
with m2:
    if st.button("📘 MCC MDS SCHEDULE"):
        selected_site_name = "MCC MDS SCHEDULE"
        selected_site_url = NEET_SITES["MCC MDS SCHEDULE"]
    if st.button("📰 MCC MDS NEWS"):
        selected_site_name = "MCC MDS NEWS AND EVENTS"
        selected_site_url = NEET_SITES["MCC MDS NEWS AND EVENTS"]
    if st.button("📢 MCC MDS CURRENT EVENTS"):
        selected_site_name = "MCC MDS CURRENT EVENTS"
        selected_site_url = NEET_SITES["MCC MDS CURRENT EVENTS"]
with m3:
    if st.button("📘 MCC PG SCHEDULE"):
        selected_site_name = "MCC PG SCHEDULE"
        selected_site_url = NEET_SITES["MCC PG SCHEDULE"]
    if st.button("📰 MCC PG NEWS"):
        selected_site_name = "MCC PG NEWS AND EVENTS"
        selected_site_url = NEET_SITES["MCC PG NEWS AND EVENTS"]
    if st.button("📢 MCC PG CURRENT EVENTS"):
        selected_site_name = "MCC PG CURRENT EVENTS"
        selected_site_url = NEET_SITES["MCC PG CURRENT EVENTS"]

st.markdown("---")

# -------------------------
# Manual URL
# -------------------------
manual_url = st.text_input("🔗 Paste custom URL (optional):", key="manual_url_input")
if st.button("Use Manual URL"):
    if manual_url.strip():
        selected_site_name = "Manual"
        selected_site_url = manual_url.strip()
    else:
        st.warning("Please paste a URL first.")

# -------------------------
# MAIN SCRAPING LOGIC
# -------------------------
if "selected_site_url" in locals() and selected_site_url:
    st.info(f"Fetching: {selected_site_name} — {selected_site_url}")
    with st.spinner("Collecting pages..."):
        single_page_keys = {
            "TELANGANA (KNRUHS)",
            "WBMCC_MBBS_BDS_SCHEDULE",
            "WBMCC_MBBS_BDS_NOTICE",
            "WBMCC_DOWNLOAD_SECTION",
            "WBMCC_AYUSH_SCHEDULE",
            "WBMCC_AYUSH_NOTICE",
            "WBMCC_AYUSH_DOWNLOAD",
            "SIKKIM NOTICES",
            "ANDHRA PRADESH MBBS CQ",
            "ANDHRA PRADESH MBBS MQ",
            "ANDHRA PRADESH MEDICAL PG CQ",
            "ANDHRA PRADESH AYUSH CQ",
            "ANDHRA PRADESH AYUSH AIQ",
            "ANDHRA PRADESH AYUSH MQ",
            "KERALA ALLOTMENT LISTS",
            "WBMCC_PG_MEDICAL_SCHEDULE",
            "WBMCC_PG_MEDICAL_NOTICE",
            "WBMCC_PG_MEDICAL_DOWNLOAD",
            "WBMCC_PG_DENTAL_SCHEDULE",
            "WBMCC_PG_DENTAL_NOTICE",
            "WBMCC_PG_DENTAL_DOWNLOAD",

            "Manual",
        }
        if selected_site_name in single_page_keys or selected_site_url in (
            "CH_GH_COMBINED",
            "CH_AYUSH_COMBINED",
        ):
            pages = (
                [selected_site_url]
                if selected_site_url not in ("CH_GH_COMBINED", "CH_AYUSH_COMBINED")
                else []
            )
        else:
            pages = collect_paginated_urls(selected_site_url)
    st.success(f"Collected {len(pages)} page(s).")

    with st.spinner("Extracting PDF links..."):
        file_links = []

        # WBMCC
        if selected_site_name == "WBMCC_MBBS_BDS_SCHEDULE":
            file_links = scrape_pdfs_wbmcc_table_style(selected_site_url)
        elif selected_site_name == "WBMCC_MBBS_BDS_NOTICE":
            file_links = scrape_pdfs_wbmcc_table_style(selected_site_url)
        elif selected_site_name == "WBMCC_DOWNLOAD_SECTION":
            file_links = scrape_pdfs_wbmcc_download_section(selected_site_url)
        elif selected_site_name == "WBMCC_AYUSH_SCHEDULE":
            file_links = scrape_pdfs_wbmcc_table_style(selected_site_url)
        elif selected_site_name == "WBMCC_AYUSH_NOTICE":
            file_links = scrape_pdfs_wbmcc_table_style(selected_site_url)
        elif selected_site_name == "WBMCC_AYUSH_DOWNLOAD":
            file_links = scrape_pdfs_wbmcc_download_section(selected_site_url)
        elif selected_site_name == "WBMCC_PG_MEDICAL_SCHEDULE":
            # first try the header-table parser (best for Title / View / Download tables)
            file_links = scrape_pdfs_wbmcc_table_headers(selected_site_url)
            # fallback: older table-style parser, then a generic page scan
            if not file_links:
                file_links = scrape_pdfs_wbmcc_table_style(selected_site_url)
            if not file_links:
                file_links = scrape_pdfs_from_pages([selected_site_url])

        elif selected_site_name == "WBMCC_PG_MEDICAL_NOTICE":
            # notices use the same table pattern
            file_links = scrape_pdfs_wbmcc_table_headers(selected_site_url)
            if not file_links:
                file_links = scrape_pdfs_wbmcc_table_style(selected_site_url)
            if not file_links:
                file_links = scrape_pdfs_from_pages([selected_site_url])

        elif selected_site_name == "WBMCC_PG_MEDICAL_DOWNLOAD":
            # download-section first, then table headers, then generic
            file_links = scrape_pdfs_wbmcc_download_section(selected_site_url)
            if not file_links:
                file_links = scrape_pdfs_wbmcc_table_headers(selected_site_url)
            if not file_links:
                file_links = scrape_pdfs_from_pages([selected_site_url])
        elif selected_site_name == "WBMCC_PG_DENTAL_SCHEDULE":
            file_links = scrape_pdfs_wbmcc_table_headers(selected_site_url)
            if not file_links:
                file_links = scrape_pdfs_wbmcc_table_style(selected_site_url)
                if not file_links:
                    file_links = scrape_pdfs_from_pages([selected_site_url])
        elif selected_site_name == "WBMCC_PG_DENTAL_NOTICE":
            file_links = scrape_pdfs_wbmcc_table_headers(selected_site_url)
            if not file_links:
              file_links = scrape_pdfs_wbmcc_table_style(selected_site_url)
              if not file_links:
                 file_links = scrape_pdfs_from_pages([selected_site_url])

        elif selected_site_name == "WBMCC_PG_DENTAL_DOWNLOAD":
            file_links = scrape_pdfs_wbmcc_download_section(selected_site_url)
            if not file_links:
                file_links = scrape_pdfs_wbmcc_table_headers(selected_site_url)
                if not file_links:
                    file_links = scrape_pdfs_from_pages([selected_site_url])

        # CHHATTISGARH
        elif selected_site_name == "CH_GH_COMBINED":
            file_links = scrape_pdfs_chhattisgarh_combined()
        elif selected_site_name == "CH_AYUSH_COMBINED":
            file_links = scrape_pdfs_chhattisgarh_ayush_combined()
        elif selected_site_name == "CH_GH_SCHEDULE":
            file_links = scrape_pdfs_chhattisgarh_from_url(
                CHHATTISGARH_URLS["CH_GH_SCHEDULE"]
            )
        elif selected_site_name == "CH_GH_NOTICES":
            file_links = scrape_pdfs_chhattisgarh_from_url(
                CHHATTISGARH_URLS["CH_GH_NOTICES"]
            )
        elif selected_site_name == "CH_AYUSH_SCHEDULE":
            file_links = scrape_pdfs_chhattisgarh_from_url(
                CHHATTISGARH_URLS["CH_AYUSH_SCHEDULE"]
            )
        elif selected_site_name == "CH_AYUSH_NOTICES":
            file_links = scrape_pdfs_chhattisgarh_from_url(
                CHHATTISGARH_URLS["CH_AYUSH_NOTICES"]
            )
        # Odisha (PUBLIC NOTICE + INFORMATION use same table pattern)
        elif selected_site_name == "ODISHA PUBLIC NOTICE (MBBS & BDS)":
            file_links = scrape_pdfs_wbmcc_table_headers(selected_site_url)
            if not file_links:
                file_links = scrape_pdfs_from_pages([selected_site_url])
        elif selected_site_name == "ODISHA MBBS & BDS INFORMATION":
            file_links = scrape_pdfs_wbmcc_table_headers(selected_site_url)
            if not file_links:
                file_links = scrape_pdfs_from_pages([selected_site_url])
        # State-specific scrapers
        elif selected_site_name == "TELANGANA (KNRUHS)":
            file_links = scrape_pdfs_telangana(selected_site_url)
        elif selected_site_name == "HIMACHAL PRADESH (AMRUHP)":

            file_links = scrape_pdfs_himachal_paginated(selected_site_url, max_pages=41)
        elif selected_site_name == "SIKKIM NOTICES":
            file_links = scrape_pdfs_from_pages([selected_site_url])

        # Tripura
        elif selected_site_name == "TRIPURA UG COUNSELLING":
            # prefer the paginated Tripura scraper (falls back to single-page scraper)
            file_links = scrape_pdfs_tripura_paginated(selected_site_url, max_pages=12)
            if not file_links:
                file_links = scrape_pdfs_tripura_ug(selected_site_url)
        elif selected_site_name == "TRIPURA PG COUNSELLING":
            file_links = scrape_pdfs_tripura_paginated(selected_site_url, max_pages=12)
            if not file_links:
                file_links = scrape_pdfs_tripura_ug(selected_site_url)
            # use the same paginated scraper and logic as UG

        # Andhra Pradesh
        elif selected_site_name and selected_site_name.startswith("ANDHRA PRADESH"):
            file_links = scrape_pdfs_andhra_openfile(selected_site_url)

        # AACCC (fixed section) - use new AACCC scraper for all AACCC pages
        elif selected_site_name and selected_site_name.startswith("AACCC"):
            file_links = scrape_pdfs_aaccc(selected_site_url)

        # Kerala KEAM Allotment
        elif selected_site_name == "KERALA ALLOTMENT LISTS" or (
            selected_site_name == "Manual"
            and selected_site_url.startswith("https://cee.kerala.gov.in/keam2025/allotlist")
        ):
            file_links = scrape_pdfs_kerala_allotlist(selected_site_url)

        # Bihar
        elif selected_site_name == "BIHAR DOWNLOAD":
            file_links = scrape_pdfs_bihar_download_section(NEET_SITES["BIHAR HOME"])
            if not file_links:
                file_links = scrape_pdfs_from_pages([NEET_SITES["BIHAR HOME"]])
        elif selected_site_name and selected_site_name.startswith("BIHAR"):
            file_links = scrape_pdfs_from_pages(pages or [selected_site_url])
            fallback = scrape_pdfs_bihar_download_section(NEET_SITES["BIHAR HOME"])
            if fallback:
                existing = {u for u, _ in file_links}
                for u, n in fallback:
                    if u not in existing:
                        file_links.append((u, n))

        # MCC
        elif selected_site_name and selected_site_name.startswith("MCC"):
            file_links = scrape_pdfs_mcc(pages or [selected_site_url])

        else:
            file_links = scrape_pdfs_from_pages(pages or [selected_site_url])

    if not file_links:
        st.error("No PDFs found.")
    else:
        st.success(f"Found {len(file_links)} PDFs.")
        st.session_state["pdf_links"] = file_links
        st.session_state["last_site_name"] = selected_site_name or "NEET"

# -------------------------
# DOWNLOAD UI
# -------------------------
# -------------------------
# DOWNLOAD UI (checkbox list version)
# -------------------------
# DOWNLOAD UI (main list + sidebar controls)
if st.session_state.get("pdf_links"):
    file_links = st.session_state["pdf_links"]

    # Ensure per-site checkbox state is reset when site changes
    if "pdf_list_site" not in st.session_state or st.session_state.get("pdf_list_site") != st.session_state.get("last_site_name"):
        for k in list(st.session_state.keys()):
            if k.startswith("pdf_chk_"):
                del st.session_state[k]
        st.session_state["pdf_list_site"] = st.session_state.get("last_site_name")

    # stable key builder
    def _pdf_key(i):
        return f"pdf_chk_{i}"

    # Sidebar controls (will remain visible while user scrolls main area)
    with st.sidebar:
        st.header("Actions")
        st.write(f"Site: **{(st.session_state.get('last_site_name') or 'NEET')}**")
        st.write(f"Found **{len(file_links)}** files")

        if st.button("Select all"):
            for i in range(len(file_links)):
                st.session_state[_pdf_key(i)] = True

        if st.button("Clear selection"):
            for i in range(len(file_links)):
                st.session_state[_pdf_key(i)] = False

        st.markdown("---")
        # When user clicks these, we will produce ZIP and show download button in the sidebar immediately.
        if st.button("⬇️ Download Selected PDFs (ZIP)"):
            # build selected list
            selected_links_local = [file_links[i] for i in range(len(file_links)) if st.session_state.get(_pdf_key(i))]
            if not selected_links_local:
                st.warning("No files selected. Use checkboxes in main area or 'Select all'.")
            else:
                with st.spinner("Downloading selected PDFs..."):
                    zip_buf = download_and_zip(selected_links_local)
                if zip_buf.getbuffer().nbytes < 100:
                    st.error("Downloaded ZIP is empty/corrupt.")
                else:
                    st.success("ZIP is ready — click to download.")
                    st.download_button(
                        "📦 Download Selected ZIP",
                        data=zip_buf,
                        file_name=f"{(st.session_state.get('last_site_name') or 'NEET').replace(' ', '_')}_Selected_PDFs.zip",
                        mime="application/zip",
                    )

        if st.button("🚀 Download All PDFs (ZIP)"):
            with st.spinner("Downloading all PDFs..."):
                zip_buf = download_and_zip(file_links)
            if zip_buf.getbuffer().nbytes < 100:
                st.error("Downloaded ZIP is empty/corrupt.")
            else:
                st.success("All PDFs ZIP ready — click to download.")
                st.download_button(
                    "📦 Download All ZIP",
                    data=zip_buf,
                    file_name=f"{(st.session_state.get('last_site_name') or 'NEET').replace(' ', '_')}_All_PDFs.zip",
                    mime="application/zip",
                )

        st.markdown("---")
        st.caption("Tip: Use the main list checkboxes to pick files, then click 'Download Selected' here.")

    # --- Main area: show the long list with checkboxes (scrollable) ---
    st.subheader("📑 PDFs found — pick what you want to download")
    st.markdown("Use the checkboxes to the left of each file. Sidebar contains quick actions and download buttons.")

    # header row
    header_cols = st.columns([0.05, 0.25, 0.65])
    header_cols[0].markdown("**#**")
    header_cols[1].markdown("**Select**")
    header_cols[2].markdown("**Filename / link**")

    # display each file
    for i, (url, name) in enumerate(file_links):
        key = _pdf_key(i)
        if key not in st.session_state:
            st.session_state[key] = False

        c1, c2, c3 = st.columns([0.05, 0.25, 0.65])
        c1.write(f"{i+1}")
        c2.checkbox(f"Select file {i+1}", key=key, help=f"Select {name}", label_visibility="hidden")
        short_name = name if len(name) < 80 else name[:77] + "..."
        # show clickable name + url on separate line (so user can preview)
        c3.markdown(f"[{short_name}]({url})  \n`{url}`")

    # show selection count at bottom of list
    selected_count = sum(1 for i in range(len(file_links)) if st.session_state.get(_pdf_key(i)))
    st.markdown("---")
    st.write(f"Selected **{selected_count}** / {len(file_links)} files. Use the sidebar to download.")

# -------------------------
# FOOTER
# -------------------------
st.markdown("---")











