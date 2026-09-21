import sqlite3

DB_NAME = "shop.db"

# أسعار التحويل التقريبية (يمكنك تعديلها حسب سعر السوق)
EGP_TO_USD = 0.021  # سعر تحويل الجنيه إلى دولار
EGP_TO_IQD = 28.0   # سعر تحويل الجنيه إلى دينار عراقي

def get_db():
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                details TEXT NOT NULL,
                price_egp REAL NOT NULL DEFAULT 0,
                credentials TEXT NOT NULL,
                image_path TEXT DEFAULT NULL,
                status TEXT DEFAULT 'available',
                reserved_by INTEGER DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                name TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_methods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                method_type TEXT NOT NULL,
                provider_title TEXT NOT NULL,
                details TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT DEFAULT NULL,
                full_name TEXT DEFAULT NULL,
                account_id INTEGER NOT NULL,
                payment_method TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts (id)
            )
        ''')
        # إضافة الأعمدة الجديدة إن لم تكن موجودة (للمشاريع القديمة)
        try:
            cursor.execute("ALTER TABLE orders ADD COLUMN username TEXT DEFAULT NULL")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE orders ADD COLUMN full_name TEXT DEFAULT NULL")
        except Exception:
            pass
        conn.commit()

# --- Admin Operations ---
def add_admin(telegram_id, name):
    with get_db() as conn:
        conn.cursor().execute("INSERT OR IGNORE INTO admins (telegram_id, name) VALUES (?, ?)", (telegram_id, name))
        conn.commit()

def get_admins():
    with get_db() as conn:
        return [dict(row) for row in conn.cursor().execute("SELECT * FROM admins").fetchall()]

def delete_admin(admin_id):
    with get_db() as conn:
        conn.cursor().execute("DELETE FROM admins WHERE id = ?", (admin_id,))
        conn.commit()

def get_admin_telegram_ids():
    with get_db() as conn:
        rows = conn.cursor().execute("SELECT telegram_id FROM admins").fetchall()
        return [row['telegram_id'] for row in rows]

# --- Payment Operations ---
def add_payment_method(method_type, provider_title, details):
    with get_db() as conn:
        conn.cursor().execute(
            "INSERT INTO payment_methods (method_type, provider_title, details) VALUES (?, ?, ?)",
            (method_type, provider_title, details)
        )
        conn.commit()

def get_payment_methods_by_type(method_type):
    with get_db() as conn:
        return [dict(row) for row in conn.cursor().execute("SELECT * FROM payment_methods WHERE method_type = ?", (method_type,)).fetchall()]

def get_all_payment_methods():
    with get_db() as conn:
        return [dict(row) for row in conn.cursor().execute("SELECT * FROM payment_methods").fetchall()]

def delete_payment_method(pm_id):
    with get_db() as conn:
        conn.cursor().execute("DELETE FROM payment_methods WHERE id = ?", (pm_id,))
        conn.commit()

# --- Accounts & Stats ---
def add_account(title, details, price_egp, credentials, image_path=None):
    with get_db() as conn:
        conn.cursor().execute(
            "INSERT INTO accounts (title, details, price_egp, credentials, image_path) VALUES (?, ?, ?, ?, ?)",
            (title, details, price_egp, credentials, image_path)
        )
        conn.commit()

def get_all_accounts():
    with get_db() as conn:
        return [dict(row) for row in conn.cursor().execute("SELECT * FROM accounts ORDER BY id DESC").fetchall()]

def get_available_accounts():
    with get_db() as conn:
        return [dict(row) for row in conn.cursor().execute("SELECT * FROM accounts WHERE status = 'available' ORDER BY id DESC").fetchall()]

def delete_account(account_id):
    with get_db() as conn:
        conn.cursor().execute("DELETE FROM accounts WHERE id = ?", (account_id,))
        conn.commit()

def reserve_account(account_id, user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        row = cursor.execute(
            "SELECT status FROM accounts WHERE id = ?", (account_id,)
        ).fetchone()
        if not row or row['status'] != 'available':
            return False
        cursor.execute(
            "UPDATE accounts SET status = 'reserved', reserved_by = ? WHERE id = ? AND status = 'available'",
            (user_id, account_id)
        )
        conn.commit()
        return cursor.rowcount > 0

def get_stats():
    with get_db() as conn:
        cursor = conn.cursor()
        total = cursor.execute("SELECT COUNT(*) FROM accounts").fetchone()[0] or 0
        available = cursor.execute("SELECT COUNT(*) FROM accounts WHERE status = 'available'").fetchone()[0] or 0
        sold = cursor.execute("SELECT COUNT(*) FROM accounts WHERE status = 'sold'").fetchone()[0] or 0
        pending_orders = cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending'").fetchone()[0] or 0
        revenue_egp = cursor.execute("SELECT SUM(price_egp) FROM accounts WHERE status = 'sold'").fetchone()[0] or 0

        revenue_usd = round(revenue_egp * EGP_TO_USD, 2)
        revenue_iqd = int(revenue_egp * EGP_TO_IQD)

        return {
            "total": total,
            "available": available,
            "sold": sold,
            "pending_orders": pending_orders,
            "revenue_egp": revenue_egp,
            "revenue_usd": revenue_usd,
            "revenue_iqd": revenue_iqd
        }

# --- Orders ---
def create_order(user_id, account_id, payment_method, username=None, full_name=None):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO orders (user_id, account_id, payment_method, username, full_name) VALUES (?, ?, ?, ?, ?)",
            (user_id, account_id, payment_method, username, full_name)
        )
        conn.commit()
        return cursor.lastrowid

def get_all_orders():
    with get_db() as conn:
        rows = conn.cursor().execute("""
            SELECT o.*, a.title as account_title, a.price_egp
            FROM orders o
            LEFT JOIN accounts a ON o.account_id = a.id
            ORDER BY o.id DESC
        """).fetchall()
        return [dict(row) for row in rows]

def get_orders_by_user(user_id):
    with get_db() as conn:
        rows = conn.cursor().execute("""
            SELECT o.*, a.title as account_title, a.price_egp
            FROM orders o
            LEFT JOIN accounts a ON o.account_id = a.id
            WHERE o.user_id = ?
            ORDER BY o.id DESC
        """, (user_id,)).fetchall()
        return [dict(row) for row in rows]

def process_order(order_id, approve=True):
    """
    معالجة الطلب: موافقة أو رفض.
    Returns: (user_id, credentials) عند الموافقة، أو (user_id, None) عند الرفض
    """
    with get_db() as conn:
        cursor = conn.cursor()
        order = cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not order:
            return None, None

        user_id = order['user_id']
        account_id = order['account_id']

        if approve:
            account = cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
            credentials = account['credentials'] if account else None
            cursor.execute("UPDATE orders SET status = 'approved' WHERE id = ?", (order_id,))
            cursor.execute("UPDATE accounts SET status = 'sold' WHERE id = ?", (account_id,))
            conn.commit()
            return user_id, credentials
        else:
            cursor.execute("UPDATE orders SET status = 'rejected' WHERE id = ?", (order_id,))
            cursor.execute("UPDATE accounts SET status = 'available', reserved_by = NULL WHERE id = ?", (account_id,))
            conn.commit()
            return user_id, None