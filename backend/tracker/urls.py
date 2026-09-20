from django.urls import path

from . import views


urlpatterns = [

    # ========================================================
    # CATALOG
    # ========================================================

    path(
        "catalog/",
        views.catalog_products,
    ),

    path(
        "catalog/sync/",
        views.sync_catalog,
    ),

    # ========================================================
    # SEARCH
    # ========================================================

    path(
        "products/search/",
        views.search_products,
    ),

    # ========================================================
    # TRACKING
    # ========================================================

    path(
        "products/track/",
        views.track_product,
    ),

    path(
        "products/tracked/",
        views.tracked_products,
    ),

    # ========================================================
    # GLOBAL LOGS
    # ========================================================

    path(
        "scrape-logs/",
        views.all_scrape_logs,
    ),

    # ========================================================
    # PRODUCT
    # ========================================================

    path(
        "products/<int:product_id>/",
        views.product_detail,
    ),

    # ========================================================
    # HISTORY
    # ========================================================

    path(
        "products/<int:product_id>/history/",
        views.price_history,
    ),

    path(
        "products/<int:product_id>/stock-history/",
        views.stock_history,
    ),

    # ========================================================
    # LOGS
    # ========================================================

    path(
        "products/<int:product_id>/logs/",
        views.scrape_logs,
    ),

    # ========================================================
    # SCRAPE
    # ========================================================

    path(
        "products/<int:product_id>/scrape/",
        views.scrape_product,
    ),

    path(
        "products/scrape-all/",
        views.scrape_all_tracked,
    ),
]