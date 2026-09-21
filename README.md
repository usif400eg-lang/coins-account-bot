# 🛒 Coins & Accounts Telegram Bot + Web Dashboard

بوت تلجرام متطور لبيع حسابات الألعاب والعملات (Coins & Accounts) مع لوحة تحكم إدارية ويب (Web Dashboard) مدمجة.

## ✨ المميزات (Features)
- 🤖 **بوت تلجرام كامل**: تصفح الحسابات، عمل الطلبات، إرسال إيصالات الدفع، إشعارات تلقائية للأدمنز والمشترين.
- 🌐 **لوحة تحكم إدارية (Flask Dashboard)**: واجهة أنيقة (Dark Mode / Glassmorphism) لإدارة الحسابات، طرق الدفع، الطلبات، وصلاحيات الأدمنز.
- 💱 **تعدد العملات**: دعم الجنيه المصري، الدولار الأمريكي، والدينار العراقي.
- 🚀 **جاهز للنشر**: مهيأ للتشغيل السحابي المباشر عبر Railway بملفات `Procfile` و `requirements.txt`.

## ⚙️ التشغيل محلياً (Local Run)
```bash
pip install -r requirements.txt
python main.py
```

## ☁️ النشر على Railway (Deployment)
1. قم بربط هذا المستودع في Railway.
2. اضغط **Deploy**.
3. أضف متغير البيئة `BOT_TOKEN` في تبويب Variables إذا رغبت.
