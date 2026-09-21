import os
import asyncio
import logging
import uuid
import traceback
import json
import urllib.request
from functools import wraps
from threading import Thread
from flask import Flask, render_template, request, redirect, url_for, session

import database as db
import config
from bot import run_telegram_bot

# إعداد السجلات
logging.basicConfig(level=logging.INFO)

# ==========================================
# 1. Helper: Send Telegram Direct Message
# ==========================================
def send_telegram_direct_message(user_id, text):
    """إرسال رسالة تليجرام متزامنة ومستقلة مباشرة إلى المشتري"""
    if not config.BOT_TOKEN or not user_id:
        return False
    url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": user_id,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status == 200
    except Exception as e:
        logging.error(f"Failed to send Telegram message to {user_id}: {e}")
        return False

# ==========================================
# 2. Flask App (Dashboard)
# ==========================================
app = Flask(__name__)
app.secret_key = config.SECRET_KEY

UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ── Auth Decorator ──────────────────────────────────────────────────────────
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_global_data():
    try:
        stats = db.get_stats()
        return {'pending_count': stats.get('pending_orders', 0)}
    except Exception:
        return {'pending_count': 0}

# ── Auth Routes ─────────────────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('index'))

    error = None
    if request.method == 'POST':
        password = request.form.get('password')
        if password == config.DASHBOARD_PASSWORD:
            session['logged_in'] = True
            next_url = request.args.get('next')
            return redirect(next_url or url_for('index'))
        else:
            error = "كلمة المرور غير صحيحة! يرجى المحاولة مرة أخرى."

    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# ── Dashboard Routes ────────────────────────────────────────────────────────
@app.route('/')
@admin_required
def index():
    try:
        db.init_db()
        stats = db.get_stats()
        recent_accounts = db.get_all_accounts()[:5]
        return render_template('index.html', stats=stats, recent_accounts=recent_accounts, active_page='home')
    except Exception:
        return f"<pre>{traceback.format_exc()}</pre>", 500

@app.route('/accounts')
@admin_required
def accounts():
    accounts_list = db.get_all_accounts()
    return render_template('accounts.html', accounts=accounts_list, active_page='accounts')

@app.route('/add_account', methods=['POST'])
@admin_required
def add_account_route():
    title = request.form.get('title')
    details = request.form.get('details')
    price_egp = request.form.get('price_egp')
    credentials = request.form.get('credentials')
    image = request.files.get('image')

    image_path = None
    if image and image.filename != '' and allowed_file(image.filename):
        ext = image.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(filepath)
        image_path = filepath.replace('\\', '/')

    db.add_account(title, details, float(price_egp), credentials, image_path)
    return redirect(url_for('accounts'))

@app.route('/accounts/edit/<int:account_id>', methods=['GET', 'POST'])
@admin_required
def edit_account_route(account_id):
    account = db.get_account_by_id(account_id)
    if not account:
        return redirect(url_for('accounts'))

    if request.method == 'POST':
        title = request.form.get('title')
        details = request.form.get('details')
        price_egp = float(request.form.get('price_egp', 0))
        credentials = request.form.get('credentials')
        status = request.form.get('status', 'available')
        image = request.files.get('image')

        image_path = None
        if image and image.filename != '' and allowed_file(image.filename):
            ext = image.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(filepath)
            image_path = filepath.replace('\\', '/')

        db.update_account(account_id, title, details, price_egp, credentials, status, image_path)
        return redirect(url_for('accounts'))

    return render_template('edit_account.html', account=account, active_page='accounts')

@app.route('/delete_account/<int:account_id>')
@admin_required
def delete_account_route(account_id):
    db.delete_account(account_id)
    return redirect(url_for('accounts'))

# ── Coins Packages Routes ───────────────────────────────────────────────────
@app.route('/coins')
@admin_required
def coins():
    packages = db.get_all_coins_packages()
    return render_template('coins.html', packages=packages, active_page='coins')

@app.route('/add_coins', methods=['POST'])
@admin_required
def add_coins_route():
    title = request.form.get('title')
    coins_amount = request.form.get('coins_amount')
    price_egp = request.form.get('price_egp')
    description = request.form.get('description', '')

    if title and coins_amount and price_egp:
        db.add_coins_package(title, coins_amount, price_egp, description)
    return redirect(url_for('coins'))

@app.route('/delete_coins/<int:pkg_id>')
@admin_required
def delete_coins_route(pkg_id):
    db.delete_coins_package(pkg_id)
    return redirect(url_for('coins'))

# ── Payments Routes ─────────────────────────────────────────────────────────
@app.route('/payments')
@admin_required
def payments():
    payment_methods = db.get_all_payment_methods()
    return render_template('payments.html', payment_methods=payment_methods, active_page='payments')

@app.route('/add_payment', methods=['POST'])
@admin_required
def add_payment_route():
    method_type = request.form.get('method_type')
    provider_title = request.form.get('provider_title')
    details = request.form.get('details')
    if method_type and provider_title and details:
        db.add_payment_method(method_type, provider_title, details)
    return redirect(url_for('payments'))

@app.route('/delete_payment/<int:pm_id>')
@admin_required
def delete_payment_route(pm_id):
    db.delete_payment_method(pm_id)
    return redirect(url_for('payments'))

# ── Orders Routes & Dashboard Approval ──────────────────────────────────────
@app.route('/orders')
@admin_required
def orders():
    all_orders = db.get_all_orders()
    return render_template('orders.html', orders=all_orders, active_page='orders')

@app.route('/order/approve/<int:order_id>')
@admin_required
def approve_order_route(order_id):
    user_id, credentials, order_type, custom_info = db.process_order(order_id, approve=True)
    if user_id:
        if order_type == 'coins' or not credentials:
            msg = (
                f"🎉 <b>تم تأكيد وشحن طلب الكوينز الخاص بك بنجاح!</b>\n\n"
                f"🎮 <b>تفاصيل الشحن:</b> {custom_info or 'شحن رسمي فوري'}\n\n"
                "✅ شكراً لاختيارك متجر RODRIGO eFootball!\n"
                "نتمنى لك تجربة لعب ممتعة ⚡"
            )
        else:
            msg = (
                f"🎉 <b>تم تأكيد وقبول طلبك بنجاح من لوحة الإدارة!</b>\n\n"
                f"🔐 <b>بيانات الحساب الخاص بك:</b>\n"
                f"<code>{credentials}</code>\n\n"
                "✅ شكراً لثقتك بمتجر RODRIGO eFootball!\n"
                "🔁 في حال واجهت أي استفسار، تواصل مع الدعم الفني."
            )
        send_telegram_direct_message(user_id, msg)
    return redirect(url_for('orders'))

@app.route('/order/reject/<int:order_id>')
@admin_required
def reject_order_route(order_id):
    user_id, _, order_type, custom_info = db.process_order(order_id, approve=False)
    if user_id:
        msg = (
            "❌ <b>تم رفض طلبك/إيصال التحويل من قِبل الإدارة.</b>\n\n"
            "الأسباب المحتملة:\n"
            "• إيصال غير واضح أو المبلغ المحول غير مطابق.\n"
            "• خطأ في كتابة بيانات الشحن.\n\n"
            "📞 يرجى مراجعة إيصالك أو التواصل مع إدارة المتجر لحل المشكلة."
        )
        send_telegram_direct_message(user_id, msg)
    return redirect(url_for('orders'))

# ── Admins Routes ───────────────────────────────────────────────────────────
@app.route('/admins')
@admin_required
def admins():
    admins_list = db.get_admins()
    return render_template('admins.html', admins=admins_list, active_page='admins')

@app.route('/add_admin', methods=['POST'])
@admin_required
def add_admin_route():
    telegram_id = request.form.get('telegram_id')
    name = request.form.get('name')
    if telegram_id and name:
        db.add_admin(int(telegram_id), name)
    return redirect(url_for('admins'))

@app.route('/delete_admin/<int:admin_id>')
@admin_required
def delete_admin_route(admin_id):
    db.delete_admin(admin_id)
    return redirect(url_for('admins'))

def run_flask():
    db.init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ==========================================
# 3. Entry Point
# ==========================================
def main():
    db.init_db()

    # تشغيل Flask في Thread منفصل
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("🌐 Dashboard → http://localhost:5000")

    # تشغيل بوت التلجرام
    print("🤖 Telegram Bot is running...")
    run_telegram_bot()

if __name__ == '__main__':
    main()