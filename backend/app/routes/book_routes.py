"""Routes for book management, search, and reviews."""

from flask import Blueprint, request, jsonify
from app import db
from app.models import Book, Review, BorrowRecord, Reservation, BookSummaryCache
from app.utils import token_required, roles_required

book_bp = Blueprint('books', __name__, url_prefix='/api/v1/books')


def _parse_total_copies(value):
    """Return a valid positive copy count or ``None``."""
    if isinstance(value, bool) or (isinstance(value, float) and not value.is_integer()):
        return None
    try:
        total_copies = int(value)
    except (TypeError, ValueError):
        return None
    return total_copies if total_copies >= 1 else None


@book_bp.route('', methods=['GET'])
def list_books():
    title = request.args.get('title')
    author = request.args.get('author')
    category = request.args.get('category')
    search = request.args.get('search')
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
    except ValueError:
        return jsonify({'error': {'message': 'page and per_page must be integers'}}), 400

    if page < 1 or per_page < 1 or per_page > 100:
        return jsonify({'error': {'message': 'page must be at least 1 and per_page must be between 1 and 100'}}), 400

    query = Book.query

    if title:
        query = query.filter(Book.title.ilike(f'%{title}%'))
    if author:
        query = query.filter(Book.author.ilike(f'%{author}%'))
    if category:
        query = query.filter(Book.category.ilike(f'%{category}%'))
    if search:
        query = query.filter(
            (Book.title.ilike(f'%{search}%')) |
            (Book.author.ilike(f'%{search}%')) |
            (Book.description.ilike(f'%{search}%'))
        )

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    books = pagination.items

    return jsonify({
        'books': [{
            'id': b.id, 'title': b.title, 'author': b.author,
            'isbn': b.isbn, 'category': b.category,
            'available_copies': b.available_copies, 'total_copies': b.total_copies
        } for b in books],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200

@book_bp.route('/<int:book_id>', methods=['GET'])
def get_book(book_id):
    book = Book.query.get_or_404(book_id)
    reviews = Review.query.filter_by(book_id=book.id).all()
    avg_rating = (sum(r.rating for r in reviews) / len(reviews)) if reviews else None

    return jsonify({
        'id': book.id,
        'title': book.title,
        'author': book.author,
        'isbn': book.isbn,
        'category': book.category,
        'description': book.description,
        'content_excerpt': book.content_excerpt,
        'total_copies': book.total_copies,
        'available_copies': book.available_copies,
        'average_rating': round(avg_rating, 2) if avg_rating else None,
        'reviews_count': len(reviews)
    }), 200

@book_bp.route('', methods=['POST'])
@token_required
@roles_required('librarian', 'admin')
def create_book(current_user):
    data = request.get_json() or {}
    if not isinstance(data, dict):
        return jsonify({'error': {'message': 'Request body must be a JSON object'}}), 400
    required = ['title', 'author', 'isbn', 'category']
    if not all(isinstance(data.get(k), str) and data[k].strip() for k in required):
        return jsonify({'error': {'message': f'Missing required fields: {required}'}}), 400

    if Book.query.filter_by(isbn=data['isbn']).first():
        return jsonify({'error': {'message': 'Book with this ISBN already exists'}}), 409

    total = _parse_total_copies(data.get('total_copies', 1))
    if total is None:
        return jsonify({'error': {'message': 'total_copies must be a positive integer'}}), 400

    book = Book(
        title=data['title'],
        author=data['author'],
        isbn=data['isbn'],
        category=data['category'],
        description=data.get('description'),
        content_excerpt=data.get('content_excerpt'),
        total_copies=total,
        available_copies=total
    )
    db.session.add(book)
    db.session.commit()
    return jsonify({'message': 'Book added successfully', 'book_id': book.id}), 201


@book_bp.route('/<int:book_id>', methods=['PUT'])
@token_required
@roles_required('librarian', 'admin')
def update_book(current_user, book_id):
    book = Book.query.get_or_404(book_id)
    data = request.get_json() or {}
    if not isinstance(data, dict):
        return jsonify({'error': {'message': 'Request body must be a JSON object'}}), 400
    allowed_fields = ['title', 'author', 'isbn', 'category', 'description', 'content_excerpt', 'total_copies']

    if not any(field in data for field in allowed_fields):
        return jsonify({'error': {'message': f'Provide at least one field to update: {allowed_fields}'}}), 400

    for field in ['title', 'author', 'isbn', 'category']:
        if field in data and (not isinstance(data[field], str) or not data[field].strip()):
            return jsonify({'error': {'message': f'{field} must be a non-empty string'}}), 400

    for field in ['description', 'content_excerpt']:
        if field in data and data[field] is not None and not isinstance(data[field], str):
            return jsonify({'error': {'message': f'{field} must be a string or null'}}), 400

    if 'isbn' in data and data['isbn'] != book.isbn:
        if Book.query.filter_by(isbn=data['isbn']).first():
            return jsonify({'error': {'message': 'Book with this ISBN already exists'}}), 409

    if 'total_copies' in data:
        total_copies = _parse_total_copies(data['total_copies'])
        if total_copies is None:
            return jsonify({'error': {'message': 'total_copies must be a positive integer'}}), 400

        borrowed_copies = book.total_copies - book.available_copies
        if total_copies < borrowed_copies:
            return jsonify({
                'error': {
                    'message': f'total_copies cannot be lower than the {borrowed_copies} currently borrowed copy/copies'
                }
            }), 400
        book.total_copies = total_copies
        book.available_copies = total_copies - borrowed_copies

    for field in ['title', 'author', 'isbn', 'category', 'description', 'content_excerpt']:
        if field in data:
            setattr(book, field, data[field])

    # Remove summaries because this content may have changed.
    if any(field in data for field in ['title', 'author', 'category', 'description', 'content_excerpt']):
        BookSummaryCache.query.filter_by(book_id=book.id).delete(synchronize_session=False)

    db.session.commit()
    return jsonify({'message': 'Book updated successfully', 'book_id': book.id}), 200


@book_bp.route('/<int:book_id>', methods=['DELETE'])
@token_required
@roles_required('librarian', 'admin')
def delete_book(current_user, book_id):
    book = Book.query.get_or_404(book_id)

    if BorrowRecord.query.filter_by(book_id=book.id).first() or Reservation.query.filter_by(book_id=book.id).first():
        return jsonify({
            'error': {
                'message': 'Book cannot be deleted because it has borrowing or reservation records'
            }
        }), 409

    db.session.delete(book)
    db.session.commit()
    return jsonify({'message': 'Book deleted successfully', 'book_id': book_id}), 200


@book_bp.route('/<int:book_id>/reviews', methods=['GET'])
def list_reviews(book_id):
    Book.query.get_or_404(book_id)
    reviews = Review.query.filter_by(book_id=book_id).order_by(Review.created_at.desc()).all()

    return jsonify({
        'reviews': [{
            'id': review.id,
            'rating': review.rating,
            'comment': review.comment,
            'created_at': review.created_at.isoformat()
        } for review in reviews],
        'total': len(reviews)
    }), 200


@book_bp.route('/<int:book_id>/reviews', methods=['POST'])
@token_required
def add_review(current_user, book_id):
    Book.query.get_or_404(book_id)
    data = request.get_json() or {}
    if not isinstance(data, dict):
        return jsonify({'error': {'message': 'Request body must be a JSON object'}}), 400
    rating = data.get('rating')

    try:
        rating = int(data.get('rating'))
    except (TypeError, ValueError):
        return jsonify({
            'error': {
                'message': 'Rating must be an integer between 1 and 5'
            }
        }), 400

    if not 1 <= rating <= 5:
        return jsonify({
            'error': {
                'message': 'Rating must be an integer between 1 and 5'
            }
        }), 400
        
        
    existing = Review.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    if existing:
        existing.rating = rating
        existing.comment = data.get('comment')
        db.session.commit()
        return jsonify({'message': 'Review updated successfully'}), 200

    review = Review(user_id=current_user.id, book_id=book_id, rating=rating, comment=data.get('comment'))
    db.session.add(review)
    db.session.commit()
    return jsonify({'message': 'Review submitted successfully'}), 201
