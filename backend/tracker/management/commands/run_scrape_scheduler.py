import json
import time
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from tracker.views import run_all_tracked_scrapes


class Command(BaseCommand):
    help = (
        "Run headless tracked-product scrape batches on a fixed interval. "
        "Default: every 120 minutes."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--interval-minutes",
            type=int,
            default=120,
            help="Minutes between completed scrape batches (default: 120).",
        )
        parser.add_argument(
            "--run-immediately",
            action="store_true",
            help="Run one batch when the scheduler starts, then continue.",
        )
        parser.add_argument(
            "--once",
            action="store_true",
            help="Run one batch and exit; useful for testing automation.",
        )

    def run_batch(self):
        started_at = timezone.localtime()

        self.stdout.write(
            self.style.NOTICE(
                "Starting scheduled scrape batch at "
                f"{started_at:%Y-%m-%d %H:%M:%S}."
            )
        )

        result = run_all_tracked_scrapes()

        self.stdout.write(
            json.dumps(
                {
                    "total": result["total"],
                    "successful": result["successful"],
                    "failed": result["failed"],
                },
                default=str,
            )
        )

        return result

    def handle(self, *args, **options):
        interval_minutes = options["interval_minutes"]

        if interval_minutes < 1:
            raise CommandError(
                "--interval-minutes must be at least 1."
            )

        if options["once"]:
            self.run_batch()
            return

        interval = timedelta(minutes=interval_minutes)

        self.stdout.write(
            self.style.SUCCESS(
                "Tracked-product scheduler is running every "
                f"{interval_minutes} minutes. Press Ctrl+C to stop."
            )
        )

        if options["run_immediately"]:
            self.run_batch()

        next_run = timezone.now() + interval

        try:
            while True:
                remaining_seconds = max(
                    (next_run - timezone.now()).total_seconds(),
                    0,
                )

                if remaining_seconds > 0:
                    time.sleep(min(remaining_seconds, 30))
                    continue

                self.run_batch()
                next_run = timezone.now() + interval

        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING("Tracked-product scheduler stopped.")
            )
