import os
import uuid
import traceback
from flask import Flask, render_template, request, redirect, url_for
import database as db

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 1. الصفحة الرئيسية (الإحصائيات)
@app.route('/')
def index():
    try:
        db.init_db()
        stats = db.get_stats()
        recent_accounts = db.get_all_accounts()[:5]  # أحدث 5 حسابات
        return render_template('index.html', stats=stats, recent_accounts=recent_accounts, active_page='home')
    except Exception as e:
        return f"<div style='direction:ltr; padding:20px; color:red;'><pre>{traceback.format_exc()}</pre></div>", 500

# 2. صفحة الحسابات والمنتجات
@app.route('/accounts')
def accounts():
    accounts_list = db.get_all_accounts()
    return render_template('accounts.html', accounts=accounts_list, active_page='accounts')

@app.route('/add_account', methods=['POST'])
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

@app.route('/delete_account/<int:account_id>')
def delete_account_route(account_id):
    db.delete_account(account_id)
    return redirect(url_for('accounts'))

# 3. صفحة وسائل الدفع
@app.route('/payments')
def payments():
    payment_methods = db.get_all_payment_methods()
    return render_template('payments.html', payment_methods=payment_methods, active_page='payments')

@app.route('/add_payment', methods=['POST'])
def add_payment_route():
    method_type = request.form.get('method_type')
    provider_title = request.form.get('provider_title')
    details = request.form.get('details')
    if method_type and provider_title and details:
        db.add_payment_method(method_type, provider_title, details)
    return redirect(url_for('payments'))

@app.route('/delete_payment/<int:pm_id>')
def delete_payment_route(pm_id):
    db.delete_payment_method(pm_id)
    return redirect(url_for('payments'))

# 4. صفحة الأدمنز
@app.route('/admins')
def admins():
    admins_list = db.get_admins()
    return render_template('admins.html', admins=admins_list, active_page='admins')

@app.route('/add_admin', methods=['POST'])
def add_admin_route():
    telegram_id = request.form.get('telegram_id')
    name = request.form.get('name')
    if telegram_id and name:
        db.add_admin(int(telegram_id), name)
    return redirect(url_for('admins'))

@app.route('/delete_admin/<int:admin_id>')
def delete_admin_route(admin_id):
    db.delete_admin(admin_id)
    return redirect(url_for('admins'))

def run_flask():
    db.init_db()
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    run_flask()