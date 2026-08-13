# Book CRUD, search, filter, reviews

from flask import Blueprint, request, jsonify
from app import db
from app.models import Book, Review
from app.utils import token_required, roles_required

book_bp = Blueprint('books', __name__, url_prefix='/api/v1/books')

@book_bp.route('', methods=['GET'])
def list_books():
    title = request.args.get('title')
    author = request.args.get('author')
    category = request.args.get('category')
    search = request.args.get('search')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))

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
    required = ['title', 'author', 'isbn', 'category']
    if not all(k in data for k in required):
        return jsonify({'error': {'message': f'Missing required fields: {required}'}}), 400

    if Book.query.filter_by(isbn=data['isbn']).first():
        return jsonify({'error': {'message': 'Book with this ISBN already exists'}}), 409

    total = data.get('total_copies', 1)
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


@book_bp.route('/<int:book_id>/reviews', methods=['POST'])
@token_required
def add_review(current_user, book_id):
    Book.query.get_or_404(book_id)
    data = request.get_json() or {}
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