from decimal import Decimal, InvalidOperation

from django.db.models import Q
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .catalog import (
    fetch_product_details_from_api,
    sync_catalog_from_store,
)
from .models import (
    Product,
    PriceHistory,
    StockHistory,
    ScrapeAttempt,
)
from .serializers import (
    ProductSerializer,
    PriceHistorySerializer,
    StockHistorySerializer,
    ScrapeAttemptSerializer,
)


# ============================================================
# HELPERS
# ============================================================

def to_decimal(value):
    if value is None or value == "":
        return None

    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def update_product_from_scrape(
    product,
    scraped_product,
):
    """
    Save successfully scraped information into the database.

    Also records price and stock history.
    """

    if not scraped_product:
        return

    # --------------------------------------------------------
    # Metadata
    # --------------------------------------------------------

    if scraped_product.get("name"):
        product.name = scraped_product["name"]

    if scraped_product.get("brand"):
        product.brand = scraped_product["brand"]

    if scraped_product.get("category"):
        product.category = scraped_product["category"]

    if scraped_product.get("sku"):
        new_sku = str(
            scraped_product["sku"]
        ).strip()

        existing_sku_product = (
            Product.objects
            .filter(sku=new_sku)
            .exclude(id=product.id)
            .first()
        )

        if existing_sku_product is None:
            product.sku = new_sku

    if scraped_product.get("url"):
        product.url = scraped_product["url"]

    if scraped_product.get("image"):
        product.image = scraped_product["image"]

    if scraped_product.get("seller"):
        product.seller = scraped_product["seller"]

    if scraped_product.get("delivery"):
        product.delivery = scraped_product["delivery"]

    if scraped_product.get("description"):
        product.description = (
            scraped_product["description"]
        )

    if scraped_product.get("about"):
        product.about = scraped_product["about"]

    if isinstance(
        scraped_product.get("specifications"),
        dict,
    ):
        product.specifications = (
            scraped_product["specifications"]
        )

    # --------------------------------------------------------
    # Dynamic price/stock
    # --------------------------------------------------------

    current_price = to_decimal(
        scraped_product.get("price")
    )

    original_price = to_decimal(
        scraped_product.get(
            "original_price"
        )
    )

    deal_price = to_decimal(
        scraped_product.get(
            "deal_price"
        )
    )

    discount = to_decimal(
        scraped_product.get(
            "discount"
        )
    )

    stock = scraped_product.get(
        "stock"
    )

    if current_price is not None:
        product.current_price = current_price

    if original_price is not None:
        product.original_price = original_price

    if deal_price is not None:
        product.deal_price = deal_price

    if discount is not None:
        product.discount = discount

    if stock:
        product.stock = str(stock)

    product.last_scraped_at = timezone.now()

    product.save()

    # Keep a time-series record only after a validated successful scrape.
    # Failed scrape attempts are persisted separately by save_scrape_attempts.
    if current_price is not None:

        PriceHistory.objects.create(
            product=product,
            price=current_price,
        )

    if stock:

        StockHistory.objects.create(
            product=product,
            stock=str(stock),
        )


def hydrate_product_metadata(product):
    if not product.store_product_id:
        return product

    if (
        product.specifications
        and product.description
        and product.category
        and product.brand
    ):
        return product

    try:
        details = fetch_product_details_from_api(
            product.store_product_id
        )
    except Exception:
        return product

    changed_fields = []

    for field in [
        "name",
        "brand",
        "category",
        "sku",
        "url",
        "description",
        "specifications",
    ]:
        value = details.get(field)

        if value in [None, "", {}]:
            continue

        if getattr(product, field) != value:
            setattr(product, field, value)
            changed_fields.append(field)

    if changed_fields:
        product.save(
            update_fields=changed_fields
            + ["updated_at"]
        )

    return product


def save_scrape_attempts(
    product,
    attempts,
):
    """
    Save every attempt, including:
    - Success
    - Retried
    - Failed
    """

    for attempt in attempts:

        ScrapeAttempt.objects.create(
            product=product,
            attempt_number=attempt.get(
                "attempt_number",
                1,
            ),
            status=attempt.get(
                "status",
                "Failed",
            ),
            details=attempt.get(
                "details",
                "",
            ),
            duration_ms=attempt.get(
                "duration_ms"
            ),
        )


def run_direct_scrape(
    product,
    headless=True,
    max_attempts=3,
):
    """
    Always scrape the known INE product ID.

    IMPORTANT:
    No homepage name search is performed here.
    """

    if not product.store_product_id:

        raise ValueError(
            "Product does not have a stored INE product ID."
        )

    from scraper.scraper import scrape_product_by_id

    return scrape_product_by_id(
        product_id=product.store_product_id,
        headless=headless,
        max_attempts=max_attempts,
    )


# ============================================================
# SEARCH
# ============================================================

@api_view(["GET"])
def search_products(request):
    """
    Search local catalog by partial/full text.

    If the local catalog is empty, sync it from the INE store.
    If no results are found, retry once after a catalog sync.
    """

    query = request.GET.get(
        "q",
        "",
    ).strip()

    if not query:

        return Response(
            [],
            status=status.HTTP_200_OK,
        )

    def find_matches():
        return (
            Product.objects
            .filter(
                Q(name__icontains=query)
                | Q(brand__icontains=query)
                | Q(category__icontains=query)
                | Q(sku__icontains=query)
            )
            .order_by("name")
        )

    if not Product.objects.exists():
        try:
            sync_catalog_from_store()
        except Exception as error:
            return Response(
                {
                    "error": "Catalog sync failed.",
                    "details": str(error),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    products = find_matches()

    if not products.exists():
        try:
            sync_catalog_from_store()
        except Exception:
            pass

        products = find_matches()

    serializer = ProductSerializer(
        products,
        many=True,
    )

    return Response(
        serializer.data,
        status=status.HTTP_200_OK,
    )


# ============================================================
# CATALOG
# ============================================================

@api_view(["GET"])
def catalog_products(request):
    """
    Return locally stored catalog products.

    If database is empty, perform initial catalog sync.
    """

    if not Product.objects.exists():

        try:

            result = (
                sync_catalog_from_store()
            )

            print(
                "Initial catalog sync:",
                result,
            )

        except Exception as error:

            return Response(
                {
                    "error": "Catalog sync failed.",
                    "details": str(error),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    products = (
        Product.objects
        .all()
        .order_by("name")
    )

    serializer = ProductSerializer(
        products,
        many=True,
    )

    return Response(
        serializer.data,
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
def sync_catalog(request):

    try:

        result = (
            sync_catalog_from_store()
        )

        return Response(
            result,
            status=status.HTTP_200_OK,
        )

    except Exception as error:

        return Response(
            {
                "error": "Catalog sync failed.",
                "details": str(error),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ============================================================
# OPTIONAL NAME-BASED DISCOVERY
# ============================================================

@api_view(["GET"])
def discover_product(request):
    """
    Legacy/manual endpoint.

    Normal search does not use this endpoint.
    """

    name = request.GET.get(
        "name",
        "",
    ).strip()

    if not name:

        return Response(
            {
                "error": (
                    "Please provide a product name."
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:

        from scraper.scraper import scrape_product_by_name

        result = scrape_product_by_name(
            search_name=name,
            headless=True,
            max_attempts=3,
        )

        if not result.get("success"):

            return Response(
                result,
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(
            result,
            status=status.HTTP_200_OK,
        )

    except Exception as error:

        return Response(
            {
                "error": str(error),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ============================================================
# TRACK PRODUCT
# ============================================================

@api_view(["POST"])
def track_product(request):

    print("")
    print("=" * 60)
    print("TRACK PRODUCT")
    print("=" * 60)

    local_product_id = request.data.get(
        "product_id"
    )

    store_product_id = request.data.get(
        "store_product_id"
    )

    if (
        not local_product_id
        and not store_product_id
    ):

        return Response(
            {
                "error": (
                    "Provide product_id or "
                    "store_product_id."
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # --------------------------------------------------------
    # Find our local DB product
    # --------------------------------------------------------

    product = None

    if local_product_id:

        product = (
            Product.objects
            .filter(
                id=local_product_id
            )
            .first()
        )

    if (
        product is None
        and store_product_id
    ):

        product = (
            Product.objects
            .filter(
                store_product_id=store_product_id
            )
            .first()
        )

    if product is None:

        return Response(
            {
                "error": (
                    "Product was not found "
                    "in local database."
                )
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    print(
        "Database ID:",
        product.id,
    )

    print(
        "INE Product ID:",
        product.store_product_id,
    )

    print(
        "Product:",
        product.name,
    )

    if not product.store_product_id:

        return Response(
            {
                "error": (
                    "Product does not have "
                    "a stored INE product ID."
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # --------------------------------------------------------
    # Mark tracked
    # --------------------------------------------------------

    product.is_tracked = True

    product.save(
        update_fields=[
            "is_tracked"
        ]
    )

    print("")
    print(
        "Starting first tracking scrape..."
    )

    print(
        "Using direct INE product ID:",
        product.store_product_id,
    )

    # --------------------------------------------------------
    # FIRST SCRAPE
    # --------------------------------------------------------

    try:

        result = run_direct_scrape(
            product,
            headless=True,
        )

    except Exception as error:

        failed_attempt = {
            "status": "Failed",
            "product": None,
            "details": (
                f"headless mode: scraper could not be started. {error}"
            ),
            "duration_ms": 0,
            "attempt_number": 1,
            "mode": "headless",
        }

        save_scrape_attempts(
            product,
            [failed_attempt],
        )

        return Response(
            {
                "success": True,
                "scrape_success": False,
                "message": (
                    "Product is now being tracked, "
                    "but the first scrape failed."
                ),
                "details": str(error),
                "product": ProductSerializer(
                    product
                ).data,
                "mode": "headless",
                "attempts": [failed_attempt],
            },
            status=status.HTTP_200_OK,
        )

    # --------------------------------------------------------
    # SAVE ALL ATTEMPTS
    # --------------------------------------------------------

    save_scrape_attempts(
        product,
        result.get(
            "attempts",
            [],
        ),
    )

    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    if result.get("success"):

        update_product_from_scrape(
            product,
            result.get(
                "product"
            ),
        )

        print("")
        print(
            "Tracking started successfully."
        )

        return Response(
            {
                "success": True,
                "scrape_success": True,
                "message": (
                    "Product is now being tracked."
                ),
                "product": ProductSerializer(
                    product
                ).data,
                "mode": result.get(
                    "mode",
                    "headless",
                ),
                "attempts": result.get(
                    "attempts",
                    [],
                ),
            },
            status=status.HTTP_200_OK,
        )

    # --------------------------------------------------------
    # SCRAPE FAILED
    # Product remains tracked.
    # No fake data is stored.
    # --------------------------------------------------------

    print("")
    print(
        "Initial tracking scrape failed."
    )

    return Response(
        {
            "success": True,
            "scrape_success": False,
            "message": (
                "Product was added to tracking, "
                "but the initial scrape failed."
            ),
            "product": ProductSerializer(
                product
            ).data,
            "mode": result.get(
                "mode",
                "headless",
            ),
            "attempts": result.get(
                "attempts",
                [],
            ),
        },
        status=status.HTTP_200_OK,
    )


# ============================================================
# TRACKED PRODUCTS
# ============================================================

@api_view(["GET"])
def tracked_products(request):

    products = (
        Product.objects
        .filter(
            is_tracked=True
        )
        .order_by(
            "-updated_at"
        )
    )

    serializer = ProductSerializer(
        products,
        many=True,
    )

    return Response(
        serializer.data,
        status=status.HTTP_200_OK,
    )


# ============================================================
# PRODUCT DETAIL / UNTRACK
# ============================================================

@api_view(["GET", "DELETE"])
def product_detail(
    request,
    product_id,
):

    product = (
        Product.objects
        .filter(
            id=product_id
        )
        .first()
    )

    if product is None:

        return Response(
            {
                "error": "Product not found."
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    # DELETE means untrack.
    if request.method == "DELETE":

        product.is_tracked = False

        product.save(
            update_fields=[
                "is_tracked"
            ]
        )

        return Response(
            {
                "success": True,
                "message": (
                    "Product removed from tracking."
                ),
            },
            status=status.HTTP_200_OK,
        )

    product = hydrate_product_metadata(
        product
    )

    serializer = ProductSerializer(product)

    return Response(
        serializer.data,
        status=status.HTTP_200_OK,
    )


# ============================================================
# PRICE HISTORY
# ============================================================

@api_view(["GET"])
def price_history(
    request,
    product_id,
):

    product = (
        Product.objects
        .filter(
            id=product_id
        )
        .first()
    )

    if product is None:

        return Response(
            {
                "error": "Product not found."
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    history = (
        PriceHistory.objects
        .filter(
            product=product
        )
        .order_by(
            "scraped_at"
        )
    )

    serializer = PriceHistorySerializer(
        history,
        many=True,
    )

    return Response(
        serializer.data,
        status=status.HTTP_200_OK,
    )


# ============================================================
# STOCK HISTORY
# ============================================================

@api_view(["GET"])
def stock_history(
    request,
    product_id,
):

    product = (
        Product.objects
        .filter(
            id=product_id
        )
        .first()
    )

    if product is None:

        return Response(
            {
                "error": "Product not found."
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    history = (
        StockHistory.objects
        .filter(
            product=product
        )
        .order_by(
            "scraped_at"
        )
    )

    serializer = StockHistorySerializer(
        history,
        many=True,
    )

    return Response(
        serializer.data,
        status=status.HTTP_200_OK,
    )


# ============================================================
# PRODUCT SCRAPE LOGS
# ============================================================

@api_view(["GET"])
def scrape_logs(
    request,
    product_id,
):

    product = (
        Product.objects
        .filter(
            id=product_id
        )
        .first()
    )

    if product is None:

        return Response(
            {
                "error": "Product not found."
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    logs = (
        ScrapeAttempt.objects
        .filter(
            product=product
        )
        .order_by(
            "-created_at"
        )
    )

    serializer = ScrapeAttemptSerializer(
        logs,
        many=True,
    )

    return Response(
        serializer.data,
        status=status.HTTP_200_OK,
    )


# ============================================================
# ALL SCRAPE LOGS
# ============================================================

@api_view(["GET"])
def all_scrape_logs(request):

    logs = (
        ScrapeAttempt.objects
        .select_related(
            "product"
        )
        .order_by(
            "-created_at"
        )
    )

    serializer = ScrapeAttemptSerializer(
        logs,
        many=True,
    )

    return Response(
        serializer.data,
        status=status.HTTP_200_OK,
    )


# ============================================================
# SCRAPE NOW
# ============================================================

@api_view(["POST"])
def scrape_product(
    request,
    product_id,
):

    product = (
        Product.objects
        .filter(
            id=product_id
        )
        .first()
    )

    if product is None:

        return Response(
            {
                "error": "Product not found."
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    if not product.store_product_id:

        return Response(
            {
                "error": (
                    "Product does not have "
                    "a stored INE product ID."
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    print("")
    print("=" * 60)
    print("SCRAPE NOW")
    print("=" * 60)

    print(
        "Database ID:",
        product.id,
    )

    print(
        "INE Product ID:",
        product.store_product_id,
    )

    print(
        "Product:",
        product.name,
    )

    headed_requested = (
        request.data.get("headed") is True
        or request.query_params.get("headed")
        in ["1", "true", "True", "yes"]
    )

    try:

        result = run_direct_scrape(
            product,
            headless=not headed_requested,
        )

    except Exception as error:

        mode = (
            "headed"
            if headed_requested
            else "headless"
        )

        failed_attempt = {
            "status": "Failed",
            "product": None,
            "details": (
                f"{mode} mode: scraper could not be started. {error}"
            ),
            "duration_ms": 0,
            "attempt_number": 1,
            "mode": mode,
        }

        save_scrape_attempts(
            product,
            [failed_attempt],
        )

        return Response(
            {
                "success": False,
                "message": (
                    "Product scrape failed before browser launch."
                ),
                "details": str(error),
                "product": ProductSerializer(
                    product
                ).data,
                "mode": mode,
                "attempts": [failed_attempt],
            },
            status=status.HTTP_200_OK,
        )

    save_scrape_attempts(
        product,
        result.get(
            "attempts",
            [],
        ),
    )

    if result.get("success"):

        update_product_from_scrape(
            product,
            result.get(
                "product"
            ),
        )

        return Response(
            {
                "success": True,
                "message": (
                    "Product scraped successfully."
                ),
                "product": ProductSerializer(
                    product
                ).data,
                "mode": result.get(
                    "mode",
                    "headless",
                ),
                "attempts": result.get(
                    "attempts",
                    [],
                ),
            },
            status=status.HTTP_200_OK,
        )

    return Response(
        {
            "success": False,
            "message": (
                "Product scrape failed."
            ),
            "product": ProductSerializer(
                product
            ).data,
            "mode": result.get(
                "mode",
                "headless",
            ),
            "attempts": result.get(
                "attempts",
                [],
            ),
        },
        status=status.HTTP_200_OK,
    )


# ============================================================
# SCRAPE ALL TRACKED PRODUCTS
# ============================================================

def run_all_tracked_scrapes():
    """
    Scrape every tracked product once in headless mode.

    This shared job is used by the HTTP cron endpoint and by the local
    management commands, keeping manual scheduling and hosted cron runs
    on the same validated save path.
    """

    products = (
        Product.objects
        .filter(
            is_tracked=True
        )
        .order_by("id")
    )

    results = []

    for product in products:

        print("")
        print("=" * 60)
        print(
            "SCRAPING TRACKED PRODUCT"
        )
        print("=" * 60)

        print(
            "Product:",
            product.name,
        )

        print(
            "INE Product ID:",
            product.store_product_id,
        )

        try:

            result = run_direct_scrape(
                product,
                headless=True,
            )

            save_scrape_attempts(
                product,
                result.get(
                    "attempts",
                    [],
                ),
            )

            if result.get("success"):

                update_product_from_scrape(
                    product,
                    result.get(
                        "product"
                    ),
                )

            results.append(
                {
                    "product_id": product.id,
                    "store_product_id": (
                        product.store_product_id
                    ),
                    "product": product.name,
                    "success": result.get(
                        "success",
                        False,
                    ),
                    "mode": result.get(
                        "mode",
                        "headless",
                    ),
                    "attempts": result.get(
                        "attempts",
                        [],
                    ),
                }
            )

        except Exception as error:

            failed_attempt = {
                "status": "Failed",
                "product": None,
                "details": (
                    f"headless mode: scraper could not be started. {error}"
                ),
                "duration_ms": 0,
                "attempt_number": 1,
                "mode": "headless",
            }

            save_scrape_attempts(
                product,
                [failed_attempt],
            )

            results.append(
                {
                    "product_id": product.id,
                    "store_product_id": (
                        product.store_product_id
                    ),
                    "product": product.name,
                    "success": False,
                    "error": str(error),
                    "mode": "headless",
                    "attempts": [failed_attempt],
                }
            )

    successful = sum(
        1
        for result in results
        if result.get("success")
    )

    failed = (
        len(results)
        - successful
    )

    return {
        "total": len(results),
        "successful": successful,
        "failed": failed,
        "results": results,
    }


@api_view(["POST"])
def scrape_all_tracked(request):
    return Response(
        run_all_tracked_scrapes(),
        status=status.HTTP_200_OK,
    )
