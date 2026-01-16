import sqlite3
from flask import g

DATABASE = 'blog.db'


# database.py
def get_db():
    if 'db' not in g:
        # Increase timeout to 30s and allow cross-thread access
        g.db = sqlite3.connect('blog.db', timeout=30, check_same_thread=False)
        g.db.row_factory = sqlite3.Row
    return g.db


def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    # Posts: Including Image Support & Status
    c.execute('''CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, content TEXT NOT NULL,
        category TEXT NOT NULL, hashtags TEXT,
        views INTEGER DEFAULT 0, likes INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active', date TEXT NOT NULL,
        author_ip TEXT, image_url TEXT)''')

    # Comments: Now supports reporting
    c.execute('''CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL, content TEXT NOT NULL,
        date TEXT NOT NULL, FOREIGN KEY(post_id) REFERENCES posts(id))''')

    # Reports: Combined Post/Comment reporting
    c.execute('''CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER, comment_id INTEGER,
        reason TEXT NOT NULL, date TEXT NOT NULL)''')

    # Security & Analytics
    c.execute(
        'CREATE TABLE IF NOT EXISTS post_views_log (post_id INTEGER, ip_address TEXT, timestamp DATETIME, PRIMARY KEY (post_id, ip_address))')
    c.execute('CREATE TABLE IF NOT EXISTS blocked_ips (ip_address TEXT PRIMARY KEY, reason TEXT, blocked_at DATETIME)')
    conn.commit()
    conn.close()