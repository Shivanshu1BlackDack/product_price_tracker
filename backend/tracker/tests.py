from decimal import Decimal
from unittest.mock import patch

from django.core.management import call_command
from rest_framework import status
from rest_framework.test import APITestCase

from .models import (
    PriceHistory,
    Product,
    ScrapeAttempt,
    StockHistory,
)


class ProductSpecificScrapeTests(APITestCase):
    def setUp(self):
        self.selected_product = Product.objects.create(
            name="Selected product",
            brand="INE",
            category="Demo",
            sku="INE-SELECTED-407",
            url="https://demo.inelabteamdev.com/product/407",
            store_product_id=407,
            is_tracked=True,
        )

        self.other_product = Product.objects.create(
            name="Other product",
            brand="INE",
            category="Demo",
            sku="INE-OTHER-408",
            url="https://demo.inelabteamdev.com/product/408",
            store_product_id=408,
            is_tracked=True,
        )

    @patch("tracker.views.run_direct_scrape")
    def test_price_check_scrapes_only_the_requested_product(
        self,
        run_direct_scrape,
    ):
        run_direct_scrape.return_value = {
            "success": True,
            "mode": "headless",
            "product": {
                "price": Decimal("15745.00"),
                "original_price": Decimal("19990.00"),
                "deal_price": Decimal("17838.00"),
                "discount": Decimal("15.00"),
                "stock": "ONLY 165 LEFT",
            },
            "attempts": [
                {
                    "status": "Success",
                    "details": "Product scraped successfully.",
                    "duration_ms": 875,
                    "attempt_number": 1,
                    "mode": "headless",
                }
            ],
        }

        response = self.client.post(
            f"/api/products/{self.selected_product.id}/scrape/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])

        run_direct_scrape.assert_called_once()
        scraped_product = run_direct_scrape.call_args.args[0]
        self.assertEqual(scraped_product.id, self.selected_product.id)
        self.assertEqual(scraped_product.store_product_id, 407)

        self.selected_product.refresh_from_db()
        self.other_product.refresh_from_db()

        self.assertEqual(
            self.selected_product.current_price,
            Decimal("15745.00"),
        )
        self.assertEqual(
            self.selected_product.stock,
            "ONLY 165 LEFT",
        )
        self.assertIsNotNone(self.selected_product.last_scraped_at)
        self.assertIsNone(self.other_product.current_price)
        self.assertFalse(
            PriceHistory.objects.filter(
                product=self.other_product,
            ).exists()
        )

        self.assertTrue(
            PriceHistory.objects.filter(
                product=self.selected_product,
                price=Decimal("15745.00"),
            ).exists()
        )
        self.assertTrue(
            StockHistory.objects.filter(
                product=self.selected_product,
                stock="ONLY 165 LEFT",
            ).exists()
        )
        self.assertTrue(
            ScrapeAttempt.objects.filter(
                product=self.selected_product,
                status="Success",
            ).exists()
        )


class ScheduledScrapeCommandTests(APITestCase):
    @patch(
        "tracker.management.commands.run_scrape_scheduler."
        "run_all_tracked_scrapes"
    )
    def test_scheduler_once_runs_one_batch(
        self,
        run_all_tracked_scrapes,
    ):
        run_all_tracked_scrapes.return_value = {
            "total": 0,
            "successful": 0,
            "failed": 0,
            "results": [],
        }

        call_command("run_scrape_scheduler", "--once")

        run_all_tracked_scrapes.assert_called_once()
