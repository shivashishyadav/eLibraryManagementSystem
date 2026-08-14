# E-Library Management System Backend

An enterprise-grade, modular RESTful backend API built with **Flask**, **SQLAlchemy**, **JWT Authentication**, and an integrated **GPT-4o-mini AI Summarization Proxy Engine**.

---

## System Architecture & Key Features

* **Role-Based Access Control (RBAC):** Gated permissions supporting `member`, `librarian`, and provisioned `admin` access levels. Public registration creates member accounts only.
* **Inventory & Review Management:** Full CRUD operations for library catalog, full-text search across titles/authors/descriptions, pagination, and user rating aggregations.
* **Smart Borrowing Engine:** Enforces user borrow limits, calculates due dates, tracks returns, and dynamically applies overdue fines ($1.50/day).
* **Automated Waitlist Management:** Automatic reservation queue processing that auto-fulfills loans to waiting members as soon as copies are returned.
* **Quota-Protected AI Summarizer:**
  * Direct integration with UserFacet API Proxy (`gpt-4o-mini`).
  * Supports 4 customized summary styles (`concise`, `detailed`, `academic`, `casual`).
  * **SHA-256 Hashing Cache Layer:** Caches generated summaries in SQLite to eliminate redundant AI calls and conserve your 100-request quota limit.

```text
                    E-LIBRARY SYSTEM
                           |
          +----------------+----------------+
          |                |                |
       Users             Books           AI Engine
          |                |                |
       JWT Auth       CRUD/Search       UserFacet API
          |                |                |
       Roles          Borrowing         GPT-4o-mini
          |                |                |
   Member/Librarian     Reviews        Summary Cache
          |             Reservations        |
          |                |                |
          +----------------+----------------+
                           |
                      SQLAlchemy
                           |
                         SQLite
```


---

## Project Files Overview

```
backend/
├── app/
│   ├── routes/
│   │   └── ai_routes.py           ← AI endpoints implementation
│   ├── models.py                   ← Database models
│   ├── config.py                   ← configuration
│   ├── utils.py                    ← JWT token decorator
│   └── __init__.py                 ← Blueprint registration
├── tests/
│   ├──
│      └── run_api_flow.py 
│      └── test_library_api.py
├── .env                            ← API credentials
├── run.py                          ← Application entry point

```

---


## According to problem Statements: 

### 1. [Identify edge cases, constraints, and real-world considerations](https://github.com/shivashishyadav/eLibraryManagementSystem/blob/main/backend/documentation.md#t-important-edge-cases)

---

### 2. Core Features

Beyond the basic requirements of book management and AI summarization, the system includes:

1. Role-based access control.
2. Inventory copy tracking.
3. Borrowing limits.
4. Automatic due dates.
5. Overdue fines.
6. Reservation queues.
7. Automatic reservation fulfillment.
8. Reservation cancellation.
9. Loan history.
10. Librarian/admin loan monitoring.
11. Book reviews and rating aggregation.
12. Public review access.
13. Pagination and multi-field searching.
14. Inventory consistency validation.
15. AI summary caching.
16. AI cache invalidation after book updates.
17. Automated API testing.
18. Structured API error handling.

---

### 3. Maintainability

The application is designed with modularity in mind:

1. Flask Blueprints separate API responsibilities.
2. SQLAlchemy separates database models from route logic.
3. Authentication is implemented through reusable decorators.
4. Role authorization is implemented through a reusable roles_required() decorator.
5. Configuration is managed through environment variables.
6. AI integration is isolated in its own route module.
7. AI responses are cached independently from the core book workflow.
8. Automated API tests are maintained separately from application code.

---

### 4. AI-Powered Book Summary

The AI feature is implemented as a dedicated summary engine using the **UserFacet AI API with GPT-4o-mini**.

The workflow is:

1. The authenticated user requests a summary for a book.
2. The system validates the requested summary style.
3. A SHA-256 content hash is generated using the book information and requested style.
4. The system checks whether a matching summary already exists in the database cache.
5. If a cached summary exists, it is returned without making another AI request.
6. If no cached summary exists, the backend builds a structured prompt using the book's title, author, category, description, and content excerpt.
7. The request is sent securely from the backend to the UserFacet AI API.
8. The generated structured summary is validated.
9. The summary is stored in `BookSummaryCache`.
10. The generated summary is returned to the user.

Supported summary styles:

- `concise`
- `detailed`
- `academic`
- `casual`


---

### 5. Entities

The system is designed around the following core entities:

- **User** — Stores members, librarians, and administrators with role-based permissions.
- **Book** — Stores book metadata, inventory, descriptions, and content excerpts.
- **BorrowRecord** — Tracks book issues, due dates, returns, and fines.
- **Reservation** — Maintains the waiting queue for unavailable books.
- **Review** — Stores user ratings and reviews for books.
- **BookSummaryCache** — Stores previously generated AI summaries to avoid unnecessary AI API calls.


---

## Installation & Setup

### 1. Prerequisites
* Python 3.9+
*  Git
* `pip`
* `venv`

--- 

### 2. Clone the Repository

```bash
git clone https://github.com/shivashishyadav/eLibraryManagementSystem.git
cd eLibraryManagementSystem
```

---

### 3. Environment Setup
Navigate to the backend directory and set up a virtual environment:

```bash
cd backend
python -m venv venv

```
#### Activate it on Windows:
```bash
cd backend
.\venv\Scripts\Activate.ps1   
```
#### For Git Bash:
```bash
cd backend
source venv/Scripts/activate
```
---

### 4. Install Dependencies
```bash
pip install -r requirements.txt 
 ```


---

### 5. Configuration (.env)
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


## Complete Documentation
### [Want to See full Documentation](https://github.com/shivashishyadav/eLibraryManagementSystem/blob/main/backend/documentation.md)