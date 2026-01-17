import sqlite3
from flask import g

DATABASE = 'blog.db'


def get_db():
    """
    Opens a new database connection if there is none yet for the
    current application context.
    """
    if 'db' not in g:
        # Increase timeout to 30s to prevent 'Database is locked' errors under load
        # check_same_thread=False allows sharing connection across threads (careful with writes!)
        g.db = sqlite3.connect(DATABASE, timeout=30, check_same_thread=False)
        g.db.row_factory = sqlite3.Row
    return g.db


def init_db():
    """
    Initializes the database with the required schema.
    Run this once (or on app startup) to ensure tables exist.
    """
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # 1. POSTS TABLE
    # Stores the main blog content, including image URLs and metadata.
    c.execute('''CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, 
        content TEXT NOT NULL,
        category TEXT NOT NULL, 
        hashtags TEXT,
        views INTEGER DEFAULT 0, 
        likes INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active', 
        date TEXT NOT NULL,
        author_ip TEXT
    )''')

    # 2. COMMENTS TABLE
    # Stores user discussions linked to specific posts.
    c.execute('''CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL, 
        content TEXT NOT NULL,
        date TEXT NOT NULL, 
        FOREIGN KEY(post_id) REFERENCES posts(id)
    )''')

    # 3. LIKES TRACKING TABLE (NEW)
    # Prevents duplicate likes by tracking (Post + IP Address) pairs.
    c.execute('''CREATE TABLE IF NOT EXISTS post_likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        ip_address TEXT NOT NULL,
        FOREIGN KEY(post_id) REFERENCES posts(id)
    )''')

    # 4. REPORTS TABLE
    # Used for community moderation.
    c.execute('''CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER, 
            comment_id INTEGER,
            reason TEXT NOT NULL, 
            date TEXT NOT NULL,
            ip_address TEXT
        )''')

    # 5. ANALYTICS & SECURITY TABLES
    # post_views_log: Ensures we count only 1 view per IP per session (primary key constraint).
    c.execute('''CREATE TABLE IF NOT EXISTS post_views_log (
        post_id INTEGER, 
        ip_address TEXT, 
        timestamp DATETIME, 
        PRIMARY KEY (post_id, ip_address)
    )''')

    # blocked_ips: For banning abusive users.
    c.execute('''CREATE TABLE IF NOT EXISTS blocked_ips (
        ip_address TEXT PRIMARY KEY, 
        reason TEXT, 
        blocked_at DATETIME
    )''')

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully.")


# Allow running this file directly to reset/init DB: `python database.py`
