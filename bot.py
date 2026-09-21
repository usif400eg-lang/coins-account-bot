# bot.py — RODRIGO eFootball Shop Bot (Upgraded)
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
import config
import database as db

logging.basicConfig(level=logging.INFO)

# ── تحويل العملات ──────────────────────────────────────────────────────────
EGP_TO_USD = 0.021
EGP_TO_IQD = 28.0

STATUS_EMOJI = {
    "pending":  "⏳",
    "approved": "✅",
    "rejected": "❌"
}

METHOD_EMOJI = {
    "vodafone":  "📱",
    "instapay":  "🏦",
    "bank_card": "💳",
    "iraq":      "🌐"
}

METHOD_LABEL = {
    "vodafone":  "فودافون كاش",
    "instapay":  "InstaPay",
    "bank_card": "بطاقة بنكية / ميزة",
    "iraq":      "آسيا سيل / زين كاش"
}

# ═══════════════════════════════════════════════
# /start
# ═══════════════════════════════════════════════
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = (
        f"⚡ <b>أهلاً {user.first_name}!</b>\n\n"
        "🎮 <b>RODRIGO eFOOTBALL SHOP</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "المتجر الأول لشراء حسابات eFootball الموثوقة\n"
        "أسعار منافسة · تسليم فوري · دعم 24/7\n\n"
        "👇 <b>اختر من القائمة:</b>"
    )

    keyboard = [
        [InlineKeyboardButton("🎮  عرض الحسابات المتاحة", callback_data="list_accounts")],
        [InlineKeyboardButton("📦  طلباتي", callback_data="my_orders")],
        [
            InlineKeyboardButton("💬 المالك الأول", url=config.OWNERS_CONTACTS[0][1]),
            InlineKeyboardButton("💬 المالك الثاني", url=config.OWNERS_CONTACTS[1][1])
        ]
    ]

    await update.message.reply_text(
        welcome_text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ═══════════════════════════════════════════════
# /myorders
# ═══════════════════════════════════════════════
async def my_orders_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _show_my_orders(update.effective_user.id, update.message.reply_text)

async def _show_my_orders(user_id, reply_fn):
    orders = db.get_orders_by_user(user_id)
    if not orders:
        await reply_fn(
            "📦 <b>لا يوجد لديك طلبات سابقة.</b>\n\nابعت /start لتصفح الحسابات!",
            parse_mode="HTML"
        )
        return

    text = "📦 <b>طلباتك:</b>\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for o in orders[:10]:
        emoji = STATUS_EMOJI.get(o['status'], "❓")
        text += (
            f"\n{emoji} <b>طلب #{o['id']}</b> — {o.get('account_title', 'حساب')}\n"
            f"   💰 {o.get('price_egp', 0)} ج.م  |  💳 {o['payment_method']}\n"
            f"   📅 {str(o['created_at'])[:16]}\n"
        )

    await reply_fn(text, parse_mode="HTML")

# ═══════════════════════════════════════════════
# Handle Buttons (Callback Queries)
# ═══════════════════════════════════════════════
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    # ─── عرض الحسابات ─────────────────────────────
    if data == "list_accounts":
        accounts = db.get_available_accounts()
        if not accounts:
            await query.message.reply_text(
                "❌ <b>عذراً، لا توجد حسابات متاحة حالياً.</b>\n\nتواصل مع الدعم لمعرفة موعد التوفر.",
                parse_mode="HTML"
            )
            return

        for acc in accounts:
            price_egp = acc['price_egp']
            price_usd = round(price_egp * EGP_TO_USD, 1)
            price_iqd = int(price_egp * EGP_TO_IQD)

            caption = (
                f"⚽ <b>{acc['title']}</b>\n"
                f"━━━━━━━━━━━━━━\n"
                f"📝 {acc['details']}\n\n"
                f"💵 <b>السعر:</b>\n"
                f"  🇪🇬 <b>{price_egp:,.0f} ج.م</b>\n"
                f"  🇺🇸 ${price_usd}\n"
                f"  🇮🇶 {price_iqd:,} IQD"
            )

            keyboard = [
                [InlineKeyboardButton(f"💳  شراء الحساب الآن", callback_data=f"buy_{acc['id']}")],
            ]

            if acc['image_path']:
                try:
                    with open(acc['image_path'], 'rb') as photo:
                        await query.message.reply_photo(
                            photo=photo,
                            caption=caption,
                            parse_mode="HTML",
                            reply_markup=InlineKeyboardMarkup(keyboard)
                        )
                    continue
                except Exception:
                    pass
            await query.message.reply_text(caption, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

    # ─── طلباتي ────────────────────────────────────
    elif data == "my_orders":
        await _show_my_orders(user_id, query.message.reply_text)

    # ─── شراء حساب ────────────────────────────────
    elif data.startswith("buy_"):
        acc_id = int(data.split("_")[1])

        if db.reserve_account(acc_id, user_id):
            keyboard = [
                [InlineKeyboardButton("📱 فودافون كاش", callback_data=f"pay_vodafone_{acc_id}")],
                [InlineKeyboardButton("🏦 InstaPay", callback_data=f"pay_instapay_{acc_id}")],
                [InlineKeyboardButton("💳 بطاقة بنكية / ميزة", callback_data=f"pay_bank_card_{acc_id}")],
                [InlineKeyboardButton("🌐 آسيا سيل / زين كاش", callback_data=f"pay_iraq_{acc_id}")],
                [InlineKeyboardButton("❌ إلغاء", callback_data=f"cancel_{acc_id}")]
            ]
            await query.message.reply_text(
                "💳 <b>اختر وسيلة الدفع المناسبة لك:</b>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.message.reply_text(
                "❌ <b>عذراً، هذا الحساب تم حجزه أو بيعه.</b>\n\nجرب حساباً آخر!",
                parse_mode="HTML"
            )

    # ─── اختيار طريقة الدفع ───────────────────────
    elif data.startswith("pay_"):
        parts = data.split("_")
        method = parts[1]
        acc_id = int(parts[2])

        context.user_data['awaiting_receipt'] = True
        context.user_data['pay_method'] = method
        context.user_data['acc_id'] = acc_id

        db_methods = db.get_payment_methods_by_type(method)
        emoji = METHOD_EMOJI.get(method, "💳")
        label = METHOD_LABEL.get(method, method)

        if db_methods:
            numbers_text = "\n".join(
                [f"  • <b>{m['provider_title']}:</b> <code>{m['details']}</code>" for m in db_methods]
            )
        else:
            numbers_text = "  • لا توجد أرقام مسجلة. تواصل مع الدعم."

        instructions = (
            f"{emoji} <b>وسيلة الدفع: {label}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📌 <b>أرقام التحويل:</b>\n"
            f"{numbers_text}\n\n"
            f"⚠️ <b>الخطوات:</b>\n"
            f"1️⃣ حوّل المبلغ المطلوب للرقم أعلاه\n"
            f"2️⃣ خذ صورة الإيصال (Screenshot)\n"
            f"3️⃣ <b>ابعت الصورة هنا مباشرة</b>\n\n"
            f"⏰ الطلب محجوز لمدة 30 دقيقة"
        )
        await query.message.reply_text(instructions, parse_mode="HTML")

    # ─── إلغاء الحجز ──────────────────────────────
    elif data.startswith("cancel_"):
        parts = data.split("_")
        if len(parts) > 1:
            try:
                acc_id = int(parts[1])
                # إعادة الحساب للمتجر
                with db.get_db() as conn:
                    conn.cursor().execute(
                        "UPDATE accounts SET status='available', reserved_by=NULL WHERE id=? AND reserved_by=?",
                        (acc_id, user_id)
                    )
                    conn.commit()
            except Exception:
                pass
        await query.message.reply_text("❌ <b>تم إلغاء العملية.</b>", parse_mode="HTML")
        context.user_data.clear()

    # ─── موافقة الأدمن ────────────────────────────
    elif data.startswith("admin_approve_"):
        admin_ids = db.get_admin_telegram_ids() + config.ADMIN_IDS
        if user_id not in admin_ids:
            await query.answer("⚠️ خاص بالإدارة فقط!", show_alert=True)
            return

        order_id = int(data.split("_")[2])
        target_user_id, credentials = db.process_order(order_id, approve=True)
        if target_user_id:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=(
                    "🎉 <b>تم تأكيد طلبك بنجاح!</b>\n\n"
                    "🔐 <b>بيانات الحساب الخاص بك:</b>\n"
                    f"<code>{credentials}</code>\n\n"
                    "✅ شكراً لثقتك بمتجر RODRIGO!\n"
                    "🔁 لأي مشكلة تواصل مع الدعم."
                ),
                parse_mode="HTML"
            )
            old_caption = query.message.caption or query.message.text or ""
            new_text = old_caption + "\n\n✅ <b>تمت الموافقة والتسليم.</b>"
            try:
                await query.edit_message_caption(caption=new_text, parse_mode="HTML")
            except Exception:
                try:
                    await query.edit_message_text(text=new_text, parse_mode="HTML")
                except Exception:
                    pass
        else:
            await query.answer("⚠️ الطلب غير موجود أو تمت معالجته مسبقاً.", show_alert=True)

    # ─── رفض الأدمن ───────────────────────────────
    elif data.startswith("admin_reject_"):
        admin_ids = db.get_admin_telegram_ids() + config.ADMIN_IDS
        if user_id not in admin_ids:
            await query.answer("⚠️ خاص بالإدارة فقط!", show_alert=True)
            return

        order_id = int(data.split("_")[2])
        target_user_id, _ = db.process_order(order_id, approve=False)
        if target_user_id:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=(
                    "❌ <b>تم رفض إيصالك.</b>\n\n"
                    "الأسباب المحتملة:\n"
                    "• صورة غير واضحة\n"
                    "• مبلغ غير مطابق\n\n"
                    "📞 تواصل مع الدعم لحل المشكلة."
                ),
                parse_mode="HTML"
            )
            old_caption = query.message.caption or query.message.text or ""
            new_text = old_caption + "\n\n❌ <b>تم الرفض وإعادة الحساب للمتجر.</b>"
            try:
                await query.edit_message_caption(caption=new_text, parse_mode="HTML")
            except Exception:
                try:
                    await query.edit_message_text(text=new_text, parse_mode="HTML")
                except Exception:
                    pass
        else:
            await query.answer("⚠️ الطلب غير موجود أو تمت معالجته مسبقاً.", show_alert=True)

# ═══════════════════════════════════════════════
# استقبال الإيصال (صورة)
# ═══════════════════════════════════════════════
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('awaiting_receipt'):
        return

    user = update.effective_user
    acc_id = context.user_data.get('acc_id')
    method = context.user_data.get('pay_method')
    photo_file_id = update.message.photo[-1].file_id

    order_id = db.create_order(
        user_id=user.id,
        account_id=acc_id,
        payment_method=method,
        username=user.username,
        full_name=user.full_name
    )
    context.user_data['awaiting_receipt'] = False

    await update.message.reply_text(
        "⏳ <b>تم استلام إيصالك بنجاح!</b>\n\n"
        f"📋 رقم طلبك: <code>#Order_{order_id}</code>\n\n"
        "جاري المراجعة وسيصلك الحساب فور التأكيد.\n"
        "⏰ وقت المراجعة المعتاد: أقل من 15 دقيقة.",
        parse_mode="HTML"
    )

    # بناء إشعار الأدمن
    emoji = METHOD_EMOJI.get(method, "💳")
    label = METHOD_LABEL.get(method, method)
    admin_caption = (
        f"📥 <b>طلب جديد #Order_{order_id}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>المشتري:</b> {user.full_name}"
        + (f" (@{user.username})" if user.username else "") + "\n"
        f"🆔 <b>User ID:</b> <code>{user.id}</code>\n"
        f"{emoji} <b>وسيلة الدفع:</b> {label}\n"
        f"🎮 <b>رقم الحساب:</b> <code>{acc_id}</code>"
    )

    keyboard = [[
        InlineKeyboardButton("✅ موافقة وتسليم", callback_data=f"admin_approve_{order_id}"),
        InlineKeyboardButton("❌ رفض الطلب", callback_data=f"admin_reject_{order_id}")
    ]]

    all_admin_ids = set(db.get_admin_telegram_ids() + config.ADMIN_IDS)
    for admin_id in all_admin_ids:
        try:
            await context.bot.send_photo(
                chat_id=admin_id,
                photo=photo_file_id,
                caption=admin_caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logging.error(f"Failed to notify admin {admin_id}: {e}")

# ═══════════════════════════════════════════════
# Entry Point
# ═══════════════════════════════════════════════
def run_telegram_bot():
    db.init_db()
    application = Application.builder().token(config.BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("myorders", my_orders_cmd))
    application.add_handler(CallbackQueryHandler(handle_buttons))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    application.run_polling()