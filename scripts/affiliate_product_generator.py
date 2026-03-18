"""Generate affiliate product data for a post by searching Amazon"""
import json
import os
import re
import time
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse, quote_plus

try:
    import requests
    from bs4 import BeautifulSoup
    REQUESTS_AVAILABLE = True
except Exception:
    REQUESTS_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

from config import AFFILIATE_DATA_FILE, AFFILIATE_IMAGES_DIR

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

BASE_HEADERS = {
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
}

AFFILIATE_TAG = "learner53-20"

CATEGORY_HINTS = [
    ("jersey", "Cristiano Ronaldo jersey"),
    ("kit", "Cristiano Ronaldo kit"),
    ("boots", "Cristiano Ronaldo soccer cleats"),
    ("shoes", "Cristiano Ronaldo soccer cleats"),
    ("fragrance", "Cristiano Ronaldo fragrance"),
    ("perfume", "Cristiano Ronaldo fragrance"),
    ("book", "Cristiano Ronaldo biography book"),
    ("biography", "Cristiano Ronaldo biography book"),
    ("poster", "Cristiano Ronaldo poster"),
    ("lamp", "Cristiano Ronaldo lamp"),
    ("night light", "Cristiano Ronaldo night light"),
    ("figurine", "Cristiano Ronaldo figurine"),
    ("statue", "Cristiano Ronaldo figurine"),
    ("ball", "Cristiano Ronaldo soccer ball"),
]


def load_affiliate_data():
    if os.path.exists(AFFILIATE_DATA_FILE):
        with open(AFFILIATE_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_affiliate_data(data):
    os.makedirs(os.path.dirname(AFFILIATE_DATA_FILE), exist_ok=True)
    with open(AFFILIATE_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def slugify(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "affiliate-product"


def pick_search_query(title, focus_kw, content):
    haystack = f"{title} {focus_kw} {content}".lower()
    for keyword, query in CATEGORY_HINTS:
        if keyword in haystack:
            return query
    if focus_kw:
        return f"Cristiano Ronaldo {focus_kw}"
    return f"Cristiano Ronaldo {title}"


def _session_with_headers():
    session = requests.Session()
    session.headers.update(BASE_HEADERS)
    session.headers["User-Agent"] = USER_AGENTS[int(time.time()) % len(USER_AGENTS)]
    return session


def _get_with_retry(session, url, max_attempts=4):
    delay = 1.5
    last_exc = None
    for attempt in range(1, max_attempts + 1):
        try:
            resp = session.get(url, timeout=30)
            if resp.status_code in (429, 503):
                raise requests.HTTPError(f"{resp.status_code} for url: {url}", response=resp)
            resp.raise_for_status()
            return resp
        except Exception as exc:
            last_exc = exc
            if attempt == max_attempts:
                break
            time.sleep(delay)
            delay *= 2
    raise last_exc


def amazon_search(query, session):
    url = f"https://www.amazon.com/s?k={quote_plus(query)}"
    resp = _get_with_retry(session, url)
    return resp.text


def relevance_score(title, query_terms):
    title_l = title.lower()
    score = 0
    for term in query_terms:
        if term in title_l:
            score += 1
    if "ronaldo" in title_l:
        score += 2
    if "cristiano" in title_l:
        score += 1
    return score


def pick_best_result(html, query):
    soup = BeautifulSoup(html, "html.parser")
    query_terms = [t for t in re.split(r"\s+", query.lower()) if t]
    candidates = []
    for item in soup.select('div[data-component-type="s-search-result"]'):
        title_el = item.select_one("h2 a span")
        link_el = item.select_one("h2 a")
        if not title_el or not link_el:
            continue
        title = title_el.get_text(strip=True)
        href = link_el.get("href")
        if not title or not href:
            continue
        score = relevance_score(title, query_terms)
        candidates.append((score, title, urljoin("https://www.amazon.com", href)))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return {
        "title": candidates[0][1],
        "url": candidates[0][2],
    }


def fetch_product_page(url, session):
    resp = _get_with_retry(session, url)
    return resp.text


def extract_product_data(html):
    soup = BeautifulSoup(html, "html.parser")

    title_el = soup.select_one("#productTitle")
    title = title_el.get_text(strip=True) if title_el else None

    price = None
    price_el = soup.select_one("span.a-price span.a-offscreen")
    if price_el:
        price = price_el.get_text(strip=True)
    else:
        for sel in ["#priceblock_ourprice", "#priceblock_dealprice", "#priceblock_saleprice", "#price_inside_buybox"]:
            el = soup.select_one(sel)
            if el:
                price = el.get_text(strip=True)
                break

    rating = None
    rating_el = soup.select_one('span[data-hook="rating-out-of-text"]')
    if rating_el:
        rating_text = rating_el.get_text(strip=True)
        rating = rating_text.split(" ")[0]
    else:
        rating_el = soup.select_one('i[data-hook="average-star-rating"] span')
        if rating_el:
            rating_text = rating_el.get_text(strip=True)
            rating = rating_text.split(" ")[0]

    reviewnum = None
    review_el = soup.select_one("#acrCustomerReviewText")
    if review_el:
        review_text = review_el.get_text(strip=True)
        review_num = re.sub(r"[^0-9]", "", review_text)
        reviewnum = int(review_num) if review_num else None

    bullets = []
    for li in soup.select("#feature-bullets ul li span"):
        text = li.get_text(" ", strip=True)
        if text:
            bullets.append(text)
    bullets = [b for b in bullets if len(b) > 10]

    desc = None
    if bullets:
        desc = " ".join(bullets[:2])
        desc = re.sub(r"\s+", " ", desc).strip()
        if len(desc) > 180:
            desc = desc[:177] + "..."

    brand = None
    brand_el = soup.select_one("#bylineInfo")
    if brand_el:
        brand_text = brand_el.get_text(" ", strip=True)
        brand = brand_text.replace("Brand:", "").replace("Visit the", "").replace("Store", "").strip()

    image_url = None
    og = soup.select_one('meta[property="og:image"]')
    if og and og.get("content"):
        image_url = og.get("content")
    if not image_url:
        img = soup.select_one("img#landingImage")
        if img and img.get("data-old-hires"):
            image_url = img.get("data-old-hires")

    return {
        "title": title,
        "price": price,
        "rating": rating,
        "reviewnum": reviewnum,
        "desc": desc,
        "brand": brand,
        "image_url": image_url,
        "bullets": bullets,
    }


def shorten_product_name(title):
    if not title:
        return None
    title = re.sub(r"\([^\)]*\)", "", title)
    title = re.sub(r"\[[^\]]*\]", "", title)
    title = re.sub(r"\s+", " ", title).strip()
    parts = re.split(r"\s+", title)
    if len(parts) > 10:
        title = " ".join(parts[:10])
    if len(title) > 70:
        title = title[:67].rsplit(" ", 1)[0] + "..."
    return title


def safe_feature(text, fallback):
    if not text:
        return fallback
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > 32:
        text = text[:29].rsplit(" ", 1)[0] + "..."
    return text


def add_affiliate_tag(url):
    if not url:
        return url
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    if "tag" not in qs:
        qs["tag"] = [AFFILIATE_TAG]
    query = urlencode(qs, doseq=True)
    return urlunparse(parsed._replace(query=query))


def download_image(image_url, filename_base, session):
    if not image_url:
        return None
    os.makedirs(AFFILIATE_IMAGES_DIR, exist_ok=True)
    resp = _get_with_retry(session, image_url)
    ext = "webp"
    out_path = os.path.join(AFFILIATE_IMAGES_DIR, f"{filename_base}.{ext}")

    if PIL_AVAILABLE:
        from io import BytesIO
        img = Image.open(BytesIO(resp.content)).convert("RGB")
        img.save(out_path, "WEBP", quality=85)
    else:
        ext = "jpg"
        out_path = os.path.join(AFFILIATE_IMAGES_DIR, f"{filename_base}.{ext}")
        with open(out_path, "wb") as f:
            f.write(resp.content)

    return out_path


def generate_affiliate_product_for_post(post_path, title, focus_kw, permalink, content):
    if not REQUESTS_AVAILABLE:
        raise RuntimeError("Missing dependencies: requests and beautifulsoup4 are required")
    slug = permalink
    data = load_affiliate_data()
    if slug in data:
        print(f"ℹ️ Affiliate data already exists for {slug}, skipping")
        return None

    session = _session_with_headers()
    try:
        _get_with_retry(session, "https://www.amazon.com/")
    except Exception:
        pass

    query = pick_search_query(title, focus_kw, content)
    print(f"🔎 Amazon search query: {query}")

    search_html = amazon_search(query, session)
    best = pick_best_result(search_html, query)
    if not best:
        print("⚠️ No Amazon results found")
        return None

    time.sleep(1.5)
    product_html = fetch_product_page(best["url"], session)
    product_data = extract_product_data(product_html)

    product_title = product_data.get("title") or best["title"]
    short_name = shorten_product_name(product_title) or product_title

    filename_base = slugify(short_name)
    image_path = download_image(product_data.get("image_url"), filename_base, session)

    afflink = add_affiliate_tag(best["url"])

    bullets = product_data.get("bullets", [])
    item = safe_feature(bullets[0] if len(bullets) > 0 else None, "Official Merchandise")
    special = safe_feature(bullets[1] if len(bullets) > 1 else None, "Fan Favorite")

    record = {
        "afflink": afflink,
        "affimage": image_path.replace("\\", "/") if image_path else None,
        "affname": short_name,
        "affdesc": product_data.get("desc"),
        "currentprice": product_data.get("price"),
        "reviewnum": product_data.get("reviewnum"),
        "rating": product_data.get("rating"),
        "brand": product_data.get("brand") or "Cristiano Ronaldo",
        "item": item,
        "specialfeature": special,
        "source": "amazon",
    }

    data[slug] = record
    save_affiliate_data(data)
    print(f"✅ Affiliate data saved for {slug}")
    return record
