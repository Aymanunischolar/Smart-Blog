from flask import Blueprint, request, jsonify, render_template
from database import get_db
from datetime import datetime, timedelta
import sqlite3

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin')
def admin_panel():
    """Renders the main administrative dashboard view."""
    return render_template('admin.html')


# --- STATS & METRICS ---
@admin_bp.route('/api/admin/stats')
def get_admin_stats():
    db = get_db()
    stats = {
        "total_posts": db.execute('SELECT COUNT(*) FROM posts').fetchone()[0],
        "total_reports": db.execute('SELECT COUNT(*) FROM reports').fetchone()[0],
        "blocked_ips": db.execute('SELECT COUNT(*) FROM blocked_ips').fetchone()[0],
        "total_views": db.execute('SELECT SUM(views) FROM posts').fetchone()[0] or 0
    }
    return jsonify(stats)


# --- DATA FETCHING ROUTES ---

@admin_bp.route('/api/admin/reports')
def get_admin_reports():
    """Retrieves reports, now including the Author IP for banning purposes."""
    db = get_db()
    query = '''
        SELECT r.id, r.post_id, r.comment_id, r.reason, r.date, 
               p.title as post_title, p.author_ip 
        FROM reports r
        LEFT JOIN posts p ON r.post_id = p.id
        ORDER BY r.id DESC
    '''
    reports = [dict(row) for row in db.execute(query).fetchall()]
    return jsonify(reports)


@admin_bp.route('/api/admin/posts')
def get_all_posts():
    """Fetches the 50 most recent posts for general management."""
    db = get_db()
    # We fetch ID, Title, Status, Date, and Author IP
    posts = [dict(row) for row in db.execute(
        "SELECT id, title, status, date, author_ip, views FROM posts ORDER BY id DESC LIMIT 50"
    ).fetchall()]
    return jsonify(posts)


@admin_bp.route('/api/admin/banned')
def get_banned_ips():
    """Lists all currently banned IPs."""
    db = get_db()
    ips = [dict(row) for row in db.execute("SELECT * FROM blocked_ips ORDER BY blocked_at DESC").fetchall()]
    return jsonify(ips)


@admin_bp.route('/api/admin/flagged')
def get_flagged_posts():
    """Lists all currently flagged posts"""
    db = get_db()
    flagged = [dict(row) for row in db.execute(
        "SELECT * FROM posts WHERE status = 'flagged' ORDER BY id DESC"
    ).fetchall()]
    return jsonify(flagged)


# --- ACTION ROUTES ---

@admin_bp.route('/api/admin/ban', methods=['POST'])
def ban_ip():
    """Bans an IP address for 24 hours."""
    data = request.json
    ip = data.get('ip')
    reason = data.get('reason', 'Admin Ban')

    if not ip:
        return jsonify({"error": "No IP provided"}), 400

    db = get_db()
    try:
        #Calculates the time that the ip was blocked to implement logic
        blocked_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        db.execute('INSERT OR REPLACE INTO blocked_ips (ip_address, reason, blocked_at) VALUES (?, ?, ?)',
                   (ip, reason, blocked_at))
        db.commit()
        return jsonify({"message": f"IP {ip} has been banned."})
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route('/api/admin/unblock', methods=['POST'])
def unblock_ip():
    """Removes an IP from the banned list."""
    data = request.json
    ip = data.get('ip_address')

    db = get_db()
    db.execute('DELETE FROM blocked_ips WHERE ip_address = ?', (ip,))
    db.commit()
    return jsonify({"message": f"IP {ip} unblocked"})


@admin_bp.route('/api/admin/moderate', methods=['POST'])
def moderate_content():
    """Updates post status (active/deleted) or deletes completely."""
    data = request.json
    post_id = data.get('post_id')
    new_status = data.get('status')

    db = get_db()

    if new_status == 'hard_delete':
        # Completely remove from DB
        db.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        db.execute("DELETE FROM comments WHERE post_id = ?", (post_id,))
        db.execute("DELETE FROM reports WHERE post_id = ?", (post_id,))
    else:
        # Soft delete / restore
        db.execute("UPDATE posts SET status = ? WHERE id = ?", (new_status, post_id))
        if new_status == 'deleted':
            db.execute("DELETE FROM reports WHERE post_id = ?", (post_id,))

    db.commit()
    return jsonify({"message": "Content updated"})