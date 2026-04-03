# db.py
import sqlite3

DB_NAME = 'pets.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    # пользователи
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            username TEXT,
            first_name TEXT,
            is_banned BOOLEAN DEFAULT 0
        )
    ''')
    # питомцы
    cur.execute('''
        CREATE TABLE IF NOT EXISTS pets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER,
            name TEXT,
            species TEXT,
            avatar_file_id TEXT
        )
    ''')
    # посты
    cur.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author_id INTEGER,
            pet_id INTEGER,
            file_id TEXT,
            file_type TEXT,
            caption TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # подписки
    cur.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            subscriber_id INTEGER,
            author_id INTEGER,
            UNIQUE(subscriber_id, author_id)
        )
    ''')
    # лайки
    cur.execute('''
        CREATE TABLE IF NOT EXISTS likes (
            user_id INTEGER,
            post_id INTEGER,
            UNIQUE(user_id, post_id)
        )
    ''')
    # комментарии
    cur.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            post_id INTEGER,
            text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# ---- пользователи ----
def register_user(telegram_id, username, first_name):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('INSERT OR IGNORE INTO users (telegram_id, username, first_name) VALUES (?, ?, ?)',
                (telegram_id, username, first_name))
    conn.commit()
    conn.close()

def get_user_by_telegram(telegram_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id, telegram_id, username, first_name, is_banned FROM users WHERE telegram_id = ?', (telegram_id,))
    user = cur.fetchone()
    conn.close()
    return user

def ban_user(telegram_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('UPDATE users SET is_banned = 1 WHERE telegram_id = ?', (telegram_id,))
    conn.commit()
    conn.close()

def unban_user(telegram_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('UPDATE users SET is_banned = 0 WHERE telegram_id = ?', (telegram_id,))
    conn.commit()
    conn.close()

# ---- питомцы ----
def add_pet(telegram_id, name, species, file_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
    user = cur.fetchone()
    if user:
        cur.execute('INSERT INTO pets (owner_id, name, species, avatar_file_id) VALUES (?, ?, ?, ?)',
                    (user[0], name, species, file_id))
        conn.commit()
        pet_id = cur.lastrowid
        conn.close()
        return pet_id
    conn.close()
    return None

def get_user_pets(telegram_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        SELECT pets.id, pets.name, pets.species 
        FROM pets JOIN users ON pets.owner_id = users.id
        WHERE users.telegram_id = ?
    ''', (telegram_id,))
    pets = cur.fetchall()
    conn.close()
    return pets

# ---- посты ----
def create_post(telegram_id, pet_id, file_id, file_type, caption):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
    user = cur.fetchone()
    if user:
        cur.execute('INSERT INTO posts (author_id, pet_id, file_id, file_type, caption) VALUES (?, ?, ?, ?, ?)',
                    (user[0], pet_id, file_id, file_type, caption))
        conn.commit()
        post_id = cur.lastrowid
        conn.close()
        return post_id
    conn.close()
    return None

def delete_post(post_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    conn.commit()
    conn.close()

def get_feed(telegram_id, limit=10):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        SELECT posts.id, posts.file_id, posts.file_type, posts.caption, posts.created_at,
               users.username, pets.name as pet_name, posts.author_id
        FROM posts
        JOIN users ON posts.author_id = users.id
        LEFT JOIN pets ON posts.pet_id = pets.id
        WHERE posts.author_id IN (
            SELECT author_id FROM subscriptions 
            WHERE subscriber_id = (SELECT id FROM users WHERE telegram_id = ?)
        ) AND users.is_banned = 0
        ORDER BY posts.created_at DESC
        LIMIT ?
    ''', (telegram_id, limit))
    feed = cur.fetchall()
    conn.close()
    return feed

def get_all_posts_for_moderation(limit=50):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        SELECT posts.id, posts.file_id, posts.file_type, posts.caption, posts.created_at,
               users.username, users.telegram_id
        FROM posts
        JOIN users ON posts.author_id = users.id
        ORDER BY posts.created_at DESC
        LIMIT ?
    ''', (limit,))
    posts = cur.fetchall()
    conn.close()
    return posts

# ---- подписки ----
def follow(subscriber_telegram, author_telegram):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id FROM users WHERE telegram_id = ?', (subscriber_telegram,))
    sub = cur.fetchone()
    cur.execute('SELECT id FROM users WHERE telegram_id = ?', (author_telegram,))
    auth = cur.fetchone()
    if sub and auth:
        cur.execute('INSERT OR IGNORE INTO subscriptions (subscriber_id, author_id) VALUES (?, ?)',
                    (sub[0], auth[0]))
        conn.commit()
    conn.close()

def unfollow(subscriber_telegram, author_telegram):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id FROM users WHERE telegram_id = ?', (subscriber_telegram,))
    sub = cur.fetchone()
    cur.execute('SELECT id FROM users WHERE telegram_id = ?', (author_telegram,))
    auth = cur.fetchone()
    if sub and auth:
        cur.execute('DELETE FROM subscriptions WHERE subscriber_id = ? AND author_id = ?', (sub[0], auth[0]))
        conn.commit()
    conn.close()

# ---- лайки ----
def like_post(telegram_id, post_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
    user = cur.fetchone()
    if user:
        cur.execute('INSERT OR IGNORE INTO likes (user_id, post_id) VALUES (?, ?)', (user[0], post_id))
        conn.commit()
    conn.close()

def unlike_post(telegram_id, post_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
    user = cur.fetchone()
    if user:
        cur.execute('DELETE FROM likes WHERE user_id = ? AND post_id = ?', (user[0], post_id))
        conn.commit()
    conn.close()

def get_likes_count(post_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM likes WHERE post_id = ?', (post_id,))
    count = cur.fetchone()[0]
    conn.close()
    return count

# ---- комментарии ----
def add_comment(telegram_id, post_id, text):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
    user = cur.fetchone()
    if user:
        cur.execute('INSERT INTO comments (user_id, post_id, text) VALUES (?, ?, ?)', (user[0], post_id, text))
        conn.commit()
    conn.close()

def get_comments(post_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        SELECT comments.text, users.username, comments.created_at
        FROM comments JOIN users ON comments.user_id = users.id
        WHERE post_id = ?
        ORDER BY comments.created_at DESC
    ''', (post_id,))
    comments = cur.fetchall()
    conn.close()
    return comments

# ---- исправленная регистрация с автоподпиской ----
def register_user(telegram_id, username, first_name):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('INSERT OR IGNORE INTO users (telegram_id, username, first_name) VALUES (?, ?, ?)',
                (telegram_id, username, first_name))
    conn.commit()
    # автоподписка на себя
    cur.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
    user_id = cur.fetchone()
    if user_id:
        cur.execute('INSERT OR IGNORE INTO subscriptions (subscriber_id, author_id) VALUES (?, ?)', 
                    (user_id[0], user_id[0]))
        conn.commit()
    conn.close()

# ---- получить посты пользователя для профиля ----
def get_user_posts(telegram_id, limit=10):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        SELECT posts.id, posts.file_id, posts.file_type, posts.caption, posts.created_at,
               pets.name as pet_name
        FROM posts
        JOIN users ON posts.author_id = users.id
        LEFT JOIN pets ON posts.pet_id = pets.id
        WHERE users.telegram_id = ?
        ORDER BY posts.created_at DESC
        LIMIT ?
    ''', (telegram_id, limit))
    posts = cur.fetchall()
    conn.close()
    return posts

# ---- удалить пост (для админа) ----
def delete_post(post_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    cur.execute('DELETE FROM likes WHERE post_id = ?', (post_id,))
    cur.execute('DELETE FROM comments WHERE post_id = ?', (post_id,))
    conn.commit()
    conn.close()

# ---- получить количество лайков ----
def get_likes_count(post_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM likes WHERE post_id = ?', (post_id,))
    count = cur.fetchone()[0]
    conn.close()
    return count

# ---- получить комментарии к посту ----
def get_comments(post_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        SELECT comments.text, users.username 
        FROM comments JOIN users ON comments.user_id = users.id 
        WHERE post_id = ? 
        ORDER BY created_at DESC
    ''', (post_id,))
    comments = cur.fetchall()
    conn.close()
    return comments