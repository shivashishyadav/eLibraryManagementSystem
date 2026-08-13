# Borrow, Return, Reserve waitlist

from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import Book, BorrowRecord, Reservation
from app.utils import token_required, roles_required

borrow_bp = Blueprint('borrow', __name__, url_prefix='/api/v1/borrow')

@borrow_bp.route('/issue', methods=['POST'])
@token_required
def borrow_book(current_user):
    data = request.get_json() or {}
    book_id = data.get('book_id')
    if not book_id:
        return jsonify({'error': {'message': 'book_id is required'}}), 400

    book = Book.query.get_or_404(book_id)

    # 1. Active borrow limit check
    active_borrows = BorrowRecord.query.filter_by(user_id=current_user.id, status='active').count()
    if active_borrows >= current_app.config['MAX_BORROW_LIMIT']:
        return jsonify({'error': {'message': f'Borrow limit reached ({current_app.config["MAX_BORROW_LIMIT"]} books)'}}), 400

    # 2. Check duplicate borrowing
    already_borrowed = BorrowRecord.query.filter_by(user_id=current_user.id, book_id=book_id, status='active').first()
    if already_borrowed:
        return jsonify({'error': {'message': 'You already have an active loan for this book'}}), 400

    # 3. Check copy availability
    if book.available_copies <= 0:
        return jsonify({'error': {'message': 'No copies available. Consider reserving this book.'}}), 409

    book.available_copies -= 1
    due_date = datetime.utcnow() + timedelta(days=current_app.config['DEFAULT_LOAN_DAYS'])
    
    record = BorrowRecord(
        user_id=current_user.id,
        book_id=book.id,
        due_date=due_date,
        status='active'
    )
    db.session.add(record)
    db.session.commit()

    return jsonify({
        'message': 'Book issued successfully',
        'borrow_id': record.id,
        'due_date': due_date.isoformat()
    }), 200


@borrow_bp.route('/return/<int:borrow_id>', methods=['POST'])
@token_required
def return_book(current_user, borrow_id):
    record = BorrowRecord.query.get_or_404(borrow_id)
    
    if current_user.role == 'member' and record.user_id != current_user.id:
        return jsonify({'error': {'message': 'Unauthorized to return this loan'}}), 403

    if record.status == 'returned':
        return jsonify({'error': {'message': 'Book has already been returned'}}), 400

    record.return_date = datetime.utcnow()
    record.status = 'returned'

    # Calculate Fine if overdue
    if record.return_date > record.due_date:
        overdue_days = (record.return_date - record.due_date).days
        if overdue_days > 0:
            record.fine_amount = overdue_days * current_app.config['DAILY_FINE_RATE']

    book = Book.query.get(record.book_id)

    # Check waitlist reservation queue
    next_reservation = Reservation.query.filter_by(book_id=book.id, status='waiting')\
                                         .order_by(Reservation.created_at.asc()).first()

    if next_reservation:
        next_reservation.status = 'fulfilled'
        auto_borrow = BorrowRecord(
            user_id=next_reservation.user_id,
            book_id=book.id,
            due_date=datetime.utcnow() + timedelta(days=current_app.config['DEFAULT_LOAN_DAYS']),
            status='active'
        )
        db.session.add(auto_borrow)
        reservation_msg = f"Book automatically assigned to waiting user ID {next_reservation.user_id}"
    else:
        book.available_copies += 1
        reservation_msg = "Stock replenished"

    db.session.commit()

    return jsonify({
        'message': 'Book returned successfully',
        'fine_amount': record.fine_amount,
        'reservation_update': reservation_msg
    }), 200


@borrow_bp.route('/reserve', methods=['POST'])
@token_required
def reserve_book(current_user):
    data = request.get_json() or {}
    book_id = data.get('book_id')
    book = Book.query.get_or_404(book_id)

    if book.available_copies > 0:
        return jsonify({'message': 'Copies are available directly. No need to join waitlist.'}), 400

    existing = Reservation.query.filter_by(user_id=current_user.id, book_id=book_id, status='waiting').first()
    if existing:
        return jsonify({'message': 'You are already in the queue for this book'}), 409

    res = Reservation(user_id=current_user.id, book_id=book_id)
    db.session.add(res)
    db.session.commit()

    queue_pos = Reservation.query.filter_by(book_id=book_id, status='waiting').count()
    return jsonify({'message': 'Added to waitlist', 'queue_position': queue_pos}), 201