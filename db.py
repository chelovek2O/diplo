# db.py
import sqlite3
from datetime import datetime, timedelta

DB_NAME = 'pets.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            username TEXT,
            first_name TEXT,
            banned_until TIMESTAMP
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS pets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER,
            name TEXT,
            species TEXT,
            avatar_file_id TEXT
        )
    ''')
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
    cur.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            subscriber_id INTEGER,
            author_id INTEGER,
            UNIQUE(subscriber_id, author_id)
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS likes (
            user_id INTEGER,
            post_id INTEGER,
            UNIQUE(user_id, post_id)
        )
    ''')
    cur.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cur.fetchall()]
    if 'banned_until' not in columns:
        cur.execute("ALTER TABLE users ADD COLUMN banned_until TIMESTAMP")
    conn.commit()
    conn.close()


# ----- users -----
def get_user(telegram_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id, telegram_id, username, first_name, banned_until FROM users WHERE telegram_id = ?', (telegram_id,))
    user = cur.fetchone()
    conn.close()
    return user


def get_user_by_username(username):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT telegram_id, username, first_name FROM users WHERE username = ?', (username,))
    user = cur.fetchone()
    conn.close()
    return user


def register_user(telegram_id, username, first_name):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('INSERT OR IGNORE INTO users (telegram_id, username, first_name, banned_until) VALUES (?, ?, ?, NULL)',
                (telegram_id, username, first_name))
    conn.commit()
    # АВТОПОДПИСКА НА СЕБЯ
    cur.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
    user_id = cur.fetchone()
    if user_id:
        cur.execute('INSERT OR IGNORE INTO subscriptions (subscriber_id, author_id) VALUES (?, ?)',
                    (user_id[0], user_id[0]))
        conn.commit()
    conn.close()


def is_user_banned(telegram_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT banned_until FROM users WHERE telegram_id = ?', (telegram_id,))
    row = cur.fetchone()
    conn.close()
    if row and row[0]:
        ban_time = datetime.fromisoformat(row[0])
        if ban_time > datetime.now():
            return True
    return False


def ban_user(telegram_id, hours=24):
    until = datetime.now() + timedelta(hours=hours)
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('UPDATE users SET banned_until = ? WHERE telegram_id = ?', (until.isoformat(), telegram_id))
    conn.commit()
    conn.close()


def unban_user(telegram_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('UPDATE users SET banned_until = NULL WHERE telegram_id = ?', (telegram_id,))
    conn.commit()
    conn.close()


# ----- pets -----
def get_user_pets(telegram_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        SELECT pets.id, pets.name, pets.species, pets.avatar_file_id 
        FROM pets JOIN users ON pets.owner_id = users.id 
        WHERE users.telegram_id = ?
    ''', (telegram_id,))
    pets = cur.fetchall()
    conn.close()
    return pets


def add_pet(telegram_id, name, species, file_id=None):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
    user = cur.fetchone()
    if user:
        cur.execute('INSERT INTO pets (owner_id, name, species, avatar_file_id) VALUES (?, ?, ?, ?)',
                    (user[0], name, species, file_id))
        conn.commit()
    conn.close()


def delete_pet(pet_id, telegram_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        DELETE FROM pets WHERE id = ? AND owner_id = (SELECT id FROM users WHERE telegram_id = ?)
    ''', (pet_id, telegram_id))
    conn.commit()
    cur.execute('DELETE FROM posts WHERE pet_id = ?', (pet_id,))
    conn.commit()
    conn.close()


# ----- posts -----
def create_post(telegram_id, pet_id, file_id, file_type, caption):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
    user = cur.fetchone()
    if user:
        cur.execute('INSERT INTO posts (author_id, pet_id, file_id, file_type, caption) VALUES (?, ?, ?, ?, ?)',
                    (user[0], pet_id, file_id, file_type, caption))
        conn.commit()
    conn.close()


def get_post_by_index(telegram_id, index):
    """Возвращает пост по индексу из ленты (включая свои посты)"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    # Получаем список авторов, на которых подписан пользователь (включая себя)
    cur.execute('''
        SELECT author_id FROM subscriptions 
        WHERE subscriber_id = (SELECT id FROM users WHERE telegram_id = ?)
    ''', (telegram_id,))
    author_ids = [row[0] for row in cur.fetchall()]
    if not author_ids:
        conn.close()
        return None, 0
    placeholders = ','.join('?' for _ in author_ids)
    cur.execute(f'''
        SELECT posts.id, posts.file_id, posts.file_type, posts.caption, posts.created_at,
               users.username, users.telegram_id as author_telegram_id,
               pets.name as pet_name
        FROM posts
        JOIN users ON posts.author_id = users.id
        LEFT JOIN pets ON posts.pet_id = pets.id
        WHERE posts.author_id IN ({placeholders})
        ORDER BY posts.created_at DESC
    ''', author_ids)
    all_posts = cur.fetchall()
    conn.close()
    if 0 <= index < len(all_posts):
        return all_posts[index], len(all_posts)
    return None, 0


def get_user_posts(telegram_id, limit=10):
    """Получить все посты пользователя (для профиля)"""
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


def get_posts_by_pet(telegram_id, pet_id):
    """Получить все посты конкретного питомца пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        SELECT posts.id, posts.file_id, posts.file_type, posts.caption, posts.created_at,
               pets.name as pet_name
        FROM posts
        JOIN pets ON posts.pet_id = pets.id
        JOIN users ON posts.author_id = users.id
        WHERE users.telegram_id = ? AND pets.id = ?
        ORDER BY posts.created_at DESC
    ''', (telegram_id, pet_id))
    posts = cur.fetchall()
    conn.close()
    return posts


def get_posts_by_user(telegram_id):
    """Получить все посты пользователя (для админ-панели)"""
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
    ''', (telegram_id,))
    posts = cur.fetchall()
    conn.close()
    return posts


def delete_post(post_id, user_telegram_id=None, is_admin=False):
    """Удалить пост. Если is_admin=False, проверяем, что пост принадлежит пользователю"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    if is_admin:
        cur.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    else:
        cur.execute('''
            DELETE FROM posts WHERE id = ? AND author_id = (SELECT id FROM users WHERE telegram_id = ?)
        ''', (post_id, user_telegram_id))
    conn.commit()
    cur.execute('DELETE FROM likes WHERE post_id = ?', (post_id,))
    conn.commit()
    conn.close()


# ----- likes -----
def like_post(user_telegram, post_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id FROM users WHERE telegram_id = ?', (user_telegram,))
    user = cur.fetchone()
    if user:
        cur.execute('INSERT OR IGNORE INTO likes (user_id, post_id) VALUES (?, ?)', (user[0], post_id))
        conn.commit()
    conn.close()


def get_likes_count(post_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM likes WHERE post_id = ?', (post_id,))
    count = cur.fetchone()[0]
    conn.close()
    return count


# ----- subscriptions -----
def get_user_subscriptions(telegram_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        SELECT users.telegram_id, users.username, users.first_name
        FROM subscriptions
        JOIN users ON subscriptions.author_id = users.id
        WHERE subscriptions.subscriber_id = (SELECT id FROM users WHERE telegram_id = ?)
    ''', (telegram_id,))
    subs = cur.fetchall()
    conn.close()
    return subs


def is_subscribed(subscriber_telegram, author_telegram):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        SELECT 1 FROM subscriptions
        WHERE subscriber_id = (SELECT id FROM users WHERE telegram_id = ?)
        AND author_id = (SELECT id FROM users WHERE telegram_id = ?)
    ''', (subscriber_telegram, author_telegram))
    row = cur.fetchone()
    conn.close()
    return row is not None


def add_subscription(subscriber_telegram, author_telegram):
    if subscriber_telegram == author_telegram:
        return False
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    try:
        cur.execute('''
            INSERT OR IGNORE INTO subscriptions (subscriber_id, author_id)
            VALUES ((SELECT id FROM users WHERE telegram_id = ?), (SELECT id FROM users WHERE telegram_id = ?))
        ''', (subscriber_telegram, author_telegram))
        conn.commit()
        success = cur.rowcount > 0
    except:
        success = False
    conn.close()
    return success


def remove_subscription(subscriber_telegram, author_telegram):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        DELETE FROM subscriptions
        WHERE subscriber_id = (SELECT id FROM users WHERE telegram_id = ?)
        AND author_id = (SELECT id FROM users WHERE telegram_id = ?)
    ''', (subscriber_telegram, author_telegram))
    conn.commit()
    conn.close()