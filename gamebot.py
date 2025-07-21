from rubka import Robot
from rubka.keypad import ChatKeypadBuilder
from rubka.context import Message
import random, time, json, os

bot = Robot("BCAHH0USYYKPVTQLQKBKVFITJSAZABHKDFQPJPXSPAGLOJSBXEEFODBMLFZTYXYS")

users_data_path = "game_users.json"
users_data = {}

if os.path.exists(users_data_path):
    with open(users_data_path, "r") as f:
        users_data = json.load(f)

def save_data():
    with open(users_data_path, "w") as f:
        json.dump(users_data, f)

def get_user(uid):
    if uid not in users_data:
        users_data[uid] = {
            "wallet": 0,
            "miner_level": 0,
            "miner_collected": 0,
            "last_mine_time": time.time(),
            "last_spin_day": "",
            "state": None,
            "bet_amount": 0
        }
    return users_data[uid]

def update_miner(uid):
    user = get_user(uid)
    now = time.time()
    elapsed = now - user["last_mine_time"]
    coins = int(user["miner_level"] * elapsed * 0.5)
    user["miner_collected"] += coins
    user["last_mine_time"] = now

main_keypad = (
    ChatKeypadBuilder()
    .row(ChatKeypadBuilder().button("wallet", "💰 موجودی"), ChatKeypadBuilder().button("miner", "⛏️ ماینر"))
    .row(ChatKeypadBuilder().button("collect", "📥 جمع ماینر"), ChatKeypadBuilder().button("spin", "🎰 گردونه"))
    .row(ChatKeypadBuilder().button("buy_one", "➕ خرید ماینر"), ChatKeypadBuilder().button("buy_max", "🛒 خرید حداکثر"))
    .row(ChatKeypadBuilder().button("bet", "🎲 شرط بندی"), ChatKeypadBuilder().button("rps", "✊ سنگ 📄 کاغذ ✂️ قیچی"))
    .build()
)

@bot.on_message()
def handle_message(bot, message: Message):
    try:
        if (time.time() - float(message.time)) > 5:
            return
        uid = message.sender_id
        text = message.text.strip()
        user = get_user(uid)
        update_miner(uid)

        if text == "/start":
            user["state"] = None
            message.reply_keypad("به گیم بات هخامنش خوش اومدی 🎮 یکی از گزینه‌ها رو انتخاب کن 👇", keypad=main_keypad)
            return
        if user.get("state") == "awaiting_even_odd":
            choice = text
            bet = user["bet_amount"]
            rand = random.randint(0, 1)
            result = "زوج" if rand == 0 else "فرد"
            win = (choice == "زوج" and rand == 0) or (choice == "فرد" and rand == 1)
            if win:
                user["wallet"] += bet
                message.reply(f"🎉 تبریک! عدد {result} اومد و {bet:,} سکه بردی!")
            else:
                user["wallet"] -= bet
                message.reply(f"😢 باختی! عدد {result} اومد و {bet:,} سکه از دست دادی.")
            user["state"] = None
            user["bet_amount"] = 0
            save_data()
            return
        if user.get("state") == "rps" and text in ["✊ سنگ", "📄 کاغذ", "✂️ قیچی"]:
            bot_choice = random.choice(["✊ سنگ", "📄 کاغذ", "✂️ قیچی"])
            user["state"] = None
            result_text = f"تو: {text}\nربات: {bot_choice}\n\n"
            wins = {"✊ سنگ": "✂️ قیچی", "📄 کاغذ": "✊ سنگ", "✂️ قیچی": "📄 کاغذ"}
            if text == bot_choice:
                result_text += "🤝 مساوی شد!"
            elif wins[text] == bot_choice:
                result_text += "🎉 تو بردی!"
            else:
                result_text += "😢 باختی!"
            message.reply(result_text)
            return
        if user.get("state") == "awaiting_bet_amount":
            if text.isdigit():
                amount = int(text)
                if amount <= 0:
                    message.reply("❌ مبلغ باید بیشتر از صفر باشه.")
                    return
                if amount > user["wallet"]:
                    message.reply("❌ موجودی کافی نداری.")
                    return
                user["bet_amount"] = amount
                user["state"] = "awaiting_even_odd"
                message.reply_keypad(
                    f"🎲 مبلغ شرط: {amount:,} سکه\nحالا انتخاب کن 👇",
                    ChatKeypadBuilder()
                        .row(ChatKeypadBuilder().button("زوج", "زوج"), ChatKeypadBuilder().button("فرد", "فرد"))
                        .build()
                )
            else:
                message.reply("❗ لطفاً فقط عدد وارد کن.")
            return
        if text == "💰 موجودی":
            message.reply(f"💰 موجودی: {user['wallet']:,} سکه")

        elif text == "⛏️ ماینر":
            message.reply(f"⛏️ سطح ماینر: {user['miner_level']}\n📥 ذخیره شده: {user['miner_collected']:,} سکه")

        elif text == "📥 جمع ماینر":
            coins = user["miner_collected"]
            if coins > 0:
                user["wallet"] += coins
                user["miner_collected"] = 0
                message.reply(f"📥 {coins:,} سکه به کیف پولت اضافه شد!")
            else:
                message.reply("⛏️ هنوز چیزی جمع نشده.")
            save_data()

        elif text == "➕ خرید ماینر":
            cost = 1000 * (user["miner_level"] + 1)
            if user["wallet"] >= cost:
                user["wallet"] -= cost
                user["miner_level"] += 1
                message.reply(f"✅ یک سطح ماینر خریدی! قیمت: {cost:,} سکه")
            else:
                message.reply(f"❌ سکه کافی نداری. قیمت فعلی: {cost:,} سکه")
            save_data()

        elif text == "🛒 خرید حداکثر":
            bought = 0
            while True:
                cost = 1000 * (user["miner_level"] + 1)
                if user["wallet"] >= cost:
                    user["wallet"] -= cost
                    user["miner_level"] += 1
                    bought += 1
                else:
                    break
            if bought > 0:
                message.reply(f"✅ {bought} سطح ماینر خریدی.")
            else:
                message.reply("❌ برای خرید حتی یک سطح هم پول نداری.")
            save_data()

        elif text == "🎰 گردونه":
            today = time.strftime("%Y-%m-%d")
            if user["last_spin_day"] == today:
                message.reply("🎰 گردونه امروز استفاده شده. فردا دوباره بیا!")
            else:
                reward = random.randint(50_000, 10_000_000_000)
                user["wallet"] += reward
                user["last_spin_day"] = today
                message.reply(f"🎉 گردونه برات {reward:,} سکه آورد!")
                save_data()

        elif text == "🎲 شرط بندی":
            user["state"] = "awaiting_bet_amount"
            message.reply("🎰 مبلغ شرط رو وارد کن (عدد):")

        elif text == "✊ سنگ 📄 کاغذ ✂️ قیچی":
            user["state"] = "awaiting_rps_amount"
            message.reply("💰 لطفاً مقدار شرط رو به عدد وارد کن:")

        elif user.get("state") == "awaiting_rps_amount":
            if text.isdigit():
                amount = int(text)
                if amount <= 0:
                    message.reply("❌ مبلغ باید بیشتر از صفر باشه.")
                    return
                if amount > user["wallet"]:
                    message.reply("❌ موجودی کافی نداری.")
                    return
                user["bet_amount"] = amount
                user["state"] = "awaiting_rps_choice"
                message.reply_keypad(
                    f"🎮 مبلغ شرط: {amount:,} سکه\nحالا یکی رو انتخاب کن 👇",
                    ChatKeypadBuilder()
                    .row(
                        ChatKeypadBuilder().button("سنگ", "✊ سنگ"),
                        ChatKeypadBuilder().button("کاغذ", "📄 کاغذ"),
                        ChatKeypadBuilder().button("قیچی", "✂️ قیچی")
                    ).build()
                )
            else:
                message.reply("❗ لطفاً فقط عدد وارد کن.")
            return

        elif user.get("state") == "awaiting_rps_choice" and text in ["✊ سنگ", "📄 کاغذ", "✂️ قیچی"]:
            user["state"] = None
            bet = user["bet_amount"]
            user["bet_amount"] = 0
            bot_choice = random.choice(["✊ سنگ", "📄 کاغذ", "✂️ قیچی"])

            result_text = f"تو: {text}\nربات: {bot_choice}\n\n"

            wins = {
                "✊ سنگ": "✂️ قیچی",
                "📄 کاغذ": "✊ سنگ",
                "✂️ قیچی": "📄 کاغذ"
            }

            if text == bot_choice:
                result_text += "🤝 مساوی شد! شرطت برگشت خورد."
            elif wins[text] == bot_choice:
                user["wallet"] += bet
                result_text += f"🎉 تو بردی! {bet:,} سکه به دست آوردی."
            else:
                user["wallet"] -= bet
                result_text += f"😢 باختی! {bet:,} سکه از دست دادی."
            save_data()
            message.reply(result_text)
            return
        else:
            message.reply("❗ لطفاً از دکمه‌های کیبورد استفاده کن یا /start بزن.")
    except Exception as e:
        print("خطا:", e)

bot.run()