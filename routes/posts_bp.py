from flask import Blueprint, request, jsonify
from database import get_db
from datetime import datetime
import os, re, sqlite3
from werkzeug.utils import secure_filename
from config import Config  # We need this for the bad words list
# Importing the cleaning logic from ai_bp to keep things DRY (Don't Repeat Yourself)
from routes.ai_bp import clean_text

posts_bp = Blueprint('posts', __name__)


# --- HELPER FUNCTIONS ---

def contains_profanity(text):
    """
    Quick safety check. Scans text against our blocked word list.
    Returns True if any bad words are found.
    """
    if not text: return False

    # Grab the list from Config, or fall back to a safe default if something breaks
    bad_words_list = getattr(Config, 'BAD_WORDS', ["fuck", "shit", "damn", "bitch", "idiot"])

    text_lower = text.lower()
    # Simple substring check - effectively blocks 'badword' inside 'notabadword',
    # but good enough for a basic filter.
    return any(word in text_lower for word in bad_words_list)


def allowed_file(filename):
    """
    Security check: Only allow safe image formats.
    Prevents users from uploading .exe or .php files.
    """
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    # Splits the filename at the last dot to check the extension
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# --- MAIN POST ROUTES ---

@posts_bp.route('/posts', methods=['GET', 'POST'])
def handle_posts():
    db = get_db()

    # 1. FETCHING POSTS (Feed Logic)
    if request.method == 'GET':
        cat = request.args.get('category', 'all')

        # We need a subquery here to get the real-time comment count for each post
        # without doing a separate API call for every single card in the feed.
        query = """
            SELECT p.*, (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comment_count 
            FROM posts p 
            WHERE status = 'active'
        """
        params = []

        # Filter by category if the user clicked a specific tab
        if cat != 'all':
            query += " AND category = ?"
            params.append(cat)

        query += " ORDER BY id DESC"  # Newest posts first
        return jsonify([dict(row) for row in db.execute(query, params).fetchall()])

    # 2. CREATING A POST
    if request.method == 'POST':
        # Sanitize text inputs immediately to strip dangerous HTML tags
        title = clean_text(request.form.get('title'))
        # Note: 'content' might contain <b> or <i> tags from the WYSIWYG editor,
        # so make sure clean_text allows those specific tags.
        content = clean_text(request.form.get('content'))
        category = request.form.get('category')
        hashtags = clean_text(request.form.get('hashtags', ''), is_hashtag=True)

        # MODERATION GATEKEEPER
        # If they use bad language, reject it before it ever touches the DB.
        if contains_profanity(title) or contains_profanity(content) or contains_profanity(hashtags):
            return jsonify({
                "status": "error",
                "reason": "Post rejected: Content contains inappropriate language."
            }), 400

        # Handle Image Upload
        file = request.files.get('image')
        img_url = None

        if file and file.filename != '':
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Ensure the folder exists so we don't crash on first run
                os.makedirs('static/uploads', exist_ok=True)
                file.save(os.path.join('static/uploads', filename))
                img_url = f'/static/uploads/{filename}'
            else:
                return jsonify({"status": "error", "reason": "Invalid file type (Images only)"}), 400

        # Save to Database
        # We log the author_ip to help with banning users later if needed.
        db.execute('''INSERT INTO posts (title, content, category, hashtags, views, likes, status, date, author_ip, image_url) 
                     VALUES (?, ?, ?, ?, 0, 0, 'active', ?, ?, ?)''',
                   (title, content, category, hashtags, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    request.remote_addr, img_url))
        db.commit()
        return jsonify({"message": "Saved successfully"}), 201


# --- ENGAGEMENT & ANALYTICS ---

@posts_bp.route('/posts/like', methods=['POST'])
def handle_like():
    """Simple toggle for likes. No user auth, so it's just a counter."""
    data = request.json
    post_id = data.get('post_id')
    action = data.get('action')  # 'add' or 'remove'

    db = get_db()
    if action == 'add':
        db.execute('UPDATE posts SET likes = likes + 1 WHERE id = ?', (post_id,))
    else:
        # Prevent likes from going below zero
        db.execute('UPDATE posts SET likes = MAX(0, likes - 1) WHERE id = ?', (post_id,))
    db.commit()
    return jsonify({"status": "success"})


@posts_bp.route('/posts/view', methods=['POST'])
def increment_view():
    """
    Tracks views. We use a separate log table to prevent race conditions
    and ensure unique views per session if we want to filter later.
    """
    data = request.json
    post_id = data.get('post_id')
    ip = request.remote_addr
    db = get_db()
    try:
        with db:  # Context manager automatically handles transactions
            db.execute('INSERT INTO post_views_log (post_id, ip_address, timestamp) VALUES (?, ?, ?)',
                       (post_id, ip, datetime.now()))
            db.execute('UPDATE posts SET views = views + 1 WHERE id = ?', (post_id,))
        return jsonify({"status": "success"})
    except sqlite3.IntegrityError:
        # This IP has already viewed this post, so we ignore it
        return jsonify({"status": "already_viewed"})
    except Exception:
        return jsonify({"status": "retry_later"}), 503


@posts_bp.route('/posts/trending', methods=['GET'])
def get_trending():
    """
    Calculates a 'Trending Score'.
    Formula: Views + (Likes * 5). Likes are weighted heavier than views.
    """
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

        # Safety: Check comments for bad words too
        if contains_profanity(content):
            return jsonify({
                "status": "UNSAFE",
                "reason": "Profanity detected."
            }), 400

        db.execute('INSERT INTO comments (post_id, content, date) VALUES (?, ?, ?)',
                   (post_id, content, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        db.commit()
        return jsonify({"status": "SAFE", "message": "Comment added"}), 201