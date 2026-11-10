# Egg-Laying Poultry Farm Monitoring System

A Django web application designed for egg-laying poultry farms to track daily egg collections (crates + loose eggs), daily broken eggs, sales dispatches, and egg room inventory.

## Features

- **Flock & Shed Management**: Track bird batches, breeds, housing dates, and active live bird populations.
- **Daily Egg Logging**:
  - Full crates collected (30 eggs/crate)
  - Loose eggs collected (< 30)
  - **Broken eggs** recorded daily
  - Live auto-calculation of total eggs produced, **Breakage Rate (%)**, and **Hen-Day Production (HDP %)**
  - Mortality & culling (which automatically updates the live flock count)
  - Feed consumption (kg)
- **Egg Sales & Customer Dispatches**:
  - Record daily crates sold, rate per crate, and loose egg sales
  - Customer details and payment status (`PAID`, `PARTIAL`, `UNPAID / CREDIT`)
  - Tracks customer credit due and overall sales revenue
- **Egg Room Stock Reconciliation**:
  - Live crates-in-stock calculation: $\text{Stock} = \sum(\text{Crates Collected}) - \sum(\text{Crates Sold})$
  - Cumulative breakage & loss audit
- **Visual Analytics Dashboard**:
  - 7-day trend chart comparing crates produced vs. crates sold and breakages
  - Daily KPI summary cards
- **Production & Cloud Ready**:
  - Dockerized with multi-stage Gunicorn + WhiteNoise static compression
  - Dokploy / Coolify / PaaS compatible with automated migrations and `/health/` endpoint
  - Supports SQLite persistent storage or managed PostgreSQL

---

## Quickstart (Local Development)

### 1. Activate Environment
In PowerShell:
```powershell
.\venv\Scripts\Activate.ps1
```

### 2. Run Database Migrations
```powershell
python manage.py migrate
```

### 3. Create Superuser (Admin)
```powershell
python manage.py createsuperuser
```

### 4. Run Development Server
```powershell
python manage.py runserver
```

Open your browser at [http://127.0.0.1:8000/](http://127.0.0.1:8000/).  
Django Admin is accessible at [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/).

---

## Production Deployment on Dokploy

### Option A: Dokploy Application (Dockerfile Deployment)

1. **Push your code to GitHub / GitLab / Gitea.**
2. In your **Dokploy Dashboard**, click **Create Application**:
   - **Source**: Connect your Git repository.
   - **Build Type**: `Dockerfile`
   - **Port**: `8000`
3. **Configure Volumes (Crucial if using SQLite)**:
   - Navigate to the **Volumes** tab in Dokploy.
   - Add a volume mount:
     - **Host / Volume Name**: `poultry-farm-data`
     - **Mount Path**: `/app/data`
   - This ensures your database (`/app/data/db.sqlite3`) persists across container restarts and redeployments.
4. **Configure Environment Variables** in the Dokploy **Environment** tab:
   ```env
   SECRET_KEY=your-secure-random-secret-key-at-least-50-chars
   DEBUG=False
   ALLOWED_HOSTS=farm.yourdomain.com
   CSRF_TRUSTED_ORIGINS=https://farm.yourdomain.com
   DATA_DIR=/app/data
   PORT=8000
   ```
   *(If using Dokploy PostgreSQL instead of SQLite, set `DATABASE_URL=postgresql://user:pass@host:5432/dbname`)*.
5. **Health Check** (Optional, under Advanced / Monitoring):
   - Path: `/health/`
   - Expected status: `200`
6. Click **Deploy**. Dokploy will build the image, collect static files, run database migrations, and boot Gunicorn behind Traefik SSL.

---

### Option B: Docker Compose Deployment

You can also run the entire stack (including a PostgreSQL database) using Docker Compose:

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Build and start containers:
   ```bash
   docker compose up -d --build
   ```
3. Create a superuser in the running container:
   ```bash
   docker compose exec web python manage.py createsuperuser
   ```
4. Access the web app at `http://localhost:8000`.
