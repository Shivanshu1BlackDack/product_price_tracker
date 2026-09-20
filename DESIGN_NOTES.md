# Design Notes

## Scraper Choice

I used Playwright instead of plain HTTP parsing because the INE mock store intentionally loads some values asynchronously and requires browser-like interaction to reveal the price. Lightweight parsing would be simpler, but it would be less reliable for the reveal-price behavior and delayed page state.

## Reliability Strategy

- Each product is scraped by direct INE product ID after catalog discovery, avoiding repeated homepage search during scheduled runs.
- The scraper waits for the product page and price block before extraction.
- Cookie banners are detected and accepted before interaction, and click recovery handles late overlays.
- The reveal-price area receives continuous mouse movement before price extraction, which matches the mock store's interaction requirement.
- Every scrape has up to three attempts.
- Failed intermediate attempts are recorded as `Retried`; the final failed attempt is recorded as `Failed`.
- The app validates price and stock before saving history. Missing, zero, or invalid data is treated as failure and is not stored as fake history.

## Price Handling

The scraper treats the revealed current price as the value used for price history. When available, crossed/original price, deal price, and discount are stored separately so discounted products do not overwrite the current tracked price with the wrong number.

## Scheduling

The backend does not run an always-on loop. Free-tier Render services can sleep, so scheduled scraping is triggered by an external cron service calling:

```text
POST /api/products/scrape-all/
```

The intended schedule is once every 2 hours.

## Headed And Headless Modes

Headless mode is used for normal API and cron scraping. Headed mode is exposed through the Django management command for the assignment recording:

```bash
python manage.py scrape_product --id 1 --headed
python manage.py scrape_product --id 1 --headless
```

Both modes use the same scraper path, retries, cookie handling, reveal-price movement, validation, and logging.

## AI Tool Corrections

The first generated version over-focused on dashboard UI and had two practical issues: one frontend page still used mock data, and the local backend assumed PostgreSQL variables were always present. I corrected those by replacing mock data with API-backed hooks and adding a SQLite fallback for local development while keeping Supabase PostgreSQL for deployment.

