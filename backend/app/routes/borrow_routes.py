# Borrow, Return, Reserve waitlist

from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import Book, BorrowRecord, Reservation
from app.utils import token_required, roles_required

borrow_bp = Blueprint('borrow', __name__, url_prefix='/api/v1/borrow')


def _loan_response(record):
    is_overdue = record.status == 'active' and record.due_date < datetime.utcnow()
    return {
        'id': record.id,
        'user_id': record.user_id,
        'book_id': record.book_id,
        'title': record.book.title,
        'borrow_date': record.borrow_date.isoformat(),
        'due_date': record.due_date.isoformat(),
        'return_date': record.return_date.isoformat() if record.return_date else None,
        'status': 'overdue' if is_overdue else record.status,
        'fine_amount': record.fine_amount
    }


@borrow_bp.route('/my-borrows', methods=['GET'])
@token_required
def my_borrows(current_user):
    records = BorrowRecord.query.filter_by(user_id=current_user.id)\
                                .order_by(BorrowRecord.borrow_date.desc()).all()
    return jsonify({'borrows': [_loan_response(record) for record in records]}), 200


@borrow_bp.route('/loans', methods=['GET'])
@token_required
@roles_required('librarian', 'admin')
def list_loans(current_user):
    status = request.args.get('status', 'active').lower()
    if status not in ['active', 'overdue', 'returned', 'all']:
        return jsonify({'error': {'message': 'Invalid status. Pick: active, overdue, returned, all'}}), 400

    query = BorrowRecord.query
    now = datetime.utcnow()
    if status == 'overdue':
        query = query.filter(BorrowRecord.status == 'active', BorrowRecord.due_date < now)
    elif status == 'active':
        query = query.filter(BorrowRecord.status == 'active', BorrowRecord.due_date >= now)
    elif status == 'returned':
        query = query.filter(BorrowRecord.status == 'returned')

    records = query.order_by(BorrowRecord.due_date.asc()).all()
    return jsonify({'loans': [_loan_response(record) for record in records], 'total': len(records)}), 200


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


@borrow_bp.route('/reservations', methods=['GET'])
@token_required
def list_reservations(current_user):
    reservations = Reservation.query.filter_by(user_id=current_user.id)\
                                      .order_by(Reservation.created_at.desc()).all()
    return jsonify({
        'reservations': [{
            'id': reservation.id,
            'book_id': reservation.book_id,
            'title': Book.query.get(reservation.book_id).title,
            'status': reservation.status,
            'created_at': reservation.created_at.isoformat()
        } for reservation in reservations]
    }), 200


@borrow_bp.route('/reserve/<int:reservation_id>', methods=['DELETE'])
@token_required
def cancel_reservation(current_user, reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    if reservation.user_id != current_user.id:
        return jsonify({'error': {'message': 'Unauthorized to cancel this reservation'}}), 403
    if reservation.status != 'waiting':
        return jsonify({'error': {'message': 'Only waiting reservations can be cancelled'}}), 400

    db.session.delete(reservation)
    db.session.commit()
    return jsonify({'message': 'Reservation cancelled successfully', 'reservation_id': reservation_id}), 200
