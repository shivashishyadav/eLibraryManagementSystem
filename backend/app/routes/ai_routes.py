"""Routes for AI summaries and cached summary results."""

import hashlib
import requests
from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import Book, BookSummaryCache
from app.utils import token_required

ai_bp = Blueprint('ai', __name__, url_prefix='/api/v1/ai')

def _generate_content_hash(book, style):
    """Create a cache key from the book content and summary style."""
    raw_str = f"{book.id}:{book.title}:{book.description}:{book.content_excerpt}:{style}"
    return hashlib.sha256(raw_str.encode('utf-8')).hexdigest()

@ai_bp.route('/usage', methods=['GET'])
@token_required
def get_ai_usage(current_user):
    url = f"{current_app.config['AI_BASE_URL']}/v1/usage"
    headers = {"Authorization": f"Bearer {current_app.config['AI_API_TOKEN']}"}
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': {'message': f'Upstream AI Service unavailable: {str(e)}'}}), 503


@ai_bp.route('/summarize/<int:book_id>', methods=['POST'])
@token_required
def summarize_book(current_user, book_id):
    book = Book.query.get_or_404(book_id)
    data = request.get_json() or {}
    if not isinstance(data, dict):
        return jsonify({'error': {'message': 'Request body must be a JSON object'}}), 400

    style = data.get('style', 'concise')
    if not isinstance(style, str):
        return jsonify({'error': {'message': 'Invalid style. Pick: concise, detailed, academic, casual'}}), 400
    style = style.lower()

    if style not in ['concise', 'detailed', 'academic', 'casual']:
        return jsonify({'error': {'message': 'Invalid style. Pick: concise, detailed, academic, casual'}}), 400

    # Reuse a summary when the book content has not changed.
    content_hash = _generate_content_hash(book, style)
    cached = BookSummaryCache.query.filter_by(book_id=book.id, style=style, content_hash=content_hash).first()

    if cached:
        return jsonify({
            'book_id': book.id,
            'title': book.title,
            'summary_style': style,
            'summary': cached.summary,
            'cached': True
        }), 200

    prompt = f"""Write a {style} summary for the following book:
Title: {book.title}
Author: {book.author}
Category: {book.category}
Description: {book.description or 'N/A'}
Excerpt: {book.content_excerpt or 'N/A'}
"""

    # Request a new summary only when no matching cache entry exists.
    url = f"{current_app.config['AI_BASE_URL']}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {current_app.config['AI_API_TOKEN']}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": f"You are an expert librarian AI. Provide a high quality {style} summary."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 800,
        "temperature": 0.5
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code != 200:
            return jsonify({'error': response.json()}), response.status_code

        res_data = response.json()
        summary_text = res_data['choices'][0]['message']['content']

        # Save the result for later requests with the same content.
        new_cache = BookSummaryCache(
            book_id=book.id,
            style=style,
            content_hash=content_hash,
            summary=summary_text
        )
        db.session.add(new_cache)
        db.session.commit()

        return jsonify({
            'book_id': book.id,
            'title': book.title,
            'summary_style': style,
            'summary': summary_text,
            'cached': False
        }), 200

    except requests.exceptions.RequestException as e:
        return jsonify({'error': {'message': f'AI Service communication error: {str(e)}'}}), 502
