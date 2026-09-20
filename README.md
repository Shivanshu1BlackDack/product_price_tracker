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

If Windows says `python` is not recognized, use your installed Python path:

```powershell
cd "D:\product_price tracker\backend"
& "C:\Users\HP\AppData\Local\Programs\Python\Python313\python.exe" -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m playwright install chromium
copy .env.example .env
python manage.py migrate
python manage.py runserver
```

If PowerShell blocks activation or the venv launcher is easier, run through the venv Python directly:

```powershell
cd "D:\product_price tracker\backend"
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m playwright install chromium
copy .env.example .env
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py runserver
```

If no database variables are set, Django uses local SQLite. For deployment, set Supabase PostgreSQL variables.

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

Use `DATABASE_URL` for Supabase. Keep `DEBUG=False` on Render.
If your database password contains special URL characters such as `@`, encode them in `DATABASE_URL`; for example, write `@` as `%40`.

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
cd /d "D:\product_price tracker\backend"
venv\Scripts\python.exe manage.py run_scrape_scheduler --interval-minutes 120 --run-immediately
```

`--run-immediately` performs a batch when the scheduler starts, then repeats
every two hours. Stop it with `Ctrl+C`.

To verify one automatic batch without leaving the scheduler running:

```cmd
venv\Scripts\python.exe manage.py run_scrape_scheduler --once
```

To run the same batch manually from a terminal:

```cmd
venv\Scripts\python.exe manage.py scrape_all_tracked
```

### Render / Production

For deployment, use cron-job.org or another external scheduler instead of a
long-running Django process. Configure it to send:

```text
POST https://your-render-service.onrender.com/api/products/scrape-all/
```

Schedule: every 2 hours.

Use only one scheduler for a deployed backend: either the external cron job or
the local `run_scrape_scheduler` command, never both. The endpoint scrapes all
tracked products in headless mode, records retries/failures, and only stores
price/stock history when validation succeeds.

## Headed vs Headless Scraper Demo

Headless mode is used by the API and scheduled cron:

```bash
python manage.py scrape_product --id 1 --headless
```

Headed mode opens Chromium visibly for the assignment screen recording:

```bash
python manage.py scrape_product --id 1 --headed
```

To save the headed/headless run into the local database when the product exists:

```bash
python manage.py scrape_product --id 1 --headed --save
```

Direct scraper CLI is also available:

```bash
python scraper/scraper.py --id 1 --headed
python scraper/scraper.py --id 1
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

## Submission Checklist

- Live Vercel URL.
- Live Render backend URL.
- Public GitHub repository.
- Supabase database configured.
- cron-job.org calls `/api/products/scrape-all/` every 2 hours.
- 2-4 minute headed scraper recording.
- `DESIGN_NOTES.md`.
- PDF resume.
