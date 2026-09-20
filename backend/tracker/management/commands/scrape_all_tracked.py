import json

from django.core.management.base import BaseCommand

from tracker.views import run_all_tracked_scrapes


class Command(BaseCommand):
    help = (
        "Run one headless scrape batch for every currently tracked product."
    )

    def handle(self, *args, **options):
        result = run_all_tracked_scrapes()

        self.stdout.write(
            json.dumps(
                result,
                indent=2,
                default=str,
            )
        )

