# Equipment Reservation System

A full-stack web application for reserving shared equipment.

Users can browse equipment, check availability, create and cancel reservations, and manage their account. Administrators can manage users, equipment, categories, and reservations.

## Live Site

- Frontend: https://equipment-reservation-system.vercel.app
- API documentation: https://equipment-reservation-system-vcdc.onrender.com/docs

## Features

- User registration and login
- JWT authentication
- User and admin roles
- Equipment browsing and filtering
- Equipment availability checks by date
- Reservation creation and cancellation
- Prevention of overlapping reservations
- Reservation history
- Admin management of users
- Admin management of equipment and categories
- Admin access to all reservations
- Responsive layout for desktop and mobile

## Tech Stack

### Backend

- Python
- FastAPI
- PostgreSQL
- psycopg
- Alembic
- Pydantic
- pytest

### Frontend

- React
- TypeScript
- Vite
- CSS

### Deployment

- Docker
- Render
- Neon
- Vercel

## Deployment Architecture

```text
Browser
   |
   v
React frontend (Vercel)
   |
   | HTTPS
   v
FastAPI backend (Render)
   |
   | SQL
   v
PostgreSQL database (Neon)
```

The frontend communicates with the FastAPI backend over HTTP. The backend handles authentication, authorization, validation, reservation rules, and database access.

## Local Setup

### Backend

Go to the backend directory:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file using `.env.example` as a reference.

The local backend expects PostgreSQL to be running and uses:

```text
DB_NAME
DB_USER
DB_PASSWORD
DB_HOST
DB_PORT
JWT_SECRET
```

Run the database migrations:

```bash
alembic upgrade head
```

Start the backend:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

### Frontend

From the project root:

```bash
cd frontend
npm install
npm run dev
```

The frontend uses `http://127.0.0.1:8000` as its default API URL during local development.

A different backend URL can be supplied with:

```text
VITE_API_URL
```

## Testing

Run the backend test suite:

```bash
cd backend
python -m pytest
```

Run the frontend checks:

```bash
cd frontend
npm run lint
npm run build
```

## Docker

The backend can also be run with Docker.

From the `backend` directory:

```bash
docker compose up --build
```

The local Docker setup runs the FastAPI application in a container and connects to PostgreSQL running on the host machine.

## Security

- Passwords are hashed before being stored.
- Protected endpoints require JWT authentication.
- User and admin permissions are enforced by the backend.
- SQL values are passed using parameterized queries.
- Application secrets and database credentials are supplied through environment variables.

## CI

GitHub Actions runs automated backend and frontend checks on pushes and pull requests.