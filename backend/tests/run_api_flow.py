"""Run a visible end-to-end API flow without starting a web server.

Run from the backend directory:
    py -3 tests/run_api_flow.py
"""

import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.config import Config
from app.models import User


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    SECRET_KEY = 'api-flow-test-secret'
    AI_BASE_URL = 'https://mock-ai-service.test'
    AI_API_TOKEN = 'mock-token'


class MockResponse:
    def __init__(self, data, status_code=200):
        self.data = data
        self.status_code = status_code

    def json(self):
        return self.data


class ApiFlow:
    def __init__(self, client):
        self.client = client
        self.completed = 0

    def request(self, name, method, url, expected_status, **kwargs):
        print(f'\n[RUN ] {name}')
        print(f'      {method.upper()} {url}')
        response = getattr(self.client, method.lower())(url, **kwargs)
        if response.status_code != expected_status:
            print(f'[FAIL] Expected {expected_status}, received {response.status_code}')
            print(f'       Response: {response.get_json()}')
            raise SystemExit(1)

        print(f'[PASS] HTTP {response.status_code}')
        self.completed += 1
        return response.get_json()


def auth_headers(token):
    return {'Authorization': f'Bearer {token}'}


def login(flow, email):
    data = flow.request(
        f'Login: {email}', 'post', '/api/v1/auth/login', 200,
        json={'email': email, 'password': 'password123'}
    )
    return auth_headers(data['access_token'])


def main():
    print('=' * 64)
    print(' E-LIBRARY API FLOW TEST')
    print('=' * 64)

    app = create_app(TestConfig)
    with app.app_context():
        librarian = User(username='librarian', email='librarian@example.com', role='librarian')
        librarian.set_password('password123')
        db.session.add(librarian)
        db.session.commit()

        flow = ApiFlow(app.test_client())
        try:
            flow.request('Application information', 'get', '/', 200)
            flow.request('Health check', 'get', '/health', 200)

            flow.request(
                'Register member Alice', 'post', '/api/v1/auth/register', 201,
                json={'username': 'alice', 'email': 'alice@example.com', 'password': 'password123'}
            )
            flow.request(
                'Reject public librarian registration', 'post', '/api/v1/auth/register', 403,
                json={
                    'username': 'unapproved', 'email': 'unapproved@example.com',
                    'password': 'password123', 'role': 'librarian'
                }
            )

            librarian_headers = login(flow, 'librarian@example.com')
            alice_headers = login(flow, 'alice@example.com')
            flow.request('Current-user profile', 'get', '/api/v1/auth/me', 200, headers=alice_headers)

            book = flow.request(
                'Create book', 'post', '/api/v1/books', 201, headers=librarian_headers,
                json={
                    'title': 'The API Test Book', 'author': 'Library Tester', 'isbn': '9780000000001',
                    'category': 'Testing', 'description': 'A book used for API flow tests.',
                    'content_excerpt': 'Testing the library API.', 'total_copies': 2
                }
            )
            book_id = book['book_id']
            flow.request('List books', 'get', '/api/v1/books?search=API&page=1&per_page=10', 200)
            flow.request('Get book details', 'get', f'/api/v1/books/{book_id}', 200)
            flow.request(
                'Update book description', 'put', f'/api/v1/books/{book_id}', 200,
                headers=librarian_headers, json={'description': 'Updated API flow test description.'}
            )

            flow.request(
                'Create review', 'post', f'/api/v1/books/{book_id}/reviews', 201,
                headers=alice_headers, json={'rating': 5, 'comment': 'Clear and useful test book.'}
            )
            flow.request('List reviews', 'get', f'/api/v1/books/{book_id}/reviews', 200)

            loan = flow.request(
                'Borrow book', 'post', '/api/v1/borrow/issue', 200,
                headers=alice_headers, json={'book_id': book_id}
            )
            flow.request('View my borrows', 'get', '/api/v1/borrow/my-borrows', 200, headers=alice_headers)
            flow.request('View librarian loans', 'get', '/api/v1/borrow/loans?status=active', 200, headers=librarian_headers)
            flow.request(
                'Return book', 'post', f"/api/v1/borrow/return/{loan['borrow_id']}", 200,
                headers=alice_headers
            )

            flow.request(
                'Register member Bob', 'post', '/api/v1/auth/register', 201,
                json={'username': 'bob', 'email': 'bob@example.com', 'password': 'password123'}
            )
            bob_headers = login(flow, 'bob@example.com')
            flow.request(
                'Reduce stock to one copy', 'put', f'/api/v1/books/{book_id}', 200,
                headers=librarian_headers, json={'total_copies': 1}
            )
            flow.request('Borrow last copy', 'post', '/api/v1/borrow/issue', 200, headers=alice_headers, json={'book_id': book_id})
            flow.request('Join waitlist', 'post', '/api/v1/borrow/reserve', 201, headers=bob_headers, json={'book_id': book_id})
            reservations = flow.request('View reservations', 'get', '/api/v1/borrow/reservations', 200, headers=bob_headers)
            flow.request(
                'Cancel reservation', 'delete', f"/api/v1/borrow/reserve/{reservations['reservations'][0]['id']}", 200,
                headers=bob_headers
            )

            disposable_book = flow.request(
                'Create disposable book', 'post', '/api/v1/books', 201, headers=librarian_headers,
                json={
                    'title': 'Disposable Test Book', 'author': 'Library Tester', 'isbn': '9780000000002',
                    'category': 'Testing', 'total_copies': 1
                }
            )
            flow.request(
                'Delete unused book', 'delete', f"/api/v1/books/{disposable_book['book_id']}", 200,
                headers=librarian_headers
            )

            with patch('app.routes.ai_routes.requests.get') as mock_get, \
                    patch('app.routes.ai_routes.requests.post') as mock_post:
                mock_get.return_value = MockResponse({'used': 0, 'limit': 100, 'remaining': 100})
                mock_post.return_value = MockResponse({
                    'choices': [{'message': {'content': 'A mocked AI summary for testing.'}}]
                })
                flow.request('Check AI usage (mocked)', 'get', '/api/v1/ai/usage', 200, headers=alice_headers)
                flow.request(
                    'Generate AI summary (mocked)', 'post', f'/api/v1/ai/summarize/{book_id}', 200,
                    headers=alice_headers, json={'style': 'concise'}
                )
                flow.request(
                    'Read cached AI summary', 'post', f'/api/v1/ai/summarize/{book_id}', 200,
                    headers=alice_headers, json={'style': 'concise'}
                )

            print('\n' + '=' * 64)
            print(f' FLOW COMPLETED: {flow.completed} route checks passed')
            print('=' * 64)
        finally:
            db.session.remove()
            db.drop_all()


if __name__ == '__main__':
    main()
