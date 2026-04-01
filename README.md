# Django Order Management

A Django-based order management application for handling order requests, approvals, and follow-up within a school or team context.

This project is designed to be practical and lightweight:

- Django backend
- SQLite database
- Docker and Docker Compose support
- Gunicorn for running Django in a production-style container
- Static files collected on container startup

---

## Features

- Custom user model
- Role-based workflow
- Order creation and follow-up
- Django admin for management
- Docker-based deployment with persistent SQLite storage

---

## Project structure

```text
django-order-management/
├── accounts/
├── orders/
├── order_management/
├── static/
├── templates/
├── Dockerfile
├── docker-compose.example
├── entrypoint.sh
├── manage.py
└── requirements.txt
```

---

## Requirements

For local development without Docker:

- Python 3.12+
- pip
- virtual environment support

For containerized usage:

- Docker
- Docker Compose

---

## Local development setup

### 1. Clone the repository

```bash
git clone https://github.com/MathieuLeroy2/django-order-management.git
cd django-order-management
```

### 2. Create and activate a virtual environment

#### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

#### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run migrations

```bash
python manage.py migrate
```

### 5. Create an admin user

```bash
python manage.py createsuperuser
```

### 6. Start the development server

```bash
python manage.py runserver
```

The application should then be available at:

```text
http://127.0.0.1:8000/
```

---

## Docker setup

The project includes Docker support for a simple production-style deployment:

- Django runs with Gunicorn
- database migrations are applied automatically on startup
- static files are collected automatically on startup
- SQLite is stored in a persistent Docker volume

### 1. Create a `docker-compose.yml`

Start from the included example file:

```bash
cp docker-compose.example docker-compose.yml
```

If you are on Windows PowerShell and `cp` does not work:

```powershell
copy docker-compose.example docker-compose.yml
```

### 2. Review the environment variables

The compose file uses environment variables directly inside `docker-compose.yml`.

Example values:

```yaml
services:
  web:
    build: .
    container_name: django-order-management
    ports:
      - "80:8000"
    environment:
      DJANGO_DEBUG: "False"
      DJANGO_SECRET_KEY: "replace-this-with-a-long-random-secret"
      DJANGO_ALLOWED_HOSTS: "localhost,127.0.0.1"
      DJANGO_CSRF_TRUSTED_ORIGINS: "http://localhost:8000"
      DJANGO_SQLITE_PATH: "/data/db.sqlite3"
    volumes:
      - django_order_data:/data
    restart: unless-stopped

volumes:
  django_order_data:
```

Adjust these values if needed for your server or domain.

### 3. Build and start the containers

```bash
docker compose up --build -d
```

### 4. View logs

```bash
docker compose logs -f
```

You should see startup steps such as:

- migrations being applied
- static files being collected
- Gunicorn starting on port `8000`

### 5. Create the first admin user

After the container is running, create the first admin user with:

```bash
docker compose exec web python manage.py createsuperuser
```

This is the command you should use to add the initial administrator account inside the running container.

### 6. Open the application

If you use the default port mapping from the example compose file, open:

```text
http://localhost/
```

If you changed the port mapping, use the matching host/port combination.

---

## Common Docker commands

### Stop the application

```bash
docker compose down
```

### Stop and remove containers but keep the SQLite data volume

```bash
docker compose down
```

### Stop and remove containers **and** delete the database volume

```bash
docker compose down -v
```

Use `-v` only if you intentionally want to reset the database.

### Rebuild after code changes

```bash
docker compose up --build -d
```

### Run Django management commands in the container

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py collectstatic --noinput
docker compose exec web python manage.py createsuperuser
```

---

## Static files

Static files are collected automatically when the container starts through the project entrypoint script.

If needed manually:

```bash
python manage.py collectstatic --noinput
```

Or inside Docker:

```bash
docker compose exec web python manage.py collectstatic --noinput
```

---

## Database

This project currently uses SQLite.

In Docker, the database file is intended to live at:

```text
/data/db.sqlite3
```

That path is mounted to a named Docker volume so the data persists across container restarts.

---

## Admin panel

Once a superuser exists, the Django admin is available at:

```text
/admin/
```

Example:

```text
http://127.0.0.1:8000/admin/
```

or with Docker:

```text
http://localhost/admin/
```

---

## Notes

- This project currently keeps configuration via environment variables.
- The Docker setup is intentionally simple and practical.
- SQLite is used for now to keep deployment lightweight.
- Gunicorn is used instead of Django’s development server in the container.

---

## License

Add a license here if you want to make the project usage terms explicit.
