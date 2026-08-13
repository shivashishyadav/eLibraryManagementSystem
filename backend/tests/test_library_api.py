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


def create_book(client, headers):
    response = client.post('/api/v1/books', headers=headers, json={
        'title': 'Test Book',
        'author': 'Test Author',
        'isbn': '9780000000001',
        'category': 'Testing',
        'total_copies': 2
    })
    assert response.status_code == 201
    return response.get_json()['book_id']


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

    client.post('/api/v1/auth/register', json={
        'username': 'member',
        'email': 'member@example.com',
        'password': 'password123'
    })
    member_headers = login(client, 'member@example.com')

    response = client.post('/api/v1/borrow/issue', headers=member_headers, json={'book_id': book_id})
    assert response.status_code == 200

    history = client.get('/api/v1/borrow/my-borrows', headers=member_headers).get_json()
    assert len(history['borrows']) == 1
    assert history['borrows'][0]['book_id'] == book_id
    assert history['borrows'][0]['status'] == 'active'
