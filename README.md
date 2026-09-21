# Product Price Tracker

Full-stack assignment project for tracking product prices from the INE mock storefront at `https://demo.inelabteamdev.com/`.

The app uses a Django REST backend, React + Vite frontend, Supabase PostgreSQL for deployment data, Playwright scraping, and an external cron trigger for scheduled scrapes.

## Features

- Search products from the INE mock catalog by partial or full name.
- Track selected products.
- Scrape current price and stock with Playwright.
- Handle cookie banners and the reveal-price hover/mouse-move interaction.
- Retry slow or failed scrapes.
- Store price history, stock history, and every scrape attempt.
- Show dashboard, tracked inventory, product detail charts/tables, and scrape logs.
- Run scraper in headless mode for cron/API and headed mode for demo recording.

## Project Structure

```text
backend/    Django REST API, scraper, migrations, Render config
frontend/   React + Vite dashboard, Vercel config through VITE_API_URL
```

## Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium
copy .env.example .env
python manage.py migrate
python manage.py runserver
```



## Frontend Setup

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

Open `http://localhost:5173`.

## Environment Variables

Backend:

```text
DJANGO_SECRET_KEY
DEBUG
ALLOWED_HOSTS
CORS_ALLOWED_ORIGINS
DATABASE_URL
```

Frontend:

```text
VITE_API_URL
```



## API Endpoints

```text
GET    /api/catalog/
POST   /api/catalog/sync/
GET    /api/products/search/?q=macbook
POST   /api/products/track/
GET    /api/products/tracked/
GET    /api/products/<id>/
DELETE /api/products/<id>/
POST   /api/products/<id>/scrape/
POST   /api/products/scrape-all/
GET    /api/products/<id>/history/
GET    /api/products/<id>/stock-history/
GET    /api/products/<id>/logs/
GET    /api/scrape-logs/
```

## Scheduled Scraping

All scheduled runs use headless Playwright and scrape every product whose
`is_tracked` value is true. A successful run adds price and stock history;
a failed run adds an audit entry without storing fake price data.

### Local Development

Keep this command open in a third terminal while developing locally:

```cmd
venv\Scripts\python.exe manage.py run_scrape_scheduler --interval-minutes 120 --run-immediately
```

`--run-immediately` performs a batch when the scheduler starts, then repeats

### Render / Production


Schedule: every 2 hours.


## Headed vs Headless Scraper Demo

Headless mode is used by the API and scheduled cron:

```bash
python manage.py scrape_product --id 1 --headless
```

Headed mode opens Chromium visibly

```bash
python manage.py scrape_product --id 1 --headed
```

To save the headed/headless run into the local database when the product exists:

```bash
python manage.py scrape_product --id 1 --headed --save
```

## Deployment

Render backend:

```bash
pip install -r requirements.txt
python -m playwright install chromium
python manage.py collectstatic --no-input
python manage.py migrate
gunicorn config.wsgi:application
```

Vercel frontend:

```text
Root directory: frontend
Build command: npm run build
Output directory: dist
Environment: VITE_API_URL=https://your-render-service.onrender.com/api
```

Supabase:

- Create a PostgreSQL project.
- Copy the pooled connection string into `DATABASE_URL`, or set the `DB_*` values.
- Run Render deploy/migrations.
