# ContactMailer

A lightweight Django application for managing contacts and sending email campaigns.

## Features Used
- **Django**: For models, views, and routing.
- **CSV Reader/Writer**: Import and export contacts via CSV.
- **Decorators**: Custom `@log_time` and `@safe` decorators for logging and error handling.
- **Threading/Concurrency**: Concurrent email sending via `ThreadPoolExecutor`.
- **Logging**: Dedicated logger `contactmailer` writing to rotated log files.
- **Dictionary**: Used for mapping CSV columns dynamically.
- **Sockets**: A TCP server for tracking campaign sending progress.
- **Map**: Used to efficiently clean and parse rows from CSV mapping.
- **Subprocess**: Pre-flight checks on the SMTP host before bulk emails are sent.
- **Send Email**: Utilizes `smtplib` directly.

## Setup

### Using Docker Compose (Recommended)
You can easily spin up the entire stack (Django, Progress Server, Mailpit for testing emails) using Docker Compose:

1. **Build and start the containers:**
   ```bash
   docker compose up --build -d
   ```
2. **Access the application:**
   - Django App: `http://localhost:8000/contacts/`
   - Mailpit Web UI: `http://localhost:8025/`
3. **Seed initial data (Superuser & Samples):**
   ```bash
   docker compose exec django python manage.py seed_data
   ```
4. **View live socket progress:**
   ```bash
   docker compose exec progress_server python -m common.progress_socket client
   ```

### Manual Local Setup

1. **Install requirements:**
    ```bash
    uv venv
    source .venv/bin/activate
    uv add django python-dotenv
    ```

2. **Configure `.env`**:
    Edit the `.env` file to include your SMTP settings:
    ```env
    EMAIL_HOST=localhost
    EMAIL_PORT=1025
    EMAIL_HOST_USER=
    EMAIL_HOST_PASSWORD=
    EMAIL_USE_TLS=False
    DEFAULT_FROM_EMAIL=test@contactmailer.local
    ```

3. **Migrate the database:**
    ```bash
    python manage.py makemigrations contacts campaigns
    python manage.py migrate
    ```

4. **Start the Progress Socket Server**:
    In a separate terminal, run:
    ```bash
    python -m common.progress_socket
    ```

5. **Start the Django Development Server**:
    ```bash
    python manage.py runserver
    ```

### Testing & Development Tools

To make testing easier, several tools are provided:

1. **Seed Data**: Populate the database with a superuser (`admin`/`admin`), sample contacts, and campaigns.
   ```bash
   python manage.py seed_data
   ```
2. **Sample CSVs**: Located in the `samples/` directory:
   - `contacts_minimal.csv`: Name and Email only.
   - `contacts_full.csv`: All fields with custom headers (tests mapping).
   - `contacts_bulk.csv`: 100 contacts for testing pagination and socket progress.

## Usage
1. Go to `http://127.0.0.1:8000/contacts/`
2. **Import CSV**: Use files from the `samples/` directory (e.g., `contacts_full.csv`).
3. **Map Columns**: If using `contacts_full.csv`, map the columns: 
   - `Full Name` -> Name
   - `Email Address` -> Email
   - `Company Name` -> Company
4. **Progress client**: To view streaming progress during a large send (like `contacts_bulk.csv`), run:
   ```bash
   python -m common.progress_socket client
   ```
5. **Trigger Campaign**: Create a campaign, choose a target tag (or leave blank), and click **Send**.
