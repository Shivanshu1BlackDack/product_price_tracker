import json
import re
import ssl
import time
from decimal import Decimal, InvalidOperation
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from playwright.sync_api import sync_playwright


# ============================================================
# CONFIGURATION
# ============================================================

STORE_BASE_URL = "https://demo.inelabteamdev.com"
PRODUCT_API_URL = f"{STORE_BASE_URL}/api/product"

DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_TIMEOUT = 30000

# The mock store requires continuous mouse movement over the
# Reveal Price area. Keep this around 2 seconds.
REVEAL_MOVE_SECONDS = 2.0

# Maximum amount of time to wait for dynamically rendered data.
DATA_WAIT_SECONDS = 10


def titleise_key(value):
    text = clean_text(value)

    if not text:
        return ""

    words = []
    current = ""

    for char in text:
        if char.isupper() and current:
            words.append(current)
            current = char
        else:
            current += char

    if current:
        words.append(current)

    label = " ".join(words).replace("_", " ")
    return label[:1].upper() + label[1:]


def normalise_api_specs(specs):
    if not isinstance(specs, dict):
        return {}

    normalised = {}

    for key, value in specs.items():
        if value in [None, ""]:
            continue

        label = titleise_key(key)

        if key == "weightGrams":
            label = "Weight"
            value = f"{value} g"

        normalised[label] = str(value)

    return normalised


def fetch_product_api_details(product_id):
    request = Request(
        f"{PRODUCT_API_URL}/{int(product_id)}",
        headers={
            "Accept": "application/json",
            "User-Agent": (
                "Mozilla/5.0 ProductPriceTracker/1.0"
            ),
        },
    )

    context = ssl._create_unverified_context()

    with urlopen(
        request,
        timeout=20,
        context=context,
    ) as response:
        payload = json.loads(
            response.read().decode("utf-8")
        )

    return {
        "id": int(payload.get("id") or product_id),
        "name": clean_text(payload.get("name")),
        "brand": clean_text(payload.get("brand")),
        "category": clean_text(payload.get("category")),
        "sku": clean_text(payload.get("sku")),
        "url": f"{STORE_BASE_URL}/product/{int(product_id)}",
        "description": clean_text(
            payload.get("description")
        ),
        "specifications": normalise_api_specs(
            payload.get("specs")
        ),
    }


# ============================================================
# BASIC HELPERS
# ============================================================

def clean_text(value):
    if value is None:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value),
    ).strip()


def parse_money(value):
    if value is None:
        return None

    text = clean_text(value)

    if not text:
        return None

    match = re.search(
        r"(?:₹|Rs\.?|INR)?\s*"
        r"([0-9][0-9,]*(?:\.[0-9]+)?)",
        text,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    try:
        return Decimal(
            match.group(1).replace(",", "")
        )
    except InvalidOperation:
        return None


def extract_product_id(url):
    match = re.search(
        r"/product/(\d+)",
        url or "",
    )

    if not match:
        return None

    return int(match.group(1))


def safe_visible_text(page, selector):
    try:
        locator = page.locator(selector)

        for index in range(locator.count()):

            element = locator.nth(index)

            if not element.is_visible():
                continue

            text = clean_text(
                element.inner_text()
            )

            if text:
                return text

    except Exception:
        pass

    return ""


def safe_texts(page, selector):
    texts = []

    try:
        locator = page.locator(selector)

        for index in range(locator.count()):
            element = locator.nth(index)

            if not element.is_visible():
                continue

            text = clean_text(
                element.inner_text()
            )

            if text:
                texts.append(text)

    except Exception:
        pass

    return texts


# ============================================================
# COOKIE HELPERS
# ============================================================

def cookie_overlay_visible(page):
    """
    Returns True when the cookie overlay is currently visible.
    """

    selectors = [
        ".cookie-overlay",
        ".cookie-banner",
        "[class*='cookie-overlay']",
        "[class*='cookie-banner']",
    ]

    for selector in selectors:

        try:

            locator = page.locator(selector)

            for index in range(locator.count()):

                element = locator.nth(index)

                if element.is_visible():
                    return True

        except Exception:
            continue

    return False


def find_cookie_accept_button(page):
    """
    Find a visible cookie consent button.
    """

    selectors = [
        ".cookie-overlay button",
        ".cookie-banner button",
        "button:has-text('ACCEPT')",
        "button[aria-label*='ACCEPT' i]",
        "button[title*='ACCEPT' i]",
        "[role='button']:has-text('ACCEPT')",
    ]

    for selector in selectors:

        try:

            buttons = page.locator(selector)

            for index in range(buttons.count()):

                button = buttons.nth(index)

                if not button.is_visible():
                    continue

                text = clean_text(
                    button.inner_text()
                ).lower()

                # Buttons found inside the cookie container
                # are already sufficiently identified.
                if (
                    "cookie-overlay" in selector
                    or "cookie-banner" in selector
                ):
                    return button

                if (
                    "accept" in text
                    or "agree" in text
                    or "allow" in text
                    or text == "ok"
                    or "continue" in text
                ):
                    return button

        except Exception:
            continue

    return None


def wait_for_cookie_to_disappear(
    page,
    timeout_seconds=5,
):
    deadline = (
        time.time()
        + timeout_seconds
    )

    while time.time() < deadline:

        if not cookie_overlay_visible(page):
            return True

        page.wait_for_timeout(200)

    return not cookie_overlay_visible(page)


def accept_cookies(
    page,
    wait_seconds=8,
):
    """
    Handle a cookie banner when it is visible.

    We do NOT repeatedly call this during normal mouse movement.
    It is used:
    1. during initial page loading
    2. when a later interaction reveals that a cookie overlay
       appeared and blocked the interaction
    """

    if not cookie_overlay_visible(page):
        return False

    print(
        "  ├── COOKIE OVERLAY DETECTED"
    )

    deadline = (
        time.time()
        + wait_seconds
    )

    while time.time() < deadline:

        button = find_cookie_accept_button(page)

        if button is None:

            page.wait_for_timeout(250)
            continue

        print(
            "  │   ├── ACCEPT button found"
        )

        try:

            button.click(
                timeout=2500
            )

        except Exception:

            try:

                button.click(
                    timeout=2500,
                    force=True,
                )

            except Exception:
                page.wait_for_timeout(300)
                continue

        if wait_for_cookie_to_disappear(
            page,
            timeout_seconds=3,
        ):

            print(
                "  │   └── cookies accepted"
            )

            return True

        # One extra forced attempt if overlay is still there.
        try:

            button.click(
                timeout=2000,
                force=True,
            )

        except Exception:
            pass

        if wait_for_cookie_to_disappear(
            page,
            timeout_seconds=2,
        ):

            print(
                "  │   └── cookies accepted"
            )

            return True

    print(
        "  │   └── could not dismiss cookie overlay"
    )

    return False


# ============================================================
# CATALOG DISCOVERY
# ============================================================

def _looks_like_product_record(data):

    if not isinstance(data, dict):
        return False

    product_id = data.get("id")

    name = (
        data.get("name")
        or data.get("title")
        or data.get("productName")
    )

    if product_id is None or not name:
        return False

    try:
        int(product_id)
    except Exception:
        return False

    return True


def _normalise_catalog_product(item):

    product_id = item.get("id")

    name = (
        item.get("name")
        or item.get("title")
        or item.get("productName")
        or ""
    )

    sku = (
        item.get("sku")
        or item.get("SKU")
        or item.get("productSku")
        or ""
    )

    brand = (
        item.get("brand")
        or item.get("brandName")
        or ""
    )

    category = (
        item.get("category")
        or item.get("categoryName")
        or ""
    )

    url = (
        item.get("url")
        or item.get("href")
        or item.get("link")
        or ""
    )

    if url and not url.startswith("http"):
        url = urljoin(
            STORE_BASE_URL,
            url,
        )

    if not url:
        url = (
            f"{STORE_BASE_URL}"
            f"/product/{product_id}"
        )

    return {
        "id": int(product_id),
        "name": clean_text(name),
        "sku": clean_text(sku),
        "brand": clean_text(brand),
        "category": clean_text(category),
        "url": url,
    }


def _walk_json_for_products(
    value,
    results,
):

    if isinstance(value, dict):

        if _looks_like_product_record(value):

            results.append(
                _normalise_catalog_product(
                    value
                )
            )

        for child in value.values():

            _walk_json_for_products(
                child,
                results,
            )

    elif isinstance(value, list):

        for child in value:

            _walk_json_for_products(
                child,
                results,
            )


def _collect_json_response(
    response,
    products,
):

    try:

        content_type = (
            response.headers
            .get(
                "content-type",
                "",
            )
            .lower()
        )

        if "json" not in content_type:
            return

        payload = response.json()

        found = []

        _walk_json_for_products(
            payload,
            found,
        )

        products.extend(found)

    except Exception:
        pass


def _deduplicate_catalog(products):

    unique = {}

    for product in products:

        product_id = product.get("id")

        if product_id is None:
            continue

        if product_id not in unique:

            unique[product_id] = product

        else:

            existing = unique[product_id]

            for field in [
                "name",
                "sku",
                "brand",
                "category",
                "url",
            ]:

                if (
                    not existing.get(field)
                    and product.get(field)
                ):

                    existing[field] = (
                        product[field]
                    )

    return list(
        unique.values()
    )


def discover_homepage_catalog(page):
    """
    Used only to populate/update the local catalog.

    Tracking does NOT call this function.
    """

    print(
        "  ├── discover product catalog"
    )

    discovered = []

    def response_handler(response):

        _collect_json_response(
            response,
            discovered,
        )

    page.on(
        "response",
        response_handler,
    )

    try:

        page.goto(
            STORE_BASE_URL,
            wait_until="domcontentloaded",
            timeout=DEFAULT_TIMEOUT,
        )

        page.wait_for_timeout(1500)

        # Initial cookie handling.
        if cookie_overlay_visible(page):

            accepted = accept_cookies(
                page,
                wait_seconds=6,
            )

            if not accepted:
                raise RuntimeError(
                    "Catalog cookie overlay could not be dismissed."
                )

        # Allow catalog APIs/rendering to finish.
        page.wait_for_timeout(2500)

        try:

            cards = page.locator(
                "article.tile"
            )

            for index in range(
                cards.count()
            ):

                card = cards.nth(index)

                try:

                    name = clean_text(
                        card
                        .locator(
                            ".tile-name"
                        )
                        .first
                        .inner_text()
                    )

                    if not name:
                        continue

                    brand = clean_text(
                        card
                        .locator(
                            ".tile-brand"
                        )
                        .first
                        .inner_text()
                    )

                    sku = clean_text(
                        card
                        .locator(
                            ".tile-sku"
                        )
                        .first
                        .inner_text()
                    )

                    category = clean_text(
                        card
                        .locator(
                            ".tile-category"
                        )
                        .first
                        .inner_text()
                    )

                    href = ""

                    try:

                        href = (
                            card
                            .locator("a")
                            .first
                            .get_attribute(
                                "href"
                            )
                            or ""
                        )

                    except Exception:
                        pass

                    product_id = extract_product_id(
                        href
                    )

                    if product_id is None:

                        data_id = (
                            card.get_attribute(
                                "data-product-id"
                            )
                            or card.get_attribute(
                                "data-id"
                            )
                        )

                        if data_id:

                            try:
                                product_id = int(
                                    data_id
                                )
                            except Exception:
                                pass

                    if product_id is None:
                        continue

                    discovered.append(
                        {
                            "id": product_id,
                            "name": name,
                            "sku": sku,
                            "brand": brand,
                            "category": category,
                            "url": (
                                f"{STORE_BASE_URL}"
                                f"/product/"
                                f"{product_id}"
                            ),
                        }
                    )

                except Exception:
                    continue

        except Exception:
            pass

    finally:

        try:
            page.remove_listener(
                "response",
                response_handler,
            )
        except Exception:
            pass

    products = _deduplicate_catalog(
        discovered
    )

    print(
        "  │   └── Product records discovered:",
        len(products),
    )

    return products


# ============================================================
# PRODUCT DETAILS
# ============================================================

def extract_product_page_details(
    page,
    product,
):

    details = dict(
        product or {}
    )

    name = safe_visible_text(
        page,
        "h1",
    )

    if name:
        details["name"] = name

    brand = safe_visible_text(
        page,
        ".product-brand",
    )

    if brand:
        details["brand"] = brand

    sku = safe_visible_text(
        page,
        ".product-sku",
    )

    body_text = ""

    try:
        body_text = clean_text(
            page.locator("body").inner_text()
        )
    except Exception:
        body_text = ""

    if not sku and body_text:
        sku_match = re.search(
            r"\bSKU\s+([A-Z0-9-]+)",
            body_text,
            flags=re.IGNORECASE,
        )

        if sku_match:
            sku = f"SKU {sku_match.group(1)}"

    if sku:
        details["sku"] = sku

    if not brand and body_text:
        brand_match = re.search(
            r"([A-Za-z][A-Za-z0-9 &.-]{1,40})\s*[·\-]\s*SKU\b",
            body_text,
        )

        if brand_match:
            brand = clean_text(
                brand_match.group(1)
            )
            details["brand"] = brand

    seller = safe_visible_text(
        page,
        ".seller",
    )

    if not seller and body_text:
        seller_match = re.search(
            r"Sold by\s+(.+?)(?:\s+Get it by|\s+ONLY|\s+Loaded in|$)",
            body_text,
            flags=re.IGNORECASE,
        )

        if seller_match:
            seller = clean_text(
                seller_match.group(1)
            )

    if seller:
        details["seller"] = seller

    delivery = safe_visible_text(
        page,
        ".delivery",
    )

    if not delivery and body_text:
        delivery_match = re.search(
            r"Get it by\s+(.+?)(?:\s+ONLY|\s+Loaded in|$)",
            body_text,
            flags=re.IGNORECASE,
        )

        if delivery_match:
            delivery = clean_text(
                delivery_match.group(1)
            )

    if delivery:
        details["delivery"] = delivery

    description = safe_visible_text(
        page,
        ".description",
    )

    if description:
        details["description"] = description

    about = safe_visible_text(
        page,
        ".about",
    )

    if about:
        details["about"] = about

    if not details.get("category"):
        category = extract_category_near_title(
            page
        )

        if category:
            details["category"] = category

    # The assignment storefront presents product details in
    # plain sections/tables. Extract them without using ratings.
    try:
        details["specifications"] = (
            extract_specifications(page)
        )
    except Exception:
        details["specifications"] = {}

    if not details.get("description"):
        fallback_description = (
            extract_intro_description(page)
        )

        if fallback_description:
            details["description"] = (
                fallback_description
            )

    if not details.get("about"):
        fallback_about = extract_about_item(
            page
        )

        if fallback_about:
            details["about"] = fallback_about

    try:

        image = (
            page
            .locator("main img")
            .first
            .get_attribute("src")
        )

        if image:

            details["image"] = urljoin(
                STORE_BASE_URL,
                image,
            )

    except Exception:
        pass

    return details


def extract_category_near_title(page):
    try:
        heading = page.locator("h1").first

        if heading.count() == 0:
            return ""

        heading_handle = heading.element_handle()

        if heading_handle is None:
            return ""

        category = page.evaluate(
            """
            (heading) => {
              let node = heading.previousElementSibling;

              while (node) {
                const text = (node.innerText || '').trim();

                if (
                  text &&
                  text.length <= 40 &&
                  /^[A-Z][A-Z\\s-]+$/.test(text)
                ) {
                  return text;
                }

                node = node.previousElementSibling;
              }

              return '';
            }
            """,
            heading_handle,
        )

        return clean_text(category)

    except Exception:
        return ""


def extract_intro_description(page):
    selectors = [
        ".product-description",
        ".description",
        "main p",
        "article p",
    ]

    ignored_fragments = [
        "rating",
        "ratings",
        "sold by",
        "only",
        "left",
        "loaded in",
    ]

    for selector in selectors:
        for text in safe_texts(page, selector):
            lower_text = text.lower()

            if any(
                fragment in lower_text
                for fragment in ignored_fragments
            ):
                continue

            if len(text) >= 30:
                return text

    return ""


def extract_about_item(page):
    try:
        about_locator = page.get_by_text(
            re.compile(
                r"about this item",
                re.IGNORECASE,
            )
        ).first

        if about_locator.count() == 0:
            return ""

        about_handle = (
            about_locator.element_handle()
        )

        if about_handle is None:
            return ""

        text = page.evaluate(
            """
            (heading) => {
              const chunks = [];
              let node = heading.nextElementSibling;

              while (node) {
                const tag = node.tagName.toLowerCase();
                const text = (node.innerText || '').trim();

                if (/^h[1-6]$/.test(tag)) {
                  break;
                }

                if (text) {
                  chunks.push(text);
                }

                node = node.nextElementSibling;
              }

              return chunks.join('\\n');
            }
            """,
            about_handle,
        )

        return clean_text(text)

    except Exception:
        return ""


def extract_specifications(page):
    specs = {}

    try:
        rows = page.locator(
            "table tr, .specification-row, "
            ".specifications tr, "
            "[class*='specification'] tr"
        )

        for index in range(rows.count()):
            row = rows.nth(index)

            if not row.is_visible():
                continue

            cells = row.locator(
                "th, td, .specification-name, "
                ".specification-value"
            )

            if cells.count() >= 2:
                key = clean_text(
                    cells.nth(0).inner_text()
                )
                value = clean_text(
                    cells.nth(1).inner_text()
                )

                if key and value:
                    specs[key] = value

    except Exception:
        pass

    if specs:
        return specs

    try:
        heading = page.get_by_text(
            re.compile(
                r"specifications",
                re.IGNORECASE,
            )
        ).first

        if heading.count() == 0:
            return {}

        heading_handle = heading.element_handle()

        if heading_handle is None:
            return {}

        extracted = page.evaluate(
            """
            (heading) => {
              const specs = {};
              let node = heading.nextElementSibling;

              while (node) {
                const tag = node.tagName.toLowerCase();

                if (/^h[1-6]$/.test(tag)) {
                  break;
                }

                const rows = Array.from(
                  node.querySelectorAll(
                    'tr, .specification-row, li, div'
                  )
                );

                for (const row of rows) {
                  const cells = Array.from(
                    row.querySelectorAll(
                      'th, td, .specification-name, .specification-value, span'
                    )
                  )
                    .map((cell) => (cell.innerText || '').trim())
                    .filter(Boolean);

                  if (cells.length >= 2) {
                    specs[cells[0]] = cells.slice(1).join(' ');
                    continue;
                  }

                  const text = (row.innerText || '').trim();
                  const parts = text
                    .split(/\\n|\\s{2,}|:/)
                    .map((part) => part.trim())
                    .filter(Boolean);

                  if (parts.length >= 2) {
                    specs[parts[0]] = parts.slice(1).join(' ');
                  }
                }

                node = node.nextElementSibling;
              }

              return specs;
            }
            """,
            heading_handle,
        )

        if isinstance(extracted, dict):
            return {
                clean_text(key): clean_text(value)
                for key, value in extracted.items()
                if clean_text(key)
                and clean_text(value)
                and "rating" not in clean_text(key).lower()
            }

    except Exception:
        pass

    return {}


# ============================================================
# REVEAL BUTTON
# ============================================================

def find_reveal_button(page):

    selectors = [
        "button[aria-label='Reveal price']",
        "button[aria-label*='Reveal price' i]",
        "button:has-text('Reveal price')",
        ".price-block button",
    ]

    for selector in selectors:

        try:

            locator = page.locator(
                selector
            )

            for index in range(
                locator.count()
            ):

                button = locator.nth(
                    index
                )

                if button.is_visible():
                    return button

        except Exception:
            continue

    return None


# ============================================================
# PRICE BLOCK SWEEP
# ============================================================

def move_across_price_block(page):

    """
    Start a real hover session over the price block.

    The INE page listens for ``onMouseEnter`` and ``onMouseMove`` on
    ``.price-block`` itself, not on the disabled Reveal Price button.
    Moving from a known point outside the block first is important: it
    guarantees that React receives a trusted mouse-enter event before
    the individual mouse moves are counted.
    """

    print(
        "  ├── moving across price block"
    )

    price_block = page.locator(
        ".price-block"
    ).first

    if price_block.count() == 0:

        raise RuntimeError(
            "Price block was not found."
        )

    price_block.wait_for(
        state="visible",
        timeout=20000,
    )

    # A product price block can be below the initially visible part of
    # the page. Native mouse events only reach it once it is in view.
    price_block.scroll_into_view_if_needed()
    page.wait_for_timeout(150)

    box = price_block.bounding_box()

    if not box:

        raise RuntimeError(
            "Could not determine price block position."
        )

    left = box["x"]
    top = box["y"]
    width = box["width"]
    height = box["height"]

    print(
        f"  │   ├── price block: "
        f"x={left:.0f}, "
        f"y={top:.0f}, "
        f"width={width:.0f}, "
        f"height={height:.0f}"
    )

    viewport = page.evaluate(
        """() => ({
            width: window.innerWidth,
            height: window.innerHeight,
        })"""
    )

    # Pick a point outside the block so the next move produces a real
    # mouse-enter on .price-block. The normal product layout leaves at
    # least one viewport corner outside the block.
    outside_points = [
        (4, 4),
        (max(viewport["width"] - 4, 1), 4),
        (4, max(viewport["height"] - 4, 1)),
        (
            max(viewport["width"] - 4, 1),
            max(viewport["height"] - 4, 1),
        ),
    ]

    outside_x, outside_y = outside_points[0]

    for candidate_x, candidate_y in outside_points:

        inside_block = (
            left <= candidate_x <= left + width
            and top <= candidate_y <= top + height
        )

        if not inside_block:
            outside_x, outside_y = candidate_x, candidate_y
            break

    page.mouse.move(outside_x, outside_y)
    page.wait_for_timeout(100)

    horizontal_margin = max(width * 0.14, 8)
    vertical_margin = max(height * 0.18, 8)
    usable_width = max(width - 2 * horizontal_margin, 12)
    usable_height = max(height - 2 * vertical_margin, 12)

    # The storefront accepts a move only every 40ms. Use sixteen
    # distinct native events with a 75ms gap, which supplies both the
    # required 8 movements and more than 600ms of dwell time.
    for step in range(16):

        horizontal_ratio = (step % 8) / 7

        if (step // 8) % 2:
            horizontal_ratio = 1 - horizontal_ratio

        vertical_ratio = 0.28 if step % 2 == 0 else 0.72

        page.mouse.move(
            left + horizontal_margin + usable_width * horizontal_ratio,
            top + vertical_margin + usable_height * vertical_ratio,
        )

        page.wait_for_timeout(75)

    print(
        "  │   └── price block movement complete"
    )


# ============================================================
# CONTINUOUS MOVEMENT OVER REVEAL BUTTON
# ============================================================

def continuously_move_over_reveal_button(
    page,
    seconds=REVEAL_MOVE_SECONDS,
):

    """
    IMPORTANT:

    The mock store requires actual pointer movement inside
    the Reveal Price area.

    We intentionally DO NOT use:

        button.hover()
        wait(2 seconds)

    Instead, the pointer continuously moves left/right
    inside the price block for approximately 2 seconds.

    The button begins disabled. Moving over the parent block is more
    reliable because the page attaches its event handlers there and
    disabled buttons do not consistently deliver mouse events.
    """

    print(
        "  ├── continuously moving over Reveal Price"
    )

    start_time = time.time()
    step = 0

    while (
        time.time() - start_time
        < seconds
    ):

        price_block = page.locator(
            ".price-block"
        ).first

        if price_block.count() == 0:

            raise RuntimeError(
                "Price block disappeared during Reveal Price movement."
            )

        price_block.scroll_into_view_if_needed()
        box = price_block.bounding_box()

        if not box:

            raise RuntimeError(
                "Could not determine price block position."
            )

        left = box["x"]
        top = box["y"]
        width = box["width"]
        height = box["height"]

        # Stay safely inside the parent price block.
        horizontal_margin = max(
            width * 0.12,
            3,
        )

        vertical_margin = max(
            height * 0.20,
            2,
        )

        usable_width = max(
            width
            - 2 * horizontal_margin,
            5,
        )

        usable_height = max(
            height
            - 2 * vertical_margin,
            5,
        )

        horizontal_ratio = (
            step % 20
        ) / 19

        # Reverse direction after each sweep.
        if (
            (step // 20) % 2
            == 1
        ):

            horizontal_ratio = (
                1
                - horizontal_ratio
            )

        vertical_ratio = (
            step % 8
        ) / 7

        x = (
            left
            + horizontal_margin
            + usable_width
            * horizontal_ratio
        )

        y = (
            top
            + vertical_margin
            + usable_height
            * vertical_ratio
        )

        # Actual mouse movement.
        page.mouse.move(
            x,
            y,
        )

        page.wait_for_timeout(
            60
        )

        step += 1

    print(
        "  │   └── continuous Reveal Price movement complete"
    )


# ============================================================
# WAIT FOR REVEAL BUTTON TO ACTIVATE
# ============================================================

def reveal_progress_message(page):
    """Return the storefront's visible hover/reveal instruction."""

    return safe_visible_text(
        page,
        ".price-block .price-substatus",
    )


def wait_for_reveal_button_enabled(
    page,
    timeout_seconds=5,
):

    """
    While waiting for activation, continue making tiny
    pointer movements. We do NOT simply stop and wait.
    """

    print(
        "  ├── waiting for Reveal Price activation"
    )

    deadline = (
        time.time()
        + timeout_seconds
    )

    direction = -1
    last_progress = ""

    while time.time() < deadline:

        button = find_reveal_button(
            page
        )

        if button is None:

            page.wait_for_timeout(
                200
            )

            continue

        try:

            if button.is_enabled():

                print(
                    "  │   └── Reveal Price button is ENABLED"
                )

                return button

        except Exception:
            pass

        progress = reveal_progress_message(page)

        if progress and progress != last_progress:

            print(
                "  │   ├── Reveal Price state:",
                progress,
            )

            last_progress = progress

        # Continue movement while waiting.
        try:

            price_block = page.locator(
                ".price-block"
            ).first

            price_block.scroll_into_view_if_needed()
            box = price_block.bounding_box()

            if box:

                center_x = (
                    box["x"]
                    + box["width"]
                    / 2
                )

                center_y = (
                    box["y"]
                    + box["height"]
                    / 2
                )

                page.mouse.move(
                    center_x
                    + direction * min(
                        box["width"] * 0.22,
                        80,
                    ),
                    center_y,
                )

                page.wait_for_timeout(
                    120
                )

                page.mouse.move(
                    center_x
                    - direction * min(
                        box["width"] * 0.22,
                        80,
                    ),
                    center_y,
                )

                page.wait_for_timeout(
                    120
                )

                direction *= -1

        except Exception:
            pass

    if last_progress:

        print(
            "  │   └── Reveal Price remained unavailable:",
            last_progress,
        )

    return None


# ============================================================
# CLICK REVEAL WITH COOKIE RECOVERY
# ============================================================

def wait_for_price_reveal_to_start(
    page,
    timeout_seconds=2,
):
    """Confirm that the page left its idle/hidden-price state."""

    deadline = time.time() + timeout_seconds

    while time.time() < deadline:

        try:
            price_block = page.locator(
                ".price-block"
            ).first
            class_name = price_block.get_attribute("class") or ""

            if "price-idle" not in class_name:
                return class_name

        except Exception:
            pass

        page.wait_for_timeout(100)

    return ""


def native_pointer_click_reveal(page, button):
    """
    Send a trusted mouse down/up sequence as a locator-click fallback.

    Do not use element.click() here. A DOM-generated click has
    ``isTrusted == false`` and the INE price service deliberately
    rejects that request.
    """

    button.scroll_into_view_if_needed()
    box = button.bounding_box()

    if not box:
        raise RuntimeError(
            "Could not determine Reveal Price button position."
        )

    x = box["x"] + box["width"] / 2
    y = box["y"] + box["height"] / 2

    page.mouse.move(x, y)
    page.wait_for_timeout(80)
    page.mouse.down()
    page.wait_for_timeout(50)
    page.mouse.up()


def click_reveal_and_confirm(page, button):
    """Use a native click and verify the page begins loading a quote."""

    button.click(timeout=4000)
    state = wait_for_price_reveal_to_start(page)

    if state:
        return state

    raise RuntimeError(
        "Reveal Price received a click but stayed in its hidden state."
    )


def click_reveal_with_cookie_recovery(
    page,
):
    """
    Perform the final Reveal Price click.

    Normally:
        real Playwright click, followed by a state check.

    If a late cookie overlay intercepts the click:
        accept cookie
        re-find button
        repeat continuous mouse movement
        wait for activation
        click again
    """

    button = find_reveal_button(
        page
    )

    if button is None:

        raise RuntimeError(
            "Reveal Price button was not found."
        )

    # --------------------------------------------------------
    # First real click.
    # --------------------------------------------------------

    print(
        "  ├── CLICKING Reveal Price"
    )

    try:

        click_reveal_and_confirm(
            page,
            button,
        )

        print(
            "  │   └── Reveal Price clicked"
        )

        return

    except Exception as click_error:

        # ----------------------------------------------------
        # Did a cookie overlay cause the failure?
        # ----------------------------------------------------

        if not cookie_overlay_visible(page):

            # A normal locator click can fail because a reactive layout
            # moved beneath the pointer. Re-arm the hover requirement and
            # use an actual mouse down/up sequence, never a DOM click.
            print(
                "  ├── rearming Reveal Price after native click failure"
            )

            continuously_move_over_reveal_button(
                page,
                seconds=REVEAL_MOVE_SECONDS,
            )

            button = wait_for_reveal_button_enabled(
                page,
                timeout_seconds=5,
            )

            if button is None:
                raise click_error

            native_pointer_click_reveal(page, button)
            state = wait_for_price_reveal_to_start(page)

            if state:
                print(
                    "  │   └── Reveal Price clicked with native pointer"
                )
                return

            raise RuntimeError(
                "Native Reveal Price click did not start the quote request."
            )

        # ----------------------------------------------------
        # Late cookie appeared.
        # ----------------------------------------------------

        print(
            "  ├── late cookie overlay blocked the click"
        )

        accepted = accept_cookies(
            page,
            wait_seconds=6,
        )

        if not accepted:

            raise RuntimeError(
                "Cookie overlay blocked Reveal Price "
                "and could not be dismissed."
            )

        # ----------------------------------------------------
        # DOM/state may have changed after accepting cookies.
        # Re-find button.
        # ----------------------------------------------------

        button = find_reveal_button(
            page
        )

        if button is None:

            raise RuntimeError(
                "Reveal Price button disappeared "
                "after cookie acceptance."
            )

        # ----------------------------------------------------
        # Re-run the required continuous movement.
        # ----------------------------------------------------

        print(
            "  ├── reactivating Reveal Price after cookie"
        )

        continuously_move_over_reveal_button(
            page,
            seconds=REVEAL_MOVE_SECONDS,
        )

        button = wait_for_reveal_button_enabled(
            page,
            timeout_seconds=5,
        )

        if button is None:

            raise RuntimeError(
                "Reveal Price button could not be "
                "reactivated after cookie acceptance."
            )

        # ----------------------------------------------------
        # Real click again.
        # ----------------------------------------------------

        try:

            click_reveal_and_confirm(
                page,
                button,
            )

            print(
                "  │   └── Reveal Price clicked after cookie recovery"
            )

        except Exception:

            native_pointer_click_reveal(page, button)
            state = wait_for_price_reveal_to_start(page)

            if not state:
                raise RuntimeError(
                    "Native Reveal Price click did not start after cookie recovery."
                )

            print(
                "  │   └── Reveal Price clicked with native pointer "
                "after cookie recovery"
            )


# ============================================================
# REVEAL PRICE - COMPLETE FLOW
# ============================================================

def reveal_price(page):

    print(
        "  ├── starting Reveal Price sequence"
    )

    # --------------------------------------------------------
    # Step 1: Initial cookie handling.
    # --------------------------------------------------------

    if cookie_overlay_visible(page):

        accepted = accept_cookies(
            page,
            wait_seconds=6,
        )

        if not accepted:

            raise RuntimeError(
                "Cookie overlay could not be dismissed."
            )

    # --------------------------------------------------------
    # Step 2: Move across complete price block.
    # --------------------------------------------------------

    move_across_price_block(
        page
    )

    # --------------------------------------------------------
    # Step 3: Find Reveal Price button.
    # --------------------------------------------------------

    button = find_reveal_button(
        page
    )

    if button is None:

        raise RuntimeError(
            "Reveal Price button was not found."
        )

    # --------------------------------------------------------
    # Step 4: Continuous movement over button.
    # --------------------------------------------------------

    continuously_move_over_reveal_button(
        page,
        seconds=2.0,
    )

    # --------------------------------------------------------
    # Step 5: Wait for activation while still moving.
    # --------------------------------------------------------

    button = wait_for_reveal_button_enabled(
        page,
        timeout_seconds=5,
    )

    # --------------------------------------------------------
    # Step 6: If not enabled, determine whether a cookie
    # appeared and recover once.
    # --------------------------------------------------------

    if button is None:

        if cookie_overlay_visible(
            page
        ):

            print(
                "  ├── cookie appeared during "
                "Reveal Price interaction"
            )

            accepted = accept_cookies(
                page,
                wait_seconds=6,
            )

            if not accepted:

                raise RuntimeError(
                    "Cookie appeared during Reveal Price "
                    "interaction and could not be dismissed."
                )

            # Start interaction again after cookie acceptance.
            continuously_move_over_reveal_button(
                page,
                seconds=2.0,
            )

            button = (
                wait_for_reveal_button_enabled(
                    page,
                    timeout_seconds=5,
                )
            )

        else:

            # No cookie. The site simply didn't activate
            # the button, so perform one additional movement pass.
            print(
                "  ├── Reveal Price not active yet, "
                "performing one more movement pass"
            )

            continuously_move_over_reveal_button(
                page,
                seconds=2.0,
            )

            button = (
                wait_for_reveal_button_enabled(
                    page,
                    timeout_seconds=5,
                )
            )

    if button is None:

        raise RuntimeError(
            "Reveal Price button remained disabled."
        )

    # --------------------------------------------------------
    # Step 7: Actual click with late-cookie recovery.
    # --------------------------------------------------------

    click_reveal_with_cookie_recovery(
        page
    )

    # --------------------------------------------------------
    # Step 8: Let asynchronous reveal finish.
    # --------------------------------------------------------

    page.wait_for_timeout(
        2000
    )

    print(
        "  └── waiting for revealed data"
    )


# ============================================================
# CURRENT PRICE
# ============================================================

def extract_current_price(page):

    selectors = [
        ".price-block .price-main b",
        ".price-block .price-main strong",
        ".price-main b",
        ".price-main strong",
        ".current-price",
        "[data-testid='current-price']",
    ]

    deadline = (
        time.time()
        + DATA_WAIT_SECONDS
    )

    while time.time() < deadline:

        # ----------------------------------------------------
        # Known selectors.
        # ----------------------------------------------------

        for selector in selectors:

            try:

                locator = page.locator(
                    selector
                )

                for index in range(
                    locator.count()
                ):

                    element = locator.nth(
                        index
                    )

                    if not element.is_visible():
                        continue

                    text = clean_text(
                        element.inner_text()
                    )

                    price = parse_money(
                        text
                    )

                    if (
                        price is not None
                        and price > 0
                    ):

                        print(
                            "  ├── extracted price:",
                            price
                        )

                        return price

            except Exception:
                continue

        # ----------------------------------------------------
        # Visible price-main fallback.
        # ----------------------------------------------------

        try:

            price_main = page.locator(
                ".price-main"
            ).first

            if (
                price_main.count() > 0
                and price_main.is_visible()
            ):

                text = clean_text(
                    price_main.inner_text()
                )

                price = parse_money(
                    text
                )

                if (
                    price is not None
                    and price > 0
                ):

                    print(
                        "  ├── extracted price:",
                        price
                    )

                    return price

        except Exception:
            pass

        # ----------------------------------------------------
        # Price block fallback.
        # ----------------------------------------------------

        try:

            price_block = page.locator(
                ".price-block"
            ).first

            if (
                price_block.count() > 0
                and price_block.is_visible()
            ):

                text = clean_text(
                    price_block.inner_text()
                )

                matches = re.findall(
                    r"(?:₹|Rs\.?|INR)\s*"
                    r"([0-9][0-9,]*"
                    r"(?:\.[0-9]+)?)",
                    text,
                    flags=re.IGNORECASE,
                )

                for value in matches:

                    price = parse_money(
                        value
                    )

                    if (
                        price is not None
                        and price > 0
                    ):

                        print(
                            "  ├── extracted price:",
                            price
                        )

                        return price

        except Exception:
            pass

        page.wait_for_timeout(
            300
        )

    return None


# ============================================================
# STOCK
# ============================================================

def extract_stock(page):

    selectors = [
        ".stock-badge",
        ".stock-status",
        ".stock",
        "[data-testid='stock']",
    ]

    deadline = (
        time.time()
        + DATA_WAIT_SECONDS
    )

    while time.time() < deadline:

        for selector in selectors:

            try:

                locator = page.locator(
                    selector
                )

                for index in range(
                    locator.count()
                ):

                    element = locator.nth(
                        index
                    )

                    if not element.is_visible():
                        continue

                    text = clean_text(
                        element.inner_text()
                    )

                    if not text:
                        continue

                    upper_text = text.upper()

                    if (
                        "STOCK" in upper_text
                        or "OUT OF STOCK"
                        in upper_text
                    ):

                        print(
                            "  ├── extracted stock:",
                            text
                        )

                        return text

            except Exception:
                continue

        # ----------------------------------------------------
        # Body text fallback.
        # ----------------------------------------------------

        try:

            body_text = clean_text(
                page.locator(
                    "body"
                ).inner_text()
            )

            patterns = [
                r"OUT OF STOCK",
                r"ONLY\s+\d+\s+LEFT",
                r"IN STOCK\s*[·\-:]?\s*\d+\s*LEFT",
                r"\d+\s+IN STOCK",
            ]

            for pattern in patterns:

                match = re.search(
                    pattern,
                    body_text,
                    flags=re.IGNORECASE,
                )

                if match:

                    stock = clean_text(
                        match.group(0)
                    )

                    print(
                        "  ├── extracted stock:",
                        stock
                    )

                    return stock

        except Exception:
            pass

        page.wait_for_timeout(
            300
        )

    return ""


# ============================================================
# OTHER PRODUCT VALUES
# ============================================================

def extract_original_price(page):

    selectors = [
        ".original-price",
        ".price-original",
        ".mrp",
        ".list-price",
    ]

    for selector in selectors:

        text = safe_visible_text(
            page,
            selector,
        )

        if text:

            price = parse_money(
                text
            )

            if price:
                return price

    try:
        body_text = clean_text(
            page.locator("body").inner_text()
        )

        match = re.search(
            r"₹\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s+Deal price",
            body_text,
            flags=re.IGNORECASE,
        )

        if match:
            return parse_money(match.group(1))

    except Exception:
        pass

    return None


def extract_deal_price(page):

    selectors = [
        ".deal-price",
        ".sale-price",
    ]

    for selector in selectors:

        text = safe_visible_text(
            page,
            selector,
        )

        if text:

            price = parse_money(
                text
            )

            if price:
                return price

    try:
        body_text = clean_text(
            page.locator("body").inner_text()
        )

        match = re.search(
            r"Deal price\s+₹\s*([0-9][0-9,]*(?:\.[0-9]+)?)",
            body_text,
            flags=re.IGNORECASE,
        )

        if match:
            return parse_money(match.group(1))

    except Exception:
        pass

    return None


def extract_discount(page):

    selectors = [
        ".discount",
        ".discount-badge",
        "[data-testid='discount']",
    ]

    for selector in selectors:

        text = safe_visible_text(
            page,
            selector,
        )

        if not text:
            continue

        match = re.search(
            r"(\d+(?:\.\d+)?)\s*%",
            text,
        )

        if match:

            try:

                return Decimal(
                    match.group(1)
                )

            except InvalidOperation:
                pass

    try:
        body_text = clean_text(
            page.locator("body").inner_text()
        )

        match = re.search(
            r"(\d+(?:\.\d+)?)\s*%\s*off",
            body_text,
            flags=re.IGNORECASE,
        )

        if match:
            return Decimal(match.group(1))

    except Exception:
        pass

    return None


# ============================================================
# RESULT VALIDATION
# ============================================================

def validate_result(
    price,
    stock,
):

    if (
        price is None
        or price <= 0
    ):

        raise RuntimeError(
            "Current price could not be extracted correctly."
        )

    if not stock:

        raise RuntimeError(
            "Stock information could not be extracted correctly."
        )


# ============================================================
# DIRECT PRODUCT SCRAPER
# ============================================================

def scrape_product_by_id(
    product_id,
    headless=True,
    max_attempts=DEFAULT_MAX_ATTEMPTS,
):

    product_id = int(
        product_id
    )

    product_url = (
        f"{STORE_BASE_URL}"
        f"/product/{product_id}"
    )

    scrape_mode = (
        "headless"
        if headless
        else "headed"
    )

    print("=" * 60)
    print(
        "STARTING DIRECT PRODUCT SCRAPE"
    )
    print(
        "INE Product ID:",
        product_id,
    )
    print(
        "URL:",
        product_url,
    )
    print(
        "Maximum attempts:",
        max_attempts,
    )
    print(
        "Browser mode:",
        scrape_mode,
    )
    print("=" * 60)

    attempts = []
    api_product = {
        "id": product_id,
        "url": product_url,
    }

    try:
        api_product.update(
            fetch_product_api_details(
                product_id
            )
        )

        print(
            "Loaded product metadata from API:",
            api_product.get("name") or product_id,
        )

    except Exception as error:
        print(
            "Product metadata API lookup failed:",
            clean_text(str(error)),
        )

    with sync_playwright() as playwright:

        browser = playwright.chromium.launch(
            headless=headless
        )

        try:

            for attempt_number in range(
                1,
                max_attempts + 1,
            ):

                start_time = (
                    time.perf_counter()
                )

                print("")
                print(
                    f"ATTEMPT "
                    f"{attempt_number}/"
                    f"{max_attempts}"
                )

                context = browser.new_context(
                    viewport={
                        "width": 1440,
                        "height": 900,
                    }
                )

                page = context.new_page()

                try:

                    # =================================================
                    # 1. OPEN DIRECT PRODUCT PAGE
                    # =================================================

                    print(
                        "  ├── opening direct product URL"
                    )

                    page.goto(
                        product_url,
                        wait_until="domcontentloaded",
                        timeout=DEFAULT_TIMEOUT,
                    )

                    # Allow JS to initialise.
                    page.wait_for_timeout(
                        1500
                    )

                    # =================================================
                    # 2. INITIAL COOKIE CHECK
                    # =================================================

                    if cookie_overlay_visible(
                        page
                    ):

                        accepted = (
                            accept_cookies(
                                page,
                                wait_seconds=6,
                            )
                        )

                        if not accepted:

                            raise RuntimeError(
                                "Initial cookie overlay "
                                "could not be dismissed."
                            )

                    else:

                        print(
                            "  ├── no cookie banner at initial load"
                        )

                    # =================================================
                    # 3. VERIFY PRODUCT ID
                    # =================================================

                    actual_product_id = (
                        extract_product_id(
                            page.url
                        )
                    )

                    if (
                        actual_product_id
                        != product_id
                    ):

                        raise RuntimeError(
                            f"Opened product "
                            f"{actual_product_id}, "
                            f"expected product "
                            f"{product_id}."
                        )

                    print(
                        "  ├── confirmed product ID:",
                        actual_product_id,
                    )

                    # =================================================
                    # 4. WAIT FOR PRICE BLOCK
                    # =================================================

                    page.locator(
                        ".price-block"
                    ).first.wait_for(
                        state="visible",
                        timeout=20000,
                    )

                    print(
                        "  ├── product page loaded"
                    )

                    # =================================================
                    # 5. PRODUCT METADATA
                    # =================================================

                    product = dict(api_product)
                    product["url"] = page.url

                    product = (
                        extract_product_page_details(
                            page,
                            product,
                        )
                    )

                    # =================================================
                    # 6. REVEAL PRICE
                    # =================================================

                    reveal_price(
                        page
                    )

                    # =================================================
                    # 7. EXTRACT PRICE + STOCK
                    # =================================================

                    price = (
                        extract_current_price(
                            page
                        )
                    )

                    stock = (
                        extract_stock(
                            page
                        )
                    )

                    original_price = (
                        extract_original_price(
                            page
                        )
                    )

                    deal_price = (
                        extract_deal_price(
                            page
                        )
                    )

                    discount = (
                        extract_discount(
                            page
                        )
                    )

                    # =================================================
                    # 8. VALIDATE
                    # =================================================

                    validate_result(
                        price,
                        stock,
                    )

                    product["price"] = price
                    product["stock"] = stock

                    if original_price is not None:

                        product[
                            "original_price"
                        ] = original_price

                    if deal_price is not None:

                        product[
                            "deal_price"
                        ] = deal_price

                    if discount is not None:

                        product[
                            "discount"
                        ] = discount

                    # =================================================
                    # 9. SUCCESS
                    # =================================================

                    duration_ms = int(
                        (
                            time.perf_counter()
                            - start_time
                        )
                        * 1000
                    )

                    success_result = {
                        "status": "Success",
                        "product": product,
                        "details": (
                            f"Product scraped successfully in "
                            f"{scrape_mode} mode."
                        ),
                        "duration_ms": duration_ms,
                        "attempt_number": (
                            attempt_number
                        ),
                        "mode": scrape_mode,
                    }

                    attempts.append(
                        success_result
                    )

                    print("")
                    print(
                        "  ├── PRICE:",
                        price,
                    )

                    print(
                        "  ├── STOCK:",
                        stock,
                    )

                    print(
                        "  ├── duration:",
                        f"{duration_ms}ms",
                    )

                    print(
                        "  └── SUCCESS"
                    )

                    break

                except Exception as error:

                    duration_ms = int(
                        (
                            time.perf_counter()
                            - start_time
                        )
                        * 1000
                    )

                    error_message = clean_text(
                        str(error)
                    )

                    attempt_status = (
                        "Retried"
                        if (
                            attempt_number
                            < max_attempts
                        )
                        else "Failed"
                    )

                    attempts.append(
                        {
                            "status": attempt_status,
                            "product": None,
                            "details": (
                                f"{scrape_mode} mode: "
                                f"{error_message}"
                            ),
                            "duration_ms": duration_ms,
                            "attempt_number": (
                                attempt_number
                            ),
                            "mode": scrape_mode,
                        }
                    )

                    print(
                        "  ├── FAILED"
                    )

                    print(
                        "  ├── reason:",
                        error_message,
                    )

                    print(
                        "  └── duration:",
                        f"{duration_ms}ms",
                    )

                    if (
                        attempt_number
                        < max_attempts
                    ):

                        wait_seconds = (
                            attempt_number
                        )

                        print(
                            f"      waiting "
                            f"{wait_seconds}s "
                            f"before retry..."
                        )

                        time.sleep(
                            wait_seconds
                        )

                finally:

                    context.close()

        finally:

            browser.close()

    successful_attempt = next(
        (
            attempt
            for attempt in attempts
            if attempt["status"]
            == "Success"
        ),
        None,
    )

    print("")
    print("=" * 60)

    if successful_attempt:

        print(
            "DIRECT SCRAPE FINISHED: SUCCESS"
        )

    else:

        print(
            "DIRECT SCRAPE FINISHED: FAILED"
        )

    print("=" * 60)

    return {
        "success": (
            successful_attempt
            is not None
        ),
        "mode": scrape_mode,
        "product": (
            successful_attempt["product"]
            if successful_attempt
            else None
        ),
        "attempts": attempts,
    }


# ============================================================
# LEGACY NAME-BASED SCRAPER
# ============================================================

def scrape_product_by_name(
    search_name,
    headless=True,
    max_attempts=DEFAULT_MAX_ATTEMPTS,
):

    search_name = clean_text(
        search_name
    )

    if not search_name:

        return {
            "success": False,
            "product": None,
            "attempts": [
                {
                    "status": "Failed",
                    "product": None,
                    "details": "Search name is empty.",
                    "duration_ms": 0,
                    "attempt_number": 1,
                }
            ],
        }

    print("=" * 60)
    print(
        "STARTING NAME-BASED PRODUCT DISCOVERY"
    )
    print(
        "Search name:",
        search_name,
    )
    print("=" * 60)

    catalog = []

    with sync_playwright() as playwright:

        browser = playwright.chromium.launch(
            headless=headless
        )

        context = browser.new_context(
            viewport={
                "width": 1440,
                "height": 900,
            }
        )

        page = context.new_page()

        try:

            catalog = (
                discover_homepage_catalog(
                    page
                )
            )

        finally:

            context.close()
            browser.close()

    search_lower = (
        search_name.lower()
    )

    target = None

    for item in catalog:

        item_name = clean_text(
            item.get(
                "name",
                "",
            )
        ).lower()

        if search_lower in item_name:

            target = item
            break

    if target is None:

        return {
            "success": False,
            "product": None,
            "attempts": [
                {
                    "status": "Failed",
                    "product": None,
                    "details": (
                        f'Product "{search_name}" '
                        f'was not found in catalog.'
                    ),
                    "duration_ms": 0,
                    "attempt_number": 1,
                }
            ],
        }

    return scrape_product_by_id(
        product_id=int(
            target["id"]
        ),
        headless=headless,
        max_attempts=max_attempts,
    )


# ============================================================
# COMMAND LINE TESTING
# ============================================================

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description="INE product scraper"
    )

    parser.add_argument(
        "--id",
        type=int,
        help="Scrape a known INE product ID",
    )

    parser.add_argument(
        "--name",
        type=str,
        help="Find product by name and scrape it",
    )

    parser.add_argument(
        "--headed",
        action="store_true",
        help="Show Chromium browser",
    )

    args = parser.parse_args()

    if args.id is not None:

        result = scrape_product_by_id(
            product_id=args.id,
            headless=not args.headed,
        )

    elif args.name:

        result = scrape_product_by_name(
            search_name=args.name,
            headless=not args.headed,
        )

    else:

        parser.error(
            "Use either --id PRODUCT_ID "
            "or --name PRODUCT_NAME"
        )

    print("")

    print(
        json.dumps(
            result,
            indent=2,
            default=str,
        )
    )
