import pytest

from app import create_app, db
from app.config import Config
from app.models import User


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    SECRET_KEY = 'test-secret-key'


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        librarian = User(username='librarian', email='librarian@example.com', role='librarian')
        librarian.set_password('password123')
        db.session.add(librarian)
        db.session.commit()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, email, password='password123'):
    response = client.post('/api/v1/auth/login', json={'email': email, 'password': password})
    return {'Authorization': f"Bearer {response.get_json()['access_token']}"}


def create_book(client, headers, isbn='9780000000001', total_copies=2):
    response = client.post('/api/v1/books', headers=headers, json={
        'title': 'Test Book',
        'author': 'Test Author',
        'isbn': isbn,
        'category': 'Testing',
        'total_copies': total_copies
    })
    assert response.status_code == 201
    return response.get_json()['book_id']


def register_member(client, username, email):
    response = client.post('/api/v1/auth/register', json={
        'username': username,
        'email': email,
        'password': 'password123'
    })
    assert response.status_code == 201
    return login(client, email)


def test_public_registration_cannot_create_librarian(client):
    response = client.post('/api/v1/auth/register', json={
        'username': 'unapproved-librarian',
        'email': 'unapproved@example.com',
        'password': 'password123',
        'role': 'librarian'
    })
    assert response.status_code == 403


def test_librarian_can_update_and_delete_unused_book(client):
    librarian_headers = login(client, 'librarian@example.com')
    book_id = create_book(client, librarian_headers)

    response = client.put(f'/api/v1/books/{book_id}', headers=librarian_headers, json={
        'title': 'Updated Test Book',
        'total_copies': 4
    })
    assert response.status_code == 200

    book = client.get(f'/api/v1/books/{book_id}').get_json()
    assert book['title'] == 'Updated Test Book'
    assert book['available_copies'] == 4

    response = client.delete(f'/api/v1/books/{book_id}', headers=librarian_headers)
    assert response.status_code == 200


def test_member_can_view_loan_history(client):
    librarian_headers = login(client, 'librarian@example.com')
    book_id = create_book(client, librarian_headers)

    member_headers = register_member(client, 'member', 'member@example.com')

    response = client.post('/api/v1/borrow/issue', headers=member_headers, json={'book_id': book_id})
    assert response.status_code == 200

    history = client.get('/api/v1/borrow/my-borrows', headers=member_headers).get_json()
    assert len(history['borrows']) == 1
    assert history['borrows'][0]['book_id'] == book_id
    assert history['borrows'][0]['status'] == 'active'


def test_review_is_listed_and_can_be_updated(client):
    librarian_headers = login(client, 'librarian@example.com')
    book_id = create_book(client, librarian_headers)
    member_headers = register_member(client, 'reviewer', 'reviewer@example.com')

    response = client.post(f'/api/v1/books/{book_id}/reviews', headers=member_headers, json={
        'rating': 5,
        'comment': 'Excellent book'
    })
    assert response.status_code == 201

    response = client.post(f'/api/v1/books/{book_id}/reviews', headers=member_headers, json={
        'rating': 4,
        'comment': 'Still excellent'
    })
    assert response.status_code == 200

    reviews = client.get(f'/api/v1/books/{book_id}/reviews').get_json()
    assert reviews['total'] == 1
    assert reviews['reviews'][0]['rating'] == 4


def test_member_can_view_and_cancel_waiting_reservation(client):
    librarian_headers = login(client, 'librarian@example.com')
    book_id = create_book(client, librarian_headers, total_copies=1)
    borrower_headers = register_member(client, 'borrower', 'borrower@example.com')
    waiting_member_headers = register_member(client, 'waiting', 'waiting@example.com')

    assert client.post('/api/v1/borrow/issue', headers=borrower_headers, json={'book_id': book_id}).status_code == 200
    response = client.post('/api/v1/borrow/reserve', headers=waiting_member_headers, json={'book_id': book_id})
    assert response.status_code == 201

    reservations = client.get('/api/v1/borrow/reservations', headers=waiting_member_headers).get_json()
    assert len(reservations['reservations']) == 1
    reservation_id = reservations['reservations'][0]['id']

    response = client.delete(f'/api/v1/borrow/reserve/{reservation_id}', headers=waiting_member_headers)
    assert response.status_code == 200
    assert client.get('/api/v1/borrow/reservations', headers=waiting_member_headers).get_json()['reservations'] == []


def test_librarian_can_view_loans_and_book_with_history_cannot_be_deleted(client):
    librarian_headers = login(client, 'librarian@example.com')
    book_id = create_book(client, librarian_headers)
    member_headers = register_member(client, 'loanmember', 'loanmember@example.com')
    assert client.post('/api/v1/borrow/issue', headers=member_headers, json={'book_id': book_id}).status_code == 200

    loans = client.get('/api/v1/borrow/loans?status=active', headers=librarian_headers).get_json()
    assert loans['total'] == 1
    assert loans['loans'][0]['book_id'] == book_id

    response = client.delete(f'/api/v1/books/{book_id}', headers=librarian_headers)
    assert response.status_code == 409


def test_invalid_pagination_returns_validation_error(client):
    assert client.get('/api/v1/books?page=invalid').status_code == 400
    assert client.get('/api/v1/books?per_page=101').status_code == 400
