import sqlite3

DB_NAME = "shop.db"

# أسعار التحويل التقريبية
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
            CREATE TABLE IF NOT EXISTS coins_packages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                coins_amount INTEGER NOT NULL,
                price_egp REAL NOT NULL DEFAULT 0,
                description TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT DEFAULT NULL,
                full_name TEXT DEFAULT NULL,
                account_id INTEGER DEFAULT NULL,
                package_id INTEGER DEFAULT NULL,
                order_type TEXT DEFAULT 'account',
                custom_info TEXT DEFAULT NULL,
                payment_method TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts (id)
            )
        ''')
        # ترقية الجداول القديمة بإضافة الأعمدة الجديدة إن لم تكن موجودة
        existing_order_cols = [row['name'] for row in cursor.execute("PRAGMA table_info(orders)").fetchall()]
        if 'username' not in existing_order_cols:
            try: cursor.execute("ALTER TABLE orders ADD COLUMN username TEXT DEFAULT NULL")
            except Exception: pass
        if 'full_name' not in existing_order_cols:
            try: cursor.execute("ALTER TABLE orders ADD COLUMN full_name TEXT DEFAULT NULL")
            except Exception: pass
        if 'package_id' not in existing_order_cols:
            try: cursor.execute("ALTER TABLE orders ADD COLUMN package_id INTEGER DEFAULT NULL")
            except Exception: pass
        if 'order_type' not in existing_order_cols:
            try: cursor.execute("ALTER TABLE orders ADD COLUMN order_type TEXT DEFAULT 'account'")
            except Exception: pass
        if 'custom_info' not in existing_order_cols:
            try: cursor.execute("ALTER TABLE orders ADD COLUMN custom_info TEXT DEFAULT NULL")
            except Exception: pass

        # إضافة باقات كوينز أولية تلقائياً إن كان الجدول فارغاً
        coins_count = cursor.execute("SELECT COUNT(*) FROM coins_packages").fetchone()[0]
        if coins_count == 0:
            initial_pkgs = [
                ("130 كوينز ⚡", 130, 65.0, "شحن رسمي فوري للـ ID"),
                ("550 كوينز 🔥", 550, 260.0, "الباقة الأكثر طلباً"),
                ("1,040 كوينز 🏆", 1040, 510.0, "باقة الباكات والنجوم"),
                ("2,130 كوينز 👑", 2130, 990.0, "باقة المحترفين"),
                ("3,250 كوينز 💎", 3250, 1490.0, "باقة الأساطير eFootball")
            ]
            cursor.executemany(
                "INSERT INTO coins_packages (title, coins_amount, price_egp, description) VALUES (?, ?, ?, ?)",
                initial_pkgs
            )

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
        return [row[0] for row in conn.cursor().execute("SELECT telegram_id FROM admins").fetchall()]

# --- Payment Methods ---
def add_payment_method(method_type, provider_title, details):
    with get_db() as conn:
        conn.cursor().execute(
            "INSERT INTO payment_methods (method_type, provider_title, details) VALUES (?, ?, ?)",
            (method_type, provider_title, details)
        )
        conn.commit()

def get_all_payment_methods():
    with get_db() as conn:
        return [dict(row) for row in conn.cursor().execute("SELECT * FROM payment_methods ORDER BY id DESC").fetchall()]

def get_payment_methods_by_type(method_type):
    with get_db() as conn:
        return [dict(row) for row in conn.cursor().execute(
            "SELECT * FROM payment_methods WHERE method_type = ?", (method_type,)
        ).fetchall()]

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

def get_account_by_id(account_id):
    with get_db() as conn:
        row = conn.cursor().execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
        return dict(row) if row else None

def update_account(account_id, title, details, price_egp, credentials, status='available', image_path=None):
    with get_db() as conn:
        if image_path:
            conn.cursor().execute("""
                UPDATE accounts 
                SET title = ?, details = ?, price_egp = ?, credentials = ?, status = ?, image_path = ?
                WHERE id = ?
            """, (title, details, price_egp, credentials, status, image_path, account_id))
        else:
            conn.cursor().execute("""
                UPDATE accounts 
                SET title = ?, details = ?, price_egp = ?, credentials = ?, status = ?
                WHERE id = ?
            """, (title, details, price_egp, credentials, status, account_id))
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

# --- Coins Packages ---
def add_coins_package(title, coins_amount, price_egp, description=''):
    with get_db() as conn:
        conn.cursor().execute(
            "INSERT INTO coins_packages (title, coins_amount, price_egp, description) VALUES (?, ?, ?, ?)",
            (title, int(coins_amount), float(price_egp), description)
        )
        conn.commit()

def get_all_coins_packages():
    with get_db() as conn:
        return [dict(row) for row in conn.cursor().execute("SELECT * FROM coins_packages ORDER BY coins_amount ASC").fetchall()]

def get_coins_package_by_id(pkg_id):
    with get_db() as conn:
        row = conn.cursor().execute("SELECT * FROM coins_packages WHERE id = ?", (pkg_id,)).fetchone()
        return dict(row) if row else None

def delete_coins_package(pkg_id):
    with get_db() as conn:
        conn.cursor().execute("DELETE FROM coins_packages WHERE id = ?", (pkg_id,))
        conn.commit()

def update_coins_package(pkg_id, title, coins_amount, price_egp, description=''):
    with get_db() as conn:
        conn.cursor().execute(
            "UPDATE coins_packages SET title = ?, coins_amount = ?, price_egp = ?, description = ? WHERE id = ?",
            (title, int(coins_amount), float(price_egp), description, pkg_id)
        )
        conn.commit()

# --- Stats ---
def get_stats():
    with get_db() as conn:
        cursor = conn.cursor()
        total = cursor.execute("SELECT COUNT(*) FROM accounts").fetchone()[0] or 0
        available = cursor.execute("SELECT COUNT(*) FROM accounts WHERE status = 'available'").fetchone()[0] or 0
        sold = cursor.execute("SELECT COUNT(*) FROM accounts WHERE status = 'sold'").fetchone()[0] or 0
        total_coins_pkgs = cursor.execute("SELECT COUNT(*) FROM coins_packages").fetchone()[0] or 0
        pending_orders = cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending'").fetchone()[0] or 0
        revenue_egp = cursor.execute("SELECT SUM(price_egp) FROM accounts WHERE status = 'sold'").fetchone()[0] or 0

        revenue_usd = round(revenue_egp * EGP_TO_USD, 2)
        revenue_iqd = int(revenue_egp * EGP_TO_IQD)

        return {
            "total": total,
            "available": available,
            "sold": sold,
            "total_coins_pkgs": total_coins_pkgs,
            "pending_orders": pending_orders,
            "revenue_egp": revenue_egp,
            "revenue_usd": revenue_usd,
            "revenue_iqd": revenue_iqd
        }

# --- Orders ---
def create_order(user_id, account_id=None, payment_method='vodafone', username=None, full_name=None, order_type='account', package_id=None, custom_info=None):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO orders (user_id, account_id, payment_method, username, full_name, order_type, package_id, custom_info)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, account_id, payment_method, username, full_name, order_type, package_id, custom_info)
        )
        conn.commit()
        return cursor.lastrowid

def get_all_orders():
    with get_db() as conn:
        rows = conn.cursor().execute("""
            SELECT o.*, 
                   COALESCE(a.title, cp.title, 'طلب كوينز / مباشر') as account_title, 
                   COALESCE(a.price_egp, cp.price_egp, 0) as price_egp
            FROM orders o
            LEFT JOIN accounts a ON o.account_id = a.id
            LEFT JOIN coins_packages cp ON o.package_id = cp.id
            ORDER BY o.id DESC
        """).fetchall()
        return [dict(row) for row in rows]

def get_order_by_id(order_id):
    with get_db() as conn:
        row = conn.cursor().execute("""
            SELECT o.*, 
                   COALESCE(a.title, cp.title, 'طلب كوينز / مباشر') as account_title, 
                   COALESCE(a.price_egp, cp.price_egp, 0) as price_egp
            FROM orders o
            LEFT JOIN accounts a ON o.account_id = a.id
            LEFT JOIN coins_packages cp ON o.package_id = cp.id
            WHERE o.id = ?
        """, (order_id,)).fetchone()
        return dict(row) if row else None

def get_orders_by_user(user_id):
    with get_db() as conn:
        rows = conn.cursor().execute("""
            SELECT o.*, 
                   COALESCE(a.title, cp.title, 'طلب كوينز') as account_title, 
                   COALESCE(a.price_egp, cp.price_egp, 0) as price_egp
            FROM orders o
            LEFT JOIN accounts a ON o.account_id = a.id
            LEFT JOIN coins_packages cp ON o.package_id = cp.id
            WHERE o.user_id = ?
            ORDER BY o.id DESC
        """, (user_id,)).fetchall()
        return [dict(row) for row in rows]

def process_order(order_id, approve=True):
    """
    معالجة الطلب: موافقة أو رفض.
    Returns: (user_id, credentials, order_type, custom_info)
    """
    with get_db() as conn:
        cursor = conn.cursor()
        order = cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not order:
            return None, None, None, None

        user_id = order['user_id']
        account_id = order['account_id']
        order_type = order['order_type'] if 'order_type' in order.keys() else 'account'
        custom_info = order['custom_info'] if 'custom_info' in order.keys() else None

        if approve:
            credentials = None
            if account_id:
                account = cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
                credentials = account['credentials'] if account else None
                cursor.execute("UPDATE accounts SET status = 'sold' WHERE id = ?", (account_id,))
            cursor.execute("UPDATE orders SET status = 'approved' WHERE id = ?", (order_id,))
            conn.commit()
            return user_id, credentials, order_type, custom_info
        else:
            if account_id:
                cursor.execute("UPDATE accounts SET status = 'available', reserved_by = NULL WHERE id = ?", (account_id,))
            cursor.execute("UPDATE orders SET status = 'rejected' WHERE id = ?", (order_id,))
            conn.commit()
            return user_id, None, order_type, custom_info