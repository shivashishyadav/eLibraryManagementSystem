# 📚 E-Library Management System Backend

An enterprise-grade, modular RESTful backend API built with **Flask**, **SQLAlchemy**, **JWT Authentication**, and an integrated **GPT-4o-mini AI Summarization Proxy Engine**.

---

## 🏛️ System Architecture & Key Features

* **Role-Based Access Control (RBAC):** Gated permissions supporting `member`, `librarian`, and provisioned `admin` access levels. Public registration creates member accounts only.
* **Inventory & Review Management:** Full CRUD operations for library catalog, full-text search across titles/authors/descriptions, pagination, and user rating aggregations.
* **Smart Borrowing Engine:** Enforces user borrow limits, calculates due dates, tracks returns, and dynamically applies overdue fines ($1.50/day).
* **Automated Waitlist Management:** Automatic reservation queue processing that auto-fulfills loans to waiting members as soon as copies are returned.
* **Quota-Protected AI Summarizer:**
  * Direct integration with UserFacet API Proxy (`gpt-4o-mini`).
  * Supports 4 customized summary styles (`concise`, `detailed`, `academic`, `casual`).
  * **SHA-256 Hashing Cache Layer:** Caches generated summaries in SQLite to eliminate redundant AI calls and conserve your 100-request quota limit.


---

## 🗂️ Project Files Overview

```
backend/
├── app/
│   ├── routes/
│   │   └── ai_routes.py           ← AI endpoints implementation
│   ├── models.py                   ← Database models
│   ├── config.py                   ← configuration
│   ├── utils.py                    ← JWT token decorator
│   └── __init__.py                 ← Blueprint registration
│
├── .env                            ← API credentials
├── run.py                          ← Application entry point

```

---

## Installation & Setup

### 1. Prerequisites
* Python 3.9+
* `pip` and `venv`

### 2. Environment Setup
Navigate to the backend directory and set up a virtual environment:

```bash
cd backend
python -m venv venv

```

---

### Configuration (.env)
```
AI_API_TOKEN=YOUR_API_KEY
SECRET_KEY=elibrary-super-secret-key-2026
AI_BASE_URL=https://ai-api.userfacet.com
DATABASE_URL=sqlite:///elibrary.db

```

---

## Launch & Test

### Step 1: Start the Application
```bash
cd backend
python run.py
```

Expected output:
```
 * Running on http://0.0.0.0:5000
 * Debug mode: on
 * WARNING in app.run_simple
```

### Step 2: Health Check
```bash
curl http://localhost:5000/health
```

Expected response:
```json
{
  "status": "ok"
}
```

### Step 3: Run the Automated API Flow

From the `backend` directory, run:

```bash
py -3 tests/run_api_flow.py
```

The runner prints each API request and its result in the terminal. It uses a temporary in-memory database and mocks AI-provider requests, so it does not change local library data or consume AI quota.



### API Endpoints Reference

### Health Check

| **Method** | **Endpoint** | **Auth** | **Description** |
| ---------- | ------------ | -------- | --------------- |
| `GET` | `/health` | None | Returns `{"status": "ok"}` |


### Authentication

| **Method** | **Endpoint** | **Auth** | **Description** |
| ---------- | ------------ | -------- | --------------- |
| `POST` | `/api/v1/auth/register` | None | Register a new member |
| `POST` | `/api/v1/auth/login` | None | Login to get Bearer JWT token |
| `GET` | `/api/v1/auth/me` | JWT | Get active user profile |


### Book Inventory

| **Method** | **Endpoint** | **Auth** | **Description** |
| ---------- | ------------ | -------- | --------------- |
| `GET` | `/api/v1/books` | None | Search & paginate books (`?search=`, `?page=`) |
| `GET` | `/api/v1/books/<id>` | None | Get detailed book view + ratings |
| `POST` | `/api/v1/books` | Librarian/Admin | Add a new book to inventory |
| `PUT` | `/api/v1/books/<id>` | Librarian/Admin | Update one or more book fields; changing book content clears cached AI summaries |
| `DELETE` | `/api/v1/books/<id>` | Librarian/Admin | Delete a book with no loan/reservation history |
| `GET` | `/api/v1/books/<id>/reviews` | None | List book reviews |
| `POST` | `/api/v1/books/<id>/reviews` | JWT | Create or update the caller's rating (1-5) and review |


### Borrowing & Reservations

| **Method** | **Endpoint** | **Auth** | **Description** |
| ---------- | ------------ | -------- | --------------- |
| `POST` | `/api/v1/borrow/issue` | JWT | Borrow a book |
| `POST` | `/api/v1/borrow/return/<id>` | JWT | Return own book; librarian/admin may return any loan |
| `POST` | `/api/v1/borrow/reserve` | JWT | Join waitlist queue for out-of-stock book |
| `GET` | `/api/v1/borrow/my-borrows` | JWT | View the current user's loan history |
| `GET` | `/api/v1/borrow/reservations` | JWT | View the current user's reservations |
| `DELETE` | `/api/v1/borrow/reserve/<id>` | JWT | Cancel a waiting reservation |
| `GET` | `/api/v1/borrow/loans` | Librarian/Admin | View loans (`?status=active|overdue|returned|all`) |


### AI Summary Engine

| **Method** | **Endpoint** | **Auth** | **Description** |
| ---------- | ------------ | -------- | --------------- |
| `GET` | `/api/v1/ai/usage` | JWT | Check UserFacet API quota limits |
| `POST` | `/api/v1/ai/summarize/<id>` | JWT | Generate AI summary (Cached) |
