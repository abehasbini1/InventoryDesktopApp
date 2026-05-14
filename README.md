# Superior Inventory Manager Enterprise Edition

A robust, full-stack inventory request and management system. Designed with a **Client-Server architecture**, it ensures that database credentials remain secured on the server while providing a modern, high-performance GUI for end-users.

##  System Architecture

The application is built on a three-tier architecture to maximize security and performance:

1. **Database (MySQL):** The central source of truth for parts, users, and transaction logs.
2. **Backend (FastAPI):** Hosted on the server (`.252`). It handles `BCrypt` password hashing, registration, and role-based validation.
3. **Frontend (CustomTkinter):** A desktop client installed on workstations that communicates with the API to perform inventory operations.

## Features

* **Secure Registration & Login:** Password protection using industry-standard `bcrypt` via the `passlib` library.
* **Role-Based Access Control (RBAC):**
* **Admins:** Manage users and view full transaction logs.
* **Cage Operators:** Update stock levels and approve/deny requests.
* **Standard Users:** Submit requests for parts via a virtual "Request Cart."


* **Microsoft Teams Integration:** Instant notifications for new part requests and stock updates via Webhooks.
* **Audit Logging:** Every stock change is automatically recorded in the `transaction_history` table.
* **Local Performance:** Optimized for low-latency interactions over a local area network (LAN).

##  Tech Stack

* **GUI Framework:** CustomTkinter (Modern Python UI)
* **API Framework:** FastAPI (Asynchronous Python Backend)
* **Database:** MySQL (Relational Data)
* **Security:** Passlib (Bcrypt hashing), Pydantic (Data validation)
* **Packaging:** PyInstaller (Executable bundling)

##  Deployment & Setup

### 1. Server Configuration

On the server machine (e.g., `192.168.200.252`):

* Configure the `.env` file with `DB_HOST`, `DB_USER`, `DB_PASSWORD`, and `TEAMS_WEBHOOK_URL`.
* Run the API server:
```bash
uvicorn main_api:app --host 0.0.0.0 --port 8000

```



### 2. Desktop Client Bundling

To distribute the application to workstations, package the script into a standalone `.exe`:

```bash
python -m PyInstaller --noconfirm --onedir --windowed --add-data "registration.py;." --add-data ".env;." --collect-all customtkinter main_app.py

```

### 3. Connection Testing

Use the included utility to verify the client can reach the database before full deployment:

```bash
python test_connection.py

```
