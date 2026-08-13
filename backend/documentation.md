# E-Library Management System API

A backend REST API for an **E-Library Management System** built with **Python, Flask, SQLAlchemy, SQLite, JWT Authentication, and UserFacet AI API (GPT-4o-mini)**.

The system provides book management, user authentication, borrowing, returning, reservations/waitlists, reviews, searching, pagination, and an AI-powered book summary engine with database caching.

---

# A. Tech Stack

* **Python**
* **Flask**
* **Flask-SQLAlchemy**
* **SQLite**
* **JWT Authentication**
* **Passlib / PBKDF2-SHA256**
* **Requests**
* **python-dotenv**
* **UserFacet AI API**
* **GPT-4o-mini**

---

# B. Project Structure

```text
backend/
│
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── models.py
│   ├── utils.py
│   │
│   └── routes/
│       ├── auth_routes.py
│       ├── book_routes.py
│       ├── borrow_routes.py
│       └── ai_routes.py
│
├── .env
├── .gitignore
├── requirements.txt
├── run.py
└── README.md
```

---

# C. Environment Variables

Create a `.env` file in the backend root directory.

```env
SECRET_KEY=your-secret-key

DATABASE_URL=sqlite:///elibrary.db

AI_BASE_URL=https://ai-api.userfacet.com
AI_API_TOKEN=YOUR_USERFACET_AI_TOKEN
```

---

# D. Install Dependencies

Create and activate a virtual environment:

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

If you don't have `requirements.txt`, install:

```bash
pip install flask flask-sqlalchemy pyjwt passlib requests python-dotenv
```

---

# E. Run the Application

```bash
python run.py
```

The API should be available at:

```text
http://127.0.0.1:5000
```

---

# F. API Base URL

```text
http://127.0.0.1:5000
```

---

# G. Authentication

The application uses JWT Bearer authentication.

After login, copy the returned:

```text
access_token
```

For protected endpoints, send:

```text
Authorization: Bearer YOUR_ACCESS_TOKEN
```

---

# H. API Endpoint Reference

## Health Check

| Method | Endpoint  | Auth | Description               |
| ------ | --------- | ---- | ------------------------- |
| GET    | `/health` | None | Returns API health status |

## Authentication

| Method | Endpoint                | Auth | Description           |
| ------ | ----------------------- | ---- | --------------------- |
| POST   | `/api/v1/auth/register` | None | Register a member     |
| POST   | `/api/v1/auth/login`    | None | Login and receive JWT |
| GET    | `/api/v1/auth/me`       | JWT  | Get current user      |

## Books

| Method | Endpoint                     | Auth            | Description                     |
| ------ | ---------------------------- | --------------- | ------------------------------- |
| GET    | `/api/v1/books`              | None            | List, search and paginate books |
| GET    | `/api/v1/books/<id>`         | None            | Get book details                |
| POST   | `/api/v1/books`              | Librarian/Admin | Add a book                      |
| PUT    | `/api/v1/books/<id>`         | Librarian/Admin | Update one or more book fields  |
| DELETE | `/api/v1/books/<id>`         | Librarian/Admin | Delete a book without loan/reservation history |
| GET    | `/api/v1/books/<id>/reviews` | None            | List book reviews               |
| POST   | `/api/v1/books/<id>/reviews` | JWT             | Create/update the caller's review |

## Borrowing & Reservations

| Method | Endpoint                     | Auth | Description            |
| ------ | ---------------------------- | ---- | ---------------------- |
| POST   | `/api/v1/borrow/issue`       | JWT  | Borrow a book          |
| POST   | `/api/v1/borrow/return/<id>` | JWT  | Return own loan; librarian/admin may return any loan |
| POST   | `/api/v1/borrow/reserve`     | JWT  | Join waitlist          |
| GET    | `/api/v1/borrow/my-borrows`  | JWT  | View current user's loans |
| GET    | `/api/v1/borrow/reservations` | JWT | View current user's reservations |
| DELETE | `/api/v1/borrow/reserve/<id>` | JWT | Cancel a waiting reservation |
| GET    | `/api/v1/borrow/loans`       | Librarian/Admin | View loans by status |

## AI Summary

| Method | Endpoint                    | Auth | Description              |
| ------ | --------------------------- | ---- | ------------------------ |
| GET    | `/api/v1/ai/usage`          | JWT  | Check UserFacet AI quota |
| POST   | `/api/v1/ai/summarize/<id>` | JWT  | Generate AI book summary |

---

# I. API TESTING — (1 TO 26)

The following tests should be performed in this order.

---

## TEST 1 — Health Check

### Endpoint

```http
GET /health
```

### URL

```text
http://127.0.0.1:5000/health
```

### Authentication

None.

### Expected Response

```json
{
    "status": "ok"
}
```

### Expected Status

```text
200 OK
```

---

# TEST 2 — Register Member

### Endpoint

```http
POST /api/v1/auth/register
```

### URL

```text
http://127.0.0.1:5000/api/v1/auth/register
```

### Headers

```text
Content-Type: application/json
```

### Body

```json
{
    "username": "alice",
    "email": "alice@example.com",
    "password": "password123"
}
```

### Expected Response

```json
{
    "message": "User registered successfully",
    "user": {
        "id": 1,
        "username": "alice",
        "role": "member"
    }
}
```

### Expected Status

```text
201 Created
```

---

# TEST 3 — Librarian Provisioning

Public registration creates only `member` accounts. Create librarian accounts through a controlled administrative or database provisioning process. Requests that include `"role": "librarian"` at the public registration endpoint return `403 Forbidden`.

---

# TEST 4 — Duplicate Registration

Send the same member registration request again.

### Body

```json
{
    "username": "alice",
    "email": "alice@example.com",
    "password": "password123"
}
```

### Expected Response

```json
{
    "error": {
        "message": "User with this email or username already exists"
    }
}
```

### Expected Status

```text
409 Conflict
```

---

# TEST 5 — Login Member

### Endpoint

```http
POST /api/v1/auth/login
```

### URL

```text
http://127.0.0.1:5000/api/v1/auth/login
```

### Headers

```text
Content-Type: application/json
```

### Body

```json
{
    "email": "alice@example.com",
    "password": "password123"
}
```

### Expected Response

```json
{
    "access_token": "YOUR_JWT_TOKEN",
    "role": "member",
    "expires_in": 86400
}
```

### Expected Status

```text
200 OK
```

### Important

Copy the `access_token`.

Use it for subsequent authenticated requests:

```text
Authorization: Bearer YOUR_JWT_TOKEN
```

---

# TEST 6 — Invalid Login

### Endpoint

```http
POST /api/v1/auth/login
```

### Body

```json
{
    "email": "alice@example.com",
    "password": "wrongpassword"
}
```

### Expected Response

```json
{
    "error": {
        "message": "Invalid email or password"
    }
}
```

### Expected Status

```text
401 Unauthorized
```

---

# TEST 7 — Get Current User

### Endpoint

```http
GET /api/v1/auth/me
```

### URL

```text
http://127.0.0.1:5000/api/v1/auth/me
```

### Headers

```text
Authorization: Bearer ALICE_JWT_TOKEN
```

### Expected Response

```json
{
    "id": 1,
    "username": "alice",
    "email": "alice@example.com",
    "role": "member"
}
```

### Expected Status

```text
200 OK
```

---

# TEST 8 — `/me` Without Token

Remove the Authorization header.

### Endpoint

```http
GET /api/v1/auth/me
```

### Expected Response

```json
{
    "error": {
        "message": "Access token is missing",
        "type": "auth_error"
    }
}
```

### Expected Status

```text
401 Unauthorized
```

---

# TEST 9 — List Books

### Endpoint

```http
GET /api/v1/books
```

### URL

```text
http://127.0.0.1:5000/api/v1/books
```

### Authentication

None.

Initially, if there are no books:

```json
{
    "books": [],
    "total": 0,
    "pages": 0,
    "current_page": 1
}
```

### Expected Status

```text
200 OK
```

---

# TEST 10 — Create a Book

Login as the librarian first.

Use the librarian JWT token.

### Endpoint

```http
POST /api/v1/books
```

### URL

```text
http://127.0.0.1:5000/api/v1/books
```

### Headers

```text
Authorization: Bearer LIBRARIAN_JWT_TOKEN
Content-Type: application/json
```

### Body

```json
{
    "title": "The Alchemist",
    "author": "Paulo Coelho",
    "isbn": "9780061122415",
    "category": "Fiction",
    "description": "A young shepherd travels in search of treasure and discovers the meaning of his dreams.",
    "content_excerpt": "Santiago is a young shepherd who dreams of finding treasure near the Egyptian pyramids.",
    "total_copies": 3
}
```

### Expected Response

```json
{
    "message": "Book added successfully",
    "book_id": 1
}
```

### Expected Status

```text
201 Created
```

---

# TEST 11 — Get Book Details

### Endpoint

```http
GET /api/v1/books/1
```

### URL

```text
http://127.0.0.1:5000/api/v1/books/1
```

### Authentication

None.

### Expected Response

```json
{
    "id": 1,
    "title": "The Alchemist",
    "author": "Paulo Coelho",
    "isbn": "9780061122415",
    "category": "Fiction",
    "description": "A young shepherd travels in search of treasure and discovers the meaning of his dreams.",
    "content_excerpt": "Santiago is a young shepherd who dreams of finding treasure near the Egyptian pyramids.",
    "total_copies": 3,
    "available_copies": 3,
    "average_rating": null,
    "reviews_count": 0
}
```

### Expected Status

```text
200 OK
```

---

# TEST 12 — Search Books

### Endpoint

```http
GET /api/v1/books?search=alchemist
```

### URL

```text
http://127.0.0.1:5000/api/v1/books?search=alchemist
```

### Authentication

None.

The book containing "Alchemist" should appear in the result.

### Additional Search Tests

Search by author:

```text
GET /api/v1/books?author=Paulo
```

Search by category:

```text
GET /api/v1/books?category=Fiction
```

Search by title:

```text
GET /api/v1/books?title=Alchemist
```

---

# TEST 13 — Pagination

Add multiple books and test:

```text
GET /api/v1/books?page=1&per_page=2
```

### URL

```text
http://127.0.0.1:5000/api/v1/books?page=1&per_page=2
```

### Expected Response Structure

```json
{
    "books": [],
    "total": 5,
    "pages": 3,
    "current_page": 1
}
```

The exact values depend on the number of books in the database.

---

# TEST 14 — Borrow a Book

Use Alice's member JWT.

### Endpoint

```http
POST /api/v1/borrow/issue
```

### URL

```text
http://127.0.0.1:5000/api/v1/borrow/issue
```

### Headers

```text
Authorization: Bearer ALICE_JWT_TOKEN
Content-Type: application/json
```

### Body

```json
{
    "book_id": 1
}
```

### Expected Response

```json
{
    "message": "Book issued successfully",
    "borrow_id": 1,
    "due_date": "2026-08-27T..."
}
```

### Expected Status

```text
200 OK
```

---

# TEST 15 — Verify Available Copies Decreased

### Endpoint

```http
GET /api/v1/books/1
```

Before borrowing:

```text
available_copies = 3
```

After borrowing:

```text
available_copies = 2
```

This confirms that inventory is being updated correctly.

---

# TEST 16 — Duplicate Borrowing

Alice tries to borrow the same book again.

### Endpoint

```http
POST /api/v1/borrow/issue
```

### Body

```json
{
    "book_id": 1
}
```

### Expected Response

```json
{
    "error": {
        "message": "You already have an active loan for this book"
    }
}
```

### Expected Status

```text
400 Bad Request
```

---

# TEST 17 — Borrow Until No Copies Are Available

Use multiple users to borrow all available copies.

Once:

```text
available_copies = 0
```

try borrowing again.

### Body

```json
{
    "book_id": 1
}
```

### Expected Response

```json
{
    "error": {
        "message": "No copies available. Consider reserving this book."
    }
}
```

### Expected Status

```text
409 Conflict
```

---

# TEST 18 — Reserve a Book

When no copies are available:

### Endpoint

```http
POST /api/v1/borrow/reserve
```

### URL

```text
http://127.0.0.1:5000/api/v1/borrow/reserve
```

### Headers

```text
Authorization: Bearer ALICE_JWT_TOKEN
Content-Type: application/json
```

### Body

```json
{
    "book_id": 1
}
```

### Expected Response

```json
{
    "message": "Added to waitlist",
    "queue_position": 1
}
```

### Expected Status

```text
201 Created
```

---

# TEST 19 — Duplicate Reservation

Send the same reservation again.

### Body

```json
{
    "book_id": 1
}
```

### Expected Response

```json
{
    "message": "You are already in the queue for this book"
}
```

### Expected Status

```text
409 Conflict
```

---

# TEST 20 — Return a Book

Use the borrower token.

### Endpoint

```http
POST /api/v1/borrow/return/1
```

### URL

```text
http://127.0.0.1:5000/api/v1/borrow/return/1
```

### Headers

```text
Authorization: Bearer ALICE_JWT_TOKEN
```

### Expected Response

```json
{
    "message": "Book returned successfully",
    "fine_amount": 0.0,
    "reservation_update": "Stock replenished"
}
```

### Expected Status

```text
200 OK
```

If there is a waiting reservation, the response may instead indicate that the book was automatically assigned to the waiting user.

---

# TEST 21 — Submit a Book Review

### Endpoint

```http
POST /api/v1/books/1/reviews
```

### URL

```text
http://127.0.0.1:5000/api/v1/books/1/reviews
```

### Headers

```text
Authorization: Bearer ALICE_JWT_TOKEN
Content-Type: application/json
```

### Body

```json
{
    "rating": 5,
    "comment": "Excellent book. Very inspiring."
}
```

### Expected Response

```json
{
    "message": "Review submitted successfully"
}
```

### Expected Status

```text
201 Created
```

---

# TEST 22 — Verify Rating

### Endpoint

```http
GET /api/v1/books/1
```

### Expected Response

The response should now contain:

```json
{
    "average_rating": 5.0,
    "reviews_count": 1
}
```

The exact rating depends on submitted reviews.

---

# TEST 23 — Update Existing Review

Send another review from the same user.

### Endpoint

```http
POST /api/v1/books/1/reviews
```

### Body

```json
{
    "rating": 4,
    "comment": "Still a great book."
}
```

### Expected Response

```json
{
    "message": "Review updated successfully"
}
```

### Expected Status

```text
200 OK
```

The system updates the existing review instead of creating a duplicate review for the same user and book.

---

# TEST 24 — Check UserFacet AI Usage

### Endpoint

```http
GET /api/v1/ai/usage
```

### URL

```text
http://127.0.0.1:5000/api/v1/ai/usage
```

### Headers

```text
Authorization: Bearer ALICE_JWT_TOKEN
```

### Expected Response

```json
{
    "email": "alice@example.com",
    "used": 0,
    "limit": 100,
    "remaining": 100
}
```

The actual numbers depend on our UserFacet account usage.

### Important

The client sends its application's JWT to Flask.

Flask internally sends the UserFacet API token to:

```text
https://ai-api.userfacet.com/v1/usage
```

The UserFacet token must never be exposed to the client.

---

# TEST 25 — Generate AI Book Summary

### Endpoint

```http
POST /api/v1/ai/summarize/1
```

### URL

```text
http://127.0.0.1:5000/api/v1/ai/summarize/1
```

### Headers

```text
Authorization: Bearer ALICE_JWT_TOKEN
Content-Type: application/json
```

### Body

```json
{
    "style": "concise"
}
```

### Expected Response

```json
{
    "book_id": 1,
    "title": "The Alchemist",
    "summary_style": "concise",
    "summary": "The Alchemist follows Santiago, a young shepherd who...",
    "cached": false
}
```

### Expected Status

```text
200 OK
```

The exact AI-generated summary will be different.

---

# TEST 26 — Verify AI Summary Cache

Send exactly the same request again:

### Endpoint

```http
POST /api/v1/ai/summarize/1
```

### Body

```json
{
    "style": "concise"
}
```

### Expected Response

```json
{
    "book_id": 1,
    "title": "The Alchemist",
    "summary_style": "concise",
    "summary": "The Alchemist follows Santiago, a young shepherd who...",
    "cached": true
}
```

The important difference is:

```json
"cached": true
```

The second request should be served from the database cache rather than making another AI request.
---


# Test 27 — Update Book Title

<!-- Legacy draft retained for source history; the corrected endpoint tests are below.
```Endpoint
PUT /api/v1/books/<book_id>
```

```URL
http://127.0.0.1:5000/api/v1/books/1
```
```
Authentication
Authorization: Bearer LIBRARIAN_JWT_TOKEN
```
```
Headers
Content-Type: application/json
Authorization: Bearer LIBRARIAN_JWT_TOKEN
```
```
Body
{
    "title": "The Alchemist - Updated Edition"
}
Expected Response
{
    "message": "Book updated successfully",
    "book_id": 1
}
```
```
Expected Status
200 OK
```
```
Verify the change:

GET /api/v1/books/1

The response should contain:

{
    "id": 1,
    "title": "The Alchemist - Updated Edition"
}
```
### Test 27.2 — Update Multiple Fields
```Body
{
    "title": "The Alchemist",
    "category": "Literary Fiction",
    "description": "An inspiring story about following dreams and discovering one's purpose.",
    "content_excerpt": "Santiago begins a journey to discover a hidden treasure and ultimately discovers the importance of his own journey."
}
```

```
Expected Response
{
    "message": "Book updated successfully",
    "book_id": 1
}
```
Expected Status
200 OK


---

-->

# TEST 27 â€” Update a Book

Only a librarian or admin can update a book. Send only the fields that need to change.

```http
PUT /api/v1/books/1
Authorization: Bearer LIBRARIAN_JWT_TOKEN
Content-Type: application/json
```

```json
{
    "title": "The Alchemist - Updated Edition",
    "description": "An inspiring story about following dreams and discovering one's purpose."
}
```

Expected response:

```json
{
    "message": "Book updated successfully",
    "book_id": 1
}
```

`total_copies` must be a positive integer and cannot be lower than the number of copies currently borrowed. Updating title, author, category, description, or excerpt removes cached AI summaries for that book.

---

# TEST 28 â€” Delete a Book

Only a librarian or admin can delete a book. Deletion is allowed only when the book has no borrowing or reservation records.

```http
DELETE /api/v1/books/1
Authorization: Bearer LIBRARIAN_JWT_TOKEN
```

Expected response:

```json
{
    "message": "Book deleted successfully",
    "book_id": 1
}
```

---

# TEST 29 â€” View Reviews

```http
GET /api/v1/books/1/reviews
```

Expected response structure:

```json
{
    "reviews": [
        {
            "id": 1,
            "rating": 5,
            "comment": "Excellent book. Very inspiring.",
            "created_at": "2026-08-14T00:00:00"
        }
    ],
    "total": 1
}
```

---

# TEST 30 â€” View and Cancel Reservations

```http
GET /api/v1/borrow/reservations
Authorization: Bearer ALICE_JWT_TOKEN
```

To cancel a waiting reservation:

```http
DELETE /api/v1/borrow/reserve/1
Authorization: Bearer ALICE_JWT_TOKEN
```

---

# TEST 31 â€” View Loans

The authenticated user can view their own loan history:

```http
GET /api/v1/borrow/my-borrows
Authorization: Bearer ALICE_JWT_TOKEN
```

A librarian or admin can view all loans by status:

```http
GET /api/v1/borrow/loans?status=overdue
Authorization: Bearer LIBRARIAN_JWT_TOKEN
```

# J. Additional AI Style Tests

The AI summary endpoint supports four styles.

## Concise

```json
{
    "style": "concise"
}
```

## Detailed

```json
{
    "style": "detailed"
}
```

## Academic

```json
{
    "style": "academic"
}
```

## Casual

```json
{
    "style": "casual"
}
```

Each style is cached separately.

For example:

```text
Book 1 + concise
Book 1 + detailed
Book 1 + academic
Book 1 + casual
```

represent four different cache entries.

---

# K. Invalid AI Style Test

Send:

```json
{
    "style": "funny"
}
```

Expected:

```json
{
    "error": {
        "message": "Invalid style. Pick: concise, detailed, academic, casual"
    }
}
```

Expected status:

```text
400 Bad Request
```

---

# L. AI Authentication Test

Remove the JWT from:

```text
POST /api/v1/ai/summarize/1
```

Expected:

```json
{
    "error": {
        "message": "Access token is missing",
        "type": "auth_error"
    }
}
```

Expected status:

```text
401 Unauthorized
```

---

# M. Role-Based Access Testing

The following tests verify authorization.

## Member trying to create a book

```text
POST /api/v1/books
```

Use:

```text
Authorization: Bearer ALICE_JWT_TOKEN
```

Expected:

```text
403 Forbidden
```

because creating books is restricted to:

```text
librarian
admin
```

---

# N. Complete Testing Flow

The recommended assessment demonstration flow is:

```text
1. GET /health
        ↓
2. Register member
        ↓
3. Provision a librarian account
        ↓
4. Login member
        ↓
5. Login librarian
        ↓
6. GET /me
        ↓
7. Librarian creates book
        ↓
8. GET books
        ↓
9. Search books
        ↓
10. Get book details
        ↓
11. Member borrows book
        ↓
12. Verify available_copies decreased
        ↓
13. Member reviews book
        ↓
14. Verify rating
        ↓
15. Consume all copies
        ↓
16. Another member tries borrowing
        ↓
17. Reservation / waitlist
        ↓
18. Return book
        ↓
19. Verify reservation handling
        ↓
20. GET AI usage
        ↓
21. Generate AI summary
        ↓
22. Generate same summary again
        ↓
23. Verify cached = true
        ↓
24. Test all four AI styles
        ↓
25. Test invalid AI style
        ↓
26. Test invalid / missing JWT
        ↓
27. Update a book
       ↓
28. Delete an unused book
       ↓
29. View book reviews
       ↓
30. View and cancel a reservation
       ↓
31. View member and librarian loan lists
```

---

# O. Important Security Considerations

## Never expose the UserFacet AI token

The UserFacet token should only exist in:

```text
.env
```

Example:

```env
AI_API_TOKEN=YOUR_USERFACET_TOKEN
```

Do not put the token in:

* README
* GitHub
* frontend code
* Postman public collections
* JavaScript files
* screenshots
* source code

---

# P. Application JWT vs UserFacet Token

There are two different authentication mechanisms.

### Application JWT

Generated by:

```text
POST /api/v1/auth/login
```

Used by the client:

```text
Authorization: Bearer YOUR_APPLICATION_JWT
```

### UserFacet AI Token

Stored on the server:

```env
AI_API_TOKEN=YOUR_USERFACET_TOKEN
```

Used internally by Flask:

```text
Flask Backend
      |
      | Bearer AI_API_TOKEN
      ↓
UserFacet AI API
      |
      ↓
GPT-4o-mini
```

The client never sees the UserFacet token.

---

# Q. AI Architecture

The AI summary workflow is:

```text
Client
   |
   | POST /api/v1/ai/summarize/1
   | JWT
   ↓
Flask Backend
   |
   | Check JWT
   ↓
Book Database
   |
   | title
   | author
   | category
   | description
   | content excerpt
   ↓
Generate Content Hash
   |
   ↓
Check BookSummaryCache
   |
   +-------- Cache Found --------+
   |                             |
   |                             ↓
   |                       Return Cached
   |
   +-------- Cache Missing ------+
                                 |
                                 ↓
                         UserFacet AI API
                                 |
                                 ↓
                            GPT-4o-mini
                                 |
                                 ↓
                          Generated Summary
                                 |
                                 ↓
                         Store in Database
                                 |
                                 ↓
                           Return Summary
```

---

# R. Why AI Caching Is Used

The UserFacet API provides a quota of:

```text
100 calls
```

Therefore, repeatedly generating the same summary would unnecessarily consume quota.

The application generates a SHA-256 hash using the book information and summary style.

For example:

```text
Book content + concise
```

generates one cache entry.

A repeated request for the same content and style returns the cached result.

This provides:

* Reduced AI API usage
* Faster response time
* Lower external dependency
* Consistent summaries
* Better handling of API quotas

---

# S. Business Rules

The current system implements the following rules:

### Borrow Limit

```text
Maximum active books per user = 5
```

### Loan Period

```text
Default loan period = 14 days
```

### Fine

```text
Daily fine = 1.50
```

### Duplicate Borrowing

A user cannot have multiple active loans for the same book.

### Reservation

Users can join the waitlist when:

```text
available_copies = 0
```

### Reviews

A user can have one review per book. Sending another review updates the existing review.

---

# T. Important Edge Cases

The API handles several important edge cases:

* Duplicate user registration
* Invalid login
* Missing JWT
* Invalid JWT
* Expired JWT
* Unauthorized role
* Duplicate ISBN
* Borrowing unavailable books
* Borrowing the same book twice
* Exceeding borrowing limit
* Duplicate reservations
* Returning an already returned book
* Unauthorized return
* Invalid review rating
* Duplicate reviews
* Invalid AI summary style
* AI service failure
* AI response caching
* Book-not-found handling through `404`
* User-not-found handling
* AI quota handling through UserFacet API

---

# U. Important Configuration

Current application configuration:

```python
MAX_BORROW_LIMIT = 5
DEFAULT_LOAN_DAYS = 14
DAILY_FINE_RATE = 1.50
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
```

---

# V. Example Postman Authorization

For protected endpoints:

```text
Authorization
```

Type:

```text
Bearer Token
```

Token:

```text
YOUR_JWT_TOKEN
```

Postman automatically sends:

```http
Authorization: Bearer YOUR_JWT_TOKEN
```

---

# W. Example Request Headers

For JSON POST requests:

```http
Content-Type: application/json
Authorization: Bearer YOUR_JWT_TOKEN
```

For public GET requests:

```http
Content-Type: application/json
```

Authorization is not required for public endpoints.

---

# X. Expected HTTP Status Codes

| Status | Meaning                         |
| ------ | ------------------------------- |
| 200    | Successful request              |
| 201    | Resource successfully created   |
| 400    | Invalid request                 |
| 401    | Authentication required/invalid |
| 403    | Insufficient permissions        |
| 404    | Resource not found              |
| 409    | Conflict                        |
| 502    | AI upstream communication error |
| 503    | AI service unavailable          |

---

# Y. API Error Format

Application errors generally follow:

```json
{
    "error": {
        "message": "Error description",
        "type": "error_type"
    }
}
```

Example:

```json
{
    "error": {
        "message": "Access token is missing",
        "type": "auth_error"
    }
}
```

---

# Z. Final API Checklist

Before submitting the assessment, verify:

* [✔] Flask server starts successfully
* [✔] `/health` returns 200
* [✔] Member registration works
* [✔] Librarian registration works
* [✔] Duplicate registration returns 409
* [✔] Login returns JWT
* [✔] Invalid login returns 401
* [✔] `/me` works with JWT
* [✔] `/me` rejects missing JWT
* [✔] Librarian can create books
* [✔] Member cannot create books
* [✔] Book listing works
* [✔] Book search works
* [✔] Book pagination works
* [✔] Book details work
* [✔] Borrowing works
* [✔] Available copies decrease after borrowing
* [✔] Duplicate borrowing is prevented
* [✔] Waitlist works
* [✔] Duplicate reservations are prevented
* [✔] Returning works
* [✔] Fine calculation works
* [✔] Reviews work
* [✔] Review update works
* [✔] AI usage endpoint works
* [✔] AI summary generation works
* [✔] AI summary caching works
* [✔] All four AI styles work
* [✔] Invalid AI style returns 400
* [✔] UserFacet API token is stored only in `.env`
* [✔] `.env` is included in `.gitignore`
* [✔] No API token is committed to GitHub

---

# Final Architecture

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
   Admin                Reservations        |
          |                |                |
          +----------------+----------------+
                           |
                      SQLAlchemy
                           |
                         SQLite
```

The backend therefore provides the core functionality expected from a digital library while also demonstrating authentication, authorization, database relationships, business rules, search, pagination, borrowing workflows, reservations, reviews, external API integration, caching, and AI-powered functionality.
