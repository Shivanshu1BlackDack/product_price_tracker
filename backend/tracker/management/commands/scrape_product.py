import json

from django.core.management.base import BaseCommand, CommandError

from scraper.scraper import scrape_product_by_id
from tracker.models import Product
from tracker.views import (
    save_scrape_attempts,
    update_product_from_scrape,
)


class Command(BaseCommand):
    help = (
        "Scrape one INE product in headed or headless mode. "
        "Use --headed for the assignment screen recording."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--id",
            type=int,
            required=True,
            help="INE storefront product ID.",
        )
        parser.add_argument(
            "--headed",
            action="store_true",
            help="Open a visible Chromium browser.",
        )
        parser.add_argument(
            "--headless",
            action="store_true",
            help="Run Chromium in headless mode.",
        )
        parser.add_argument(
            "--max-attempts",
            type=int,
            default=3,
            help="Maximum scrape attempts before failing.",
        )
        parser.add_argument(
            "--save",
            action="store_true",
            help=(
                "Save successful scrape data and attempt logs "
                "to the database if the product exists locally."
            ),
        )

    def handle(self, *args, **options):
        if options["headed"] and options["headless"]:
            raise CommandError(
                "Choose either --headed or --headless, not both."
            )

        headless = not options["headed"]
        store_product_id = options["id"]

        result = scrape_product_by_id(
            product_id=store_product_id,
            headless=headless,
            max_attempts=options["max_attempts"],
        )

        if options["save"]:
            product = Product.objects.filter(
                store_product_id=store_product_id,
            ).first()

            if product is None:
                self.stderr.write(
                    "No local Product matched this INE ID; "
                    "scrape result was not saved."
                )
            else:
                save_scrape_attempts(
                    product,
                    result.get("attempts", []),
                )

                if result.get("success"):
                    update_product_from_scrape(
                        product,
                        result.get("product"),
                    )

        self.stdout.write(
            json.dumps(
                result,
                indent=2,
                default=str,
            )
        )

        if not result.get("success"):
            raise CommandError("Scrape failed.")
