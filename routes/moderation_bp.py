from flask import Blueprint, request, jsonify, make_response
from database import get_db
from datetime import datetime
import google.generativeai as genai
import os

moderation_bp = Blueprint('moderation', __name__)

# Fast Keyword Filter
BAD_WORDS = ["fuck", "shit", "damn", "bitch", "fuckoff", "idiot", "stupid"]


def is_text_clean(text):
    """Helper to check for profanity."""
    if not text: return True
    return not any(word in text.lower() for word in BAD_WORDS)


@moderation_bp.route('/report', methods=['POST'])
def handle_report():
    """Logs community reports and auto-flags content."""
    data = request.json
    post_id = str(data.get('post_id'))
    reason = data.get('reason', 'General violation')

    #Cookie Check (Prevents spamming reports)
    cookie_name = f"reported_post_{post_id}"
    if request.cookies.get(cookie_name):
        return jsonify({"message": "You have already reported this post."}), 429

    db = get_db()

    # Log the report in the DB
    db.execute('INSERT INTO reports (post_id, reason, date) VALUES (?, ?, ?)',
               (post_id, reason, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    # Check report threshold (Flag post if >= 3 reports which will then go for admin review)
    report_count = db.execute('SELECT COUNT(*) FROM reports WHERE post_id = ?', (post_id,)).fetchone()[0]

    if report_count >= 3:
        db.execute("UPDATE posts SET status = 'flagged' WHERE id = ?", (post_id,))

    db.commit()

    #  Set cookie to block multiple reports from same user. One report for one post per user
    resp = make_response(jsonify({"message": "Report logged. Admin will review."}))
    resp.set_cookie(cookie_name, 'true', max_age=60 * 60 * 24 * 30)  # 30 days
    return resp