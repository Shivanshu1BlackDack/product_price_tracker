import json
import ssl
import time
from decimal import Decimal
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from .models import Product


STORE_BASE_URL = "https://demo.inelabteamdev.com"
CATALOG_API_URL = f"{STORE_BASE_URL}/api/catalog"
PRODUCT_API_URL = f"{STORE_BASE_URL}/api/product"


FALLBACK_CATALOG = [
    {
        "id": 10877,
        "name": "Vista Sneaker XL",
        "sku": "VIS-10877",
        "brand": "Vista",
        "category": "Footwear",
        "url": "https://demo.inelabteamdev.com/product/10877",
        "seller": "Quillon Direct",
        "current_price": "15745.00",
        "original_price": "19990.00",
        "deal_price": "17838.00",
        "discount": "15.00",
        "stock": "ONLY 165 LEFT",
        "delivery": "Mon, 21 Sept",
        "description": (
            "The Vista Sneaker XL. A dependable footwear pick "
            "with a clean, no-nonsense design and everyday features "
            "you actually use."
        ),
        "about": (
            "The Vista Sneaker XL is part of our everyday footwear "
            "range. It is built around the features people actually "
            "reach for, without the ones they never use, and it is "
            "designed to keep working after the novelty wears off. "
            "Pricing and availability on this page are live and can "
            "change during the day."
        ),
        "specifications": {
            "Warranty": "1 year manufacturer warranty",
            "In the box": (
                "Sneaker, Care card, Sizing guide, Spare laces, Dust bag"
            ),
            "Country of origin": "Vietnam",
            "Returns": "7-day replacement, unopened",
            "Support": "Phone support, 9am-6pm IST, weekdays only",
            "Weight": "1.04 kg",
            "Material": "EVA and rubber",
            "Colour": "Pewter",
            "Model year": "2023",
        },
    },
]


def to_decimal(value):
    if value in [None, ""]:
        return None

    try:
        return Decimal(str(value))
    except Exception:
        return None


def api_get_json(url, attempts=2, timeout=10):
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": (
                "Mozilla/5.0 ProductPriceTracker/1.0"
            ),
        },
    )

    context = ssl._create_unverified_context()

    last_error = None

    for attempt in range(1, attempts + 1):
        try:
            with urlopen(
                request,
                timeout=timeout,
                context=context,
            ) as response:
                return json.loads(
                    response.read().decode("utf-8")
                )

        except Exception as error:
            last_error = error

            if attempt < attempts:
                time.sleep(attempt * 0.25)

    raise last_error


def titleise_key(value):
    text = str(value or "").strip()

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


def normalise_specs(specs):
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


def normalise_api_product(item):
    product_id = item.get("id")

    if not product_id:
        return None

    slug = item.get("slug") or ""
    url = (
        item.get("url")
        or item.get("href")
        or item.get("link")
        or f"/product/{product_id}"
    )

    if not str(url).startswith("http"):
        url = urljoin(
            STORE_BASE_URL,
            str(url),
        )

    return {
        "id": int(product_id),
        "slug": slug,
        "name": (item.get("name") or "").strip(),
        "sku": (item.get("sku") or "").strip(),
        "brand": (item.get("brand") or "").strip(),
        "category": (item.get("category") or "").strip(),
        "url": url,
        "description": (
            item.get("description") or ""
        ).strip(),
        "specifications": normalise_specs(
            item.get("specs")
        ),
    }


def fetch_catalog_from_api(page_size=60, max_rounds=12):
    unique = {}
    total = None
    pages = None

    for _round in range(max_rounds):
        found_before_round = len(unique)
        page = 1

        while pages is None or page <= pages:
            try:
                payload = api_get_json(
                    (
                        f"{CATALOG_API_URL}"
                        f"?page={page}&pageSize={page_size}"
                    ),
                    attempts=2,
                    timeout=8,
                )
            except Exception:
                page += 1
                continue

            pages = int(
                payload.get("pages") or pages or 1
            )

            total = int(
                payload.get("total") or total or 0
            )

            for item in payload.get("items") or []:
                product = normalise_api_product(item)

                if product and product["name"]:
                    unique[product["id"]] = product

            page += 1

        if total and len(unique) >= total:
            break

        if len(unique) == found_before_round:
            break

        pages = None

    return [
        unique[product_id]
        for product_id in sorted(unique)
    ]


def fetch_product_details_from_api(product_id):
    payload = api_get_json(
        f"{PRODUCT_API_URL}/{int(product_id)}",
        attempts=2,
        timeout=8,
    )

    return normalise_api_product(payload) or {}


def upsert_catalog_products(products):
    created_count = 0
    updated_count = 0

    for item in products:

        store_product_id = item.get("id")
        name = item.get("name", "").strip()

        if not store_product_id or not name:
            continue

        sku = (
            item.get("sku") or ""
        ).strip()

        brand = (
            item.get("brand") or ""
        ).strip()

        category = (
            item.get("category") or ""
        ).strip()

        url = (
            item.get("url")
            or f"{STORE_BASE_URL}/product/{store_product_id}"
        )

        product = Product.objects.filter(
            store_product_id=store_product_id
        ).first()

        if product is None and sku:
            product = Product.objects.filter(
                sku=sku
            ).first()

        if product is None:

            Product.objects.create(
                store_product_id=store_product_id,
                name=name,
                brand=brand,
                category=category,
                sku=sku or f"INE-{store_product_id}",
                url=url,
                seller=item.get("seller", ""),
                current_price=to_decimal(
                    item.get("current_price")
                    or item.get("price")
                ),
                original_price=to_decimal(
                    item.get("original_price")
                ),
                deal_price=to_decimal(
                    item.get("deal_price")
                ),
                discount=to_decimal(
                    item.get("discount")
                ),
                stock=item.get("stock", ""),
                delivery=item.get("delivery", ""),
                description=item.get(
                    "description",
                    "",
                ),
                about=item.get("about", ""),
                specifications=item.get(
                    "specifications",
                    {},
                ),
                is_tracked=False,
            )

            created_count += 1

        else:

            product.store_product_id = (
                store_product_id
            )

            product.name = name

            if brand:
                product.brand = brand

            if category:
                product.category = category

            if sku:
                product.sku = sku

            product.url = url

            if item.get("seller") and not product.seller:
                product.seller = item["seller"]

            if (
                product.current_price is None
                and (
                    item.get("current_price")
                    or item.get("price")
                )
            ):
                product.current_price = to_decimal(
                    item.get("current_price")
                    or item.get("price")
                )

            if (
                product.original_price is None
                and item.get("original_price")
            ):
                product.original_price = to_decimal(
                    item.get("original_price")
                )

            if (
                product.deal_price is None
                and item.get("deal_price")
            ):
                product.deal_price = to_decimal(
                    item.get("deal_price")
                )

            if (
                product.discount is None
                and item.get("discount")
            ):
                product.discount = to_decimal(
                    item.get("discount")
                )

            if item.get("stock") and not product.stock:
                product.stock = item["stock"]

            if item.get("delivery") and not product.delivery:
                product.delivery = item["delivery"]

            if (
                item.get("description")
                and not product.description
            ):
                product.description = item["description"]

            if item.get("about") and not product.about:
                product.about = item["about"]

            if (
                item.get("specifications")
                and not product.specifications
            ):
                product.specifications = (
                    item["specifications"]
                )

            product.save()

            updated_count += 1

    return created_count, updated_count


def seed_fallback_catalog(reason=""):
    created_count, updated_count = upsert_catalog_products(
        FALLBACK_CATALOG
    )

    return {
        "total": len(FALLBACK_CATALOG),
        "created": created_count,
        "updated": updated_count,
        "fallback": True,
        "reason": reason,
    }


def sync_catalog_from_store():
    """
    Fetch product metadata from the INE storefront and
    synchronize it into our Product table.

    This is catalog discovery only.
    It does NOT reveal prices and does NOT perform product
    scraping.
    """

    print()
    print("=" * 60)
    print("CATALOG SYNC STARTED")
    print("=" * 60)

    try:
        products = fetch_catalog_from_api()

        if products:
            created_count, updated_count = upsert_catalog_products(
                products
            )

            print()
            print(
                f"Catalog API records received: {len(products)}"
            )
            print(f"Created: {created_count}")
            print(f"Updated: {updated_count}")
            print("=" * 60)

            return {
                "total": len(products),
                "created": created_count,
                "updated": updated_count,
                "source": "api",
            }

    except Exception as api_error:
        print(
            "Catalog API sync failed:",
            str(api_error),
        )

    from playwright.sync_api import sync_playwright
    from scraper.scraper import discover_homepage_catalog

    try:

        with sync_playwright() as playwright:

            browser = playwright.chromium.launch(
                headless=True
            )

            context = browser.new_context(
                viewport={
                    "width": 1440,
                    "height": 900,
                }
            )

            page = context.new_page()

            try:
                products = discover_homepage_catalog(
                    page
                )

            finally:
                context.close()
                browser.close()

    except Exception as error:

        return seed_fallback_catalog(
            reason=str(error)
        )

    if not products:
        return seed_fallback_catalog(
            reason="Store catalog discovery returned no products."
        )

    created_count, updated_count = upsert_catalog_products(
        products
    )

    print()
    print(
        f"Catalog records received: {len(products)}"
    )

    print(
        f"Created: {created_count}"
    )

    print(
        f"Updated: {updated_count}"
    )

    print(
        "=" * 60
    )

    return {
        "total": len(products),
        "created": created_count,
        "updated": updated_count,
        "source": "browser",
    }
