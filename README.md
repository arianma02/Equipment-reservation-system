# Equipment Reservation System

A full-stack application for reserving shared equipment. Users can check availability, book equipment, and cancel reservations. Admins manage equipment, categories, users, and bookings.

[Live app](https://equipment-reservation-system.vercel.app) · [API documentation](https://equipment-reservation-system-vcdc.onrender.com/docs)

## Features

- JWT authentication with backend-enforced user and admin permissions
- Equipment browsing, filtering, and availability checks
- Booking and cancellation with reservation history
- PostgreSQL transactions and row locking to prevent overlapping bookings
- Admin controls for equipment, categories, users, and reservations

## Stack

- **Backend:** Python, FastAPI, PostgreSQL, psycopg, Alembic
- **Frontend:** React, TypeScript, Vite
- **Tests:** pytest, Playwright
- **Hosting:** Vercel frontend → Render API → Neon PostgreSQL

## Screenshots

![Admin dashboard](screenshots/admin.png)
![Equipment management](screenshots/manage-equipment.png)
![Reservation management](screenshots/manage-reservations.png)

Admin credentials are not shared for the public demo.

## Local setup

Requires Python 3.14, Node.js 24, and PostgreSQL. Create a local application database before running migrations.

### Backend

From the project root, in PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create `backend/.env` with `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, and `JWT_SECRET`. Alternatively, use `DATABASE_URL` for the database connection; it takes priority over the `DB_*` settings.

```powershell
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

The API runs at `http://127.0.0.1:8000`.

### Frontend

In another terminal, from the project root:

```bash
cd frontend
npm ci
npm run dev
```

The frontend defaults to the local API. Set `VITE_API_URL` to use a different backend.

### Docker

Run `docker compose up --build` from `backend`. This runs the API in a container and connects to PostgreSQL on the host machine.

## Testing

### Backend

Create a separate, disposable PostgreSQL database named `equipment_reservation_test`. In a separate PowerShell terminal, activate the backend virtual environment and run:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
$env:PYTHON_DOTENV_DISABLED = "1"
$env:TEST_DATABASE_URL = "postgresql://TEST_USER:TEST_PASSWORD@localhost:5432/equipment_reservation_test"
$env:DATABASE_URL = $env:TEST_DATABASE_URL
python -m alembic upgrade head
python -m pytest
```

Replace the connection placeholders with your test database details. Tests clear the database between cases and refuse to clear a database with another name. Run them serially. This terminal is configured for the test database; use another terminal for the normal application.

Backend tests cover API behavior, permissions, date validation, concurrent booking, last-active-admin protection, and transaction rollback. They use real PostgreSQL to test database behavior.

### Frontend

From `frontend`:

```bash
npm run lint
npm run build
npx playwright install chromium
npm run test:browser
```

Browser tests cover login, booking, cancellation, conflicts, session expiry, permission errors, and outdated availability responses. They use mocked API responses; they do not test the full deployed system. Browser-test mode ignores local dotenv files.

GitHub Actions runs backend tests, browser tests, frontend lint, and the frontend build on pushes and pull requests.

## Implementation notes

- Booking creation locks the user and equipment rows before checking dates and inserting within one transaction.
- Admin updates and account deactivation share a PostgreSQL transaction advisory lock to coordinate changes affecting the last active admin.
- Passwords are hashed, SQL values are parameterized, and credentials are supplied through environment variables.
