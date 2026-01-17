from flask import Blueprint, request, jsonify
from database import get_db
from datetime import datetime
import os, re, sqlite3
from werkzeug.utils import secure_filename
from config import Config
from routes.ai_bp import clean_text

posts_bp = Blueprint('posts', __name__)


# --- HELPERS ---

def contains_profanity(text):
    """Checks text against the blocked word list from Config."""
    if not text: return False
    bad_words_list = getattr(Config, 'BAD_WORDS', ["fuck", "shit", "damn", "bitch", "idiot"])
    text_lower = text.lower()
    return any(word in text_lower for word in bad_words_list)


def allowed_file(filename):
    """Security check for uploaded file extensions."""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# --- MAIN POST ROUTES ---

# In routes/posts_bp.py

@posts_bp.route('/posts', methods=['GET', 'POST'])
def handle_posts():
    db = get_db()

    # --- 1. GET: Fetch Feed ---
    if request.method == 'GET':
        cat = request.args.get('category', 'all')
        limit = request.args.get('limit', 5, type=int)
        offset = request.args.get('offset', 0, type=int)
        user_ip = request.remote_addr

        query = """
            SELECT p.*, 
            (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comment_count,
            (SELECT COUNT(*) FROM post_likes WHERE post_id = p.id AND ip_address = ?) as user_liked
            FROM posts p 
            WHERE status = 'active'
        """
        params = [user_ip]

        if cat != 'all':
            query += " AND category = ?"
            params.append(cat)

        query += " ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        posts = [dict(row) for row in db.execute(query, params).fetchall()]
        for post in posts:
            post['user_liked'] = bool(post['user_liked'])

        return jsonify(posts)

    # --- 2. POST: Create New Story (Text Only) ---
    if request.method == 'POST':
        # Ensure we interpret JSON correctly
        data = request.get_json(force=True, silent=True) or {}

        title = clean_text(data.get('title'))
        content = clean_text(data.get('content'))

        # SAFETY FIX: Default to 'Social' if category is missing/empty
        category = data.get('category')
        if not category:
            category = 'Social'

        hashtags = clean_text(data.get('hashtags', ''), is_hashtag=True)

        # Basic Validation
        if not title or not content:
            return jsonify({"status": "error", "reason": "Title and Content are required."}), 400

        # Moderation Check
        if contains_profanity(title) or contains_profanity(content) or contains_profanity(hashtags):
            return jsonify({
                "status": "error",
                "reason": "Post rejected: Content contains inappropriate language."
            }), 400

        # Save to DB
        db.execute('''INSERT INTO posts (title, content, category, hashtags, views, likes, status, date, author_ip) 
                     VALUES (?, ?, ?, ?, 0, 0, 'active', ?, ?)''',
                   (title, content, category, hashtags, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    request.remote_addr))
        db.commit()
        return jsonify({"message": "Saved successfully"}), 201

# --- ENGAGEMENT & ANALYTICS ---

@posts_bp.route('/posts/like', methods=['POST'])
def handle_like():
    data = request.json
    post_id = data.get('post_id')
    action = data.get('action')  # 'add' or 'remove'
    user_ip = request.remote_addr

    db = get_db()

    # Check if connection exists
    existing_like = db.execute(
        'SELECT 1 FROM post_likes WHERE post_id = ? AND ip_address = ?',
        (post_id, user_ip)
    ).fetchone()

    if action == 'add':
        if not existing_like:
            db.execute('INSERT INTO post_likes (post_id, ip_address) VALUES (?, ?)', (post_id, user_ip))
            db.execute('UPDATE posts SET likes = likes + 1 WHERE id = ?', (post_id,))

    elif action == 'remove':
        if existing_like:
            db.execute('DELETE FROM post_likes WHERE post_id = ? AND ip_address = ?', (post_id, user_ip))
            db.execute('UPDATE posts SET likes = MAX(0, likes - 1) WHERE id = ?', (post_id,))

    db.commit()
    return jsonify({"status": "success"})


@posts_bp.route('/posts/view', methods=['POST'])
def increment_view():
    data = request.json
    post_id = data.get('post_id')
    ip = request.remote_addr
    db = get_db()
    try:
        with db:
            db.execute('INSERT INTO post_views_log (post_id, ip_address, timestamp) VALUES (?, ?, ?)',
                       (post_id, ip, datetime.now()))
            db.execute('UPDATE posts SET views = views + 1 WHERE id = ?', (post_id,))
        return jsonify({"status": "success"})
    except sqlite3.IntegrityError:
        return jsonify({"status": "already_viewed"})
    except Exception:
        return jsonify({"status": "retry_later"}), 503


@posts_bp.route('/posts/trending', methods=['GET'])
def get_trending():
    db = get_db()
    query = '''
        SELECT p.*, 
        (views + (likes * 5)) as score,
        (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comment_count
        FROM posts p
        WHERE status = 'active'
        ORDER BY score DESC 
        LIMIT 10
    '''
    return jsonify([dict(row) for row in db.execute(query).fetchall()])


# --- COMMENT MANAGEMENT ---

@posts_bp.route('/comments', methods=['GET', 'POST'])
def handle_comments():
    db = get_db()

    if request.method == 'GET':
        post_id = request.args.get('post_id')
        comments = db.execute('SELECT * FROM comments WHERE post_id = ? ORDER BY id ASC', (post_id,)).fetchall()
        return jsonify([dict(row) for row in comments])

    if request.method == 'POST':
        data = request.json
        content = data.get('content', '')
        post_id = data.get('post_id')

        if contains_profanity(content):
            return jsonify({"status": "UNSAFE", "reason": "Profanity detected."}), 400

        db.execute('INSERT INTO comments (post_id, content, date) VALUES (?, ?, ?)',
                   (post_id, content, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        db.commit()
        return jsonify({"status": "SAFE", "message": "Comment added"}), 201


# Add this inside routes/posts_bp.py

@posts_bp.route('/report', methods=['POST'])
def handle_report():
    # 1. Get Data
    data = request.json or {}
    post_id = data.get('post_id')
    reason = data.get('reason')
    user_ip = request.remote_addr

    # 2. Print to Console (Debugging)
    print(f"🚩 Report received for Post {post_id} from {user_ip}")

    # 3. Save directly to DB (Bypassing "Already Reported" check for now)
    db = get_db()
    db.execute(
        'INSERT INTO reports (post_id, reason, date, ip_address) VALUES (?, ?, ?, ?)',
        (post_id, reason, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_ip)
    )
    db.commit()

    return jsonify({"message": "Report submitted successfully."}), 200