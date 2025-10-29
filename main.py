import telebot
from telebot import types
import json
import time
from datetime import datetime, timedelta

# --- CONSTANTS (CHANGE THESE PLACEHOLDERS) ---
API_TOKEN = '8330994680:AAGzqKp1-E-f_-peG0giaYyO2NcEI2aYbNA'
ADMIN_ID = 7943354448  # Admin ID provided by user
DATA_FILE = 'bot_data.json'
# IMPORTANT: Replace these with actual payment numbers
ADMIN_BKASH_NO = "01774049543" 
ADMIN_NAGAD_NO = "01774049543" 

bot = telebot.TeleBot(API_TOKEN)

# --- GLOBAL DATA STRUCTURES ---
users = {}
orders = {}
visa_mastercards = [] # Stores cards: [{"card": "1234... | 01/25 | 123", "available": True}]

# --- DATA PERSISTENCE ---

def load_data():
    """Loads data from the JSON file."""
    global users, orders, visa_mastercards
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            users = data.get('users', {})
            orders = data.get('orders', {})
            visa_mastercards = data.get('visa_mastercards', [])
    except FileNotFoundError:
        print("Data file not found, starting with empty data.")
    except Exception as e:
        print(f"Error loading data: {e}")

def save_data():
    """Saves data to the JSON file."""
    try:
        data = {
            'users': users,
            'orders': orders,
            'visa_mastercards': visa_mastercards
        }
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving data: {e}")

load_data()

# --- HELPER FUNCTIONS & MARKUPS ---

def back_markup():
    """Returns a ReplyKeyboardMarkup with the back button."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("↩️ মেনুতে ফিরে যান")
    return markup

def payment_markup():
    """Returns a ReplyKeyboardMarkup for payment selection."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📲 Bkash", "📲 Nagad", "↩️ মেনুতে ফিরে যান")
    return markup

def home_menu(chat_id):
    """Sends the main menu keyboard."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # New buttons
    markup.add("💳 Free Visa/Mastercard")
    markup.add("💬 Support Admin")
    
    # Existing button
    markup.add("🎁 Play Point Park On")
    
    bot.send_message(chat_id, "🏠 প্রধান মেনু:", reply_markup=markup)

def admin_required(func):
    """Decorator to restrict access to admin only."""
    def wrapper(message):
        if message.chat.id == ADMIN_ID:
            func(message)
        else:
            bot.send_message(message.chat.id, "❌ আপনি এই কমান্ড ব্যবহার করার অনুমতি পাননি।")
    return wrapper

# --- CORE HANDLERS ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Handles the /start command and initializes user data."""
    user_id = str(message.from_user.id)
    if user_id not in users:
        # Initialize card_claims for the new user
        users[user_id] = {"card_claims": []} 
        save_data()
    home_menu(message.chat.id)

@bot.message_handler(func=lambda m: m.text == "↩️ মেনুতে ফিরে যান")
def back_to_home(message):
    """Clears step handlers and returns to the main menu."""
    bot.clear_step_handler(message)
    home_menu(message.chat.id)

# --- NEW FEATURE: SUPPORT ADMIN ---

@bot.message_handler(func=lambda m: m.text == "💬 Support Admin")
def support_handler(message):
    """Displays admin contact information."""
    support_info = f"""
ℹ️ **সাপোর্ট তথ্য:**

এডমিন আইডি: **@Raimadmin**
হোয়াটসঅ্যাপ নম্বর: **01774049543**

যেকোনো প্রয়োজনে যোগাযোগ করুন।
"""
    bot.send_message(message.chat.id, support_info, parse_mode="Markdown")

# --- NEW FEATURE: FREE CARD SYSTEM ---

def check_daily_limit(user_id):
    """Checks if the user has claimed 5 cards today."""
    today_date = datetime.now().strftime("%Y-%m-%d")
    
    # Filter claims only for today
    today_claims = [
        c for c in users.get(user_id, {}).get("card_claims", []) 
        if c.get("date") == today_date
    ]
    return len(today_claims)

@bot.message_handler(func=lambda m: m.text == "💳 Free Visa/Mastercard")
def free_card_handler(message):
    """Handles the free card claim process with a daily limit of 5."""
    user_id = str(message.from_user.id)
    
    if user_id not in users: 
        users[user_id] = {"card_claims": []}
    
    claims_today = check_daily_limit(user_id)
    
    if claims_today >= 5:
        bot.send_message(message.chat.id, f"❌ দুঃখিত! আপনি আজকের জন্য আপনার **৫টি কার্ডের দৈনিক সীমা** পূরণ করেছেন। আগামীকাল আবার চেষ্টা করুন।")
        return
        
    # Find the first available card
    available_card_index = -1
    for i, card_data in enumerate(visa_mastercards):
        if card_data.get("available", True) is True:
            available_card_index = i
            break
            
    if available_card_index == -1:
        bot.send_message(message.chat.id, "😔 দুঃখিত! এই মুহূর্তে কোনো ফ্রি কার্ড মজুত নেই। এডমিনকে যোগাযোগ করুন।")
        return

    # Claim the card
    claimed_card = visa_mastercards[available_card_index]
    claimed_card_number = claimed_card["card"]
    
    # Mark as unavailable
    visa_mastercards[available_card_index]["available"] = False
    
    # Update user claims
    today_date = datetime.now().strftime("%Y-%m-%d")
    users[user_id]["card_claims"].append({
        "card": claimed_card_number,
        "date": today_date,
        "time": time.time()
    })
    
    save_data()
    
    remaining_claims = 5 - (claims_today + 1)
    
    response_msg = f"""
✅ কার্ড সফলভাবে দাবি করা হয়েছে!

💳 **আপনার ফ্রি কার্ড:**
`{claimed_card_number}`

⚠️ **দ্রষ্টব্য:** এই কার্ড শুধুমাত্র একবার ব্যবহারযোগ্য।

আপনি আজকে আরও **{remaining_claims}** টি কার্ড নিতে পারবেন।
"""
    bot.send_message(message.chat.id, response_msg, parse_mode="Markdown")

# --- EXISTING: Play Point Park On Flow ---

@bot.message_handler(func=lambda m: m.text == "🎁 Play Point Park On")
def play_point_menu(message):
    user_id = str(message.from_user.id)
    if user_id in users and users[user_id].get("is_blocked"): return

    options = """
🌍 দেশ নির্বাচন করুন:

🇺🇸 USA
🇹🇼 Taiwan
🇬🇧 UK
🇰🇷 South Korean

💡 প্রতিটি Park On-এর জন্য 20 টাকা খরচ হবে
"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🇺🇸 USA", "🇹🇼 Taiwan", "🇬🇧 UK", "🇰🇷 South Korean", "↩️ মেনুতে ফিরে যান")
    msg = bot.send_message(message.chat.id, options, reply_markup=markup)
    bot.register_next_step_handler(msg, process_play_point_country)

def process_play_point_country(message):
    if message.text == "↩️ মেনুতে ফিরে যান":
        bot.clear_step_handler(message)
        return home_menu(message.chat.id)
    
    country = message.text
    user_id = str(message.from_user.id)
    if user_id not in users: users[user_id] = {} # Safety check
    
    users[user_id]["play_point_country"] = country
    quantity_msg = f"""
🔢 কতগুলো Park On চান?

💡 পরিমাণ লিখুন (সংখ্যা):
"""
    msg = bot.send_message(message.chat.id, quantity_msg, reply_markup=back_markup())
    bot.register_next_step_handler(msg, process_play_point_quantity)

def process_play_point_quantity(message):
    if message.text == "↩️ মেনুতে ফিরে যান":
        bot.clear_step_handler(message)
        return home_menu(message.chat.id)
    
    try:
        quantity = int(message.text)
        if quantity <= 0:
            raise ValueError
        
        user_id = str(message.from_user.id)
        if user_id not in users: return home_menu(message.chat.id) # Session check

        users[user_id]["play_point_quantity"] = quantity
        total_price = quantity * 20
        users[user_id]["play_point_price"] = total_price
        
        details_msg = f"""
💰 মোট মূল্য: {total_price} টাকা

এখন আপনি যে Gmail/Password-গুলোতে Park On করতে চান সেগুলো একসাথে লিখুন:
(প্রতি লাইনে একটি Gmail/Password)

ফরম্যাট:
example1@gmail.com/password1
example2@gmail.com/password2
"""
        msg = bot.send_message(message.chat.id, details_msg, reply_markup=back_markup())
        bot.register_next_step_handler(msg, process_play_point_details)
        
    except ValueError:
        error_msg = """
❌ অবৈধ সংখ্যা! শুধুমাত্র সংখ্যা লিখুন।

আবার চেষ্টা করুন:
"""
        msg = bot.send_message(message.chat.id, error_msg, reply_markup=back_markup())
        bot.register_next_step_handler(msg, process_play_point_quantity)

def process_play_point_details(message):
    if message.text == "↩️ মেনুতে ফিরে যান":
        bot.clear_step_handler(message)
        return home_menu(message.chat.id)
    
    user_id = str(message.from_user.id)
    if user_id not in users or "play_point_price" not in users[user_id]: 
        bot.send_message(message.chat.id, "❌ সেশন এক্সপায়ার্ড! আবার চেষ্টা করুন।")
        return home_menu(message.chat.id)
        
    play_point_details = message.text
    users[user_id]["play_point_details"] = play_point_details

    order_summary = f"""
📝 অর্ডার সারাংশ:

🌍 Country: {users[user_id]["play_point_country"]}
🔢 Quantity: {users[user_id]["play_point_quantity"]} টি
💰 মোট মূল্য: {users[user_id]["play_point_price"]} TK

💳 পেমেন্ট মাধ্যম নির্বাচন করুন:
"""
    # Use the message object from the previous step to register the next step
    bot.send_message(message.chat.id, order_summary, reply_markup=payment_markup())
    bot.register_next_step_handler(message, process_play_point_payment)

def process_play_point_payment(message):
    if message.text == "↩️ মেনুতে ফিরে যান":
        bot.clear_step_handler(message)
        return home_menu(message.chat.id)

    user_id = str(message.from_user.id)
    if user_id not in users or "play_point_price" not in users[user_id]: 
        bot.send_message(message.chat.id, "❌ সেশন এক্সপায়ার্ড! আবার চেষ্টা করুন।")
        return home_menu(message.chat.id)
        
    user_data = users[user_id]
    
    if message.text not in ["📲 Bkash", "📲 Nagad"]:
        error_msg = "❌ দয়া করে পেমেন্ট মাধ্যম নির্বাচন করুন:"
        msg = bot.send_message(message.chat.id, error_msg, reply_markup=payment_markup())
        bot.register_next_step_handler(msg, process_play_point_payment)
        return
        
    method = "Bkash" if "Bkash" in message.text else "Nagad"
    payment_number = ADMIN_BKASH_NO if method == "Bkash" else ADMIN_NAGAD_NO
    price = user_data["play_point_price"]
    
    payment_instructions = f"""
💳 {method} এ টাকা পাঠান:

📱 Number: {payment_number}
💰 Amount: {price} TK
📝 Reference: PPON{user_id}

⚠️ টাকা পাঠানোর পর Transaction ID নোট করে রাখুন

📨 এখন আপনার Transaction ID লিখুন:
"""
    msg = bot.send_message(message.chat.id, payment_instructions, reply_markup=back_markup())
    bot.register_next_step_handler(msg, lambda m: confirm_play_point_order(m, method, price))

def confirm_play_point_order(message, method, price):
    if message.text == "↩️ মেনুতে ফিরে যান":
        bot.clear_step_handler(message)
        return home_menu(message.chat.id)
        
    txn_id = message.text
    user_id = str(message.from_user.id)
    if user_id not in users or "play_point_details" not in users[user_id]: 
        bot.send_message(message.chat.id, "❌ সেশন এক্সপায়ার্ড! আবার চেষ্টা করুন।")
        return home_menu(message.chat.id)
        
    order_id = f"PPON{int(time.time())}{user_id}"
    orders[order_id] = {
        "user_id": user_id,
        "service": "Play Point Park On",
        "country": users[user_id]["play_point_country"],
        "quantity": users[user_id]["play_point_quantity"],
        "details": users[user_id]["play_point_details"],
        "price": price,
        "method": method,
        "txn_id": txn_id,
        "status": "pending",
        "username": message.from_user.username
    }
    save_data() # Save the new order

    markup = types.InlineKeyboardMarkup()
    # Inline button for admin delivery
    markup.add(types.InlineKeyboardButton("✅ Deliver Order", callback_data=f"deliver_pp_{order_id}")) 

    admin_msg = f"""
🎁 **নতুন Play Point Park On অর্ডার** 🎁

📦 Order ID: `{order_id}`
👤 User: @{message.from_user.username or 'N/A'}
🆔 User ID: `{user_id}`
🌍 Country: {orders[order_id]["country"]}
🔢 Quantity: {orders[order_id]["quantity"]} টি
💰 Amount: {price} TK
💳 Method: {method}
📝 Txn ID: `{txn_id}`
⏰ Time: {time.strftime("%Y-%m-%d %H:%M:%S")}

📩 Gmail Details:
{orders[order_id]["details"]}
"""
    bot.send_message(ADMIN_ID, admin_msg, reply_markup=markup, parse_mode="Markdown")

    user_confirmation = f"""
✅ **আপনার অর্ডার কনফার্ম হয়েছে!**

📦 Order ID: `{order_id}`
🎁 Service: Play Point Park On
💰 Paid: {price} TK

আপনার অর্ডারটি প্রসেস করা হচ্ছে।
ডেলিভারি সময়: ১-১২ ঘন্টা

সেবা নেওয়ার জন্য ধন্যবাদ! 🙏
"""
    bot.send_message(message.chat.id, user_confirmation, parse_mode="Markdown")
    home_menu(message.chat.id)


# --- ADMIN PANEL ---

@bot.message_handler(commands=['admin'])
@admin_required
def admin_menu(message):
    """Displays the admin control panel menu."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("/addcard", "/removecard", "/broadcast", "↩️ মেনুতে ফিরে যান")
    
    card_count = sum(1 for card in visa_mastercards if card.get("available", True))
    pending_count = len([o for o in orders.values() if o['status'] == 'pending'])
    
    msg = f"""
👑 **এডমিন প্যানেল** 👑
মুজুত ফ্রি কার্ড: **{card_count}** টি
পেন্ডিং অর্ডার: **{pending_count}** টি

দয়া করে একটি অপশন নির্বাচন করুন:
"""
    bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="Markdown")

# --- ADMIN: ADD CARD ---

@bot.message_handler(commands=['addcard'])
@admin_required
def add_card_start(message):
    """Starts the process for adding new free cards."""
    msg = bot.send_message(message.chat.id, 
                           "💳 নতুন ভিসা/মাস্টারকার্ডের তথ্য লিখুন।\n\nফরম্যাট (প্রতি লাইনে একটি কার্ড):\nCard Number | Exp Date | CVV\n\nউদাহরণ:\n1234-5678-9012-3456 | 01/25 | 123", 
                           reply_markup=back_markup())
    bot.register_next_step_handler(msg, process_add_card)

def process_add_card(message):
    """Processes the input card data and adds them to inventory."""
    if message.text == "↩️ মেনুতে ফিরে যান":
        return admin_menu(message)
        
    new_cards = []
    lines = message.text.strip().split('\n')
    
    for line in lines:
        card_data = line.strip()
        if card_data:
            # Check if card already exists (basic deduplication)
            if not any(c['card'] == card_data and c['available'] for c in visa_mastercards):
                new_cards.append({"card": card_data, "available": True})
            
    if new_cards:
        visa_mastercards.extend(new_cards)
        save_data()
        bot.send_message(message.chat.id, f"✅ সফলভাবে **{len(new_cards)}** টি কার্ড যোগ করা হয়েছে।", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "⚠️ কোনো কার্ড যোগ করা হয়নি অথবা কার্ডগুলো ইতিমধ্যেই মজুত আছে। ফরম্যাট ঠিক আছে কি না দেখুন।")
        
    admin_menu(message)

# --- ADMIN: REMOVE CARD ---

@bot.message_handler(commands=['removecard'])
@admin_required
def remove_card_start(message):
    """Starts the process for removing an available card by index."""
    available_cards_info = [
        (i, card["card"]) 
        for i, card in enumerate(visa_mastercards) 
        if card.get("available", True)
    ]
    
    if not available_cards_info:
        bot.send_message(message.chat.id, "❌ বর্তমানে কোনো মজুত ফ্রি কার্ড নেই যা আপনি রিমুভ করতে পারেন।")
        return admin_menu(message)
        
    # Create a list for display, using 1-based indexing
    card_list = "\n".join([f"**{i+1}**: `{card_str}`" for i, (_, card_str) in enumerate(available_cards_info)])
    
    msg_text = f"""
🗑️ **কার্ড রিমুভ করুন**

নিচের তালিকা থেকে যে কার্ডটি রিমুভ করতে চান তার ক্রমিক সংখ্যা (index) লিখুন:

{card_list}

❌ রিমুভ করতে না চাইলে `cancel` লিখে পাঠান।
"""
    msg = bot.send_message(message.chat.id, msg_text, parse_mode="Markdown", reply_markup=back_markup())
    bot.register_next_step_handler(msg, process_remove_card)

def process_remove_card(message):
    """Processes the index input to remove the card."""
    if message.text.lower() == "cancel" or message.text == "↩️ মেনুতে ফিরে যান":
        bot.send_message(message.chat.id, "🗑️ কার্ড রিমুভ বাতিল করা হলো।")
        return admin_menu(message)
        
    try:
        index_to_remove = int(message.text.strip()) - 1
        
        # Get the list of actual indices that are available
        available_indices = [i for i, card in enumerate(visa_mastercards) if card.get("available", True)]
        
        if 0 <= index_to_remove < len(available_indices):
            actual_index = available_indices[index_to_remove]
            removed_card = visa_mastercards.pop(actual_index)
            save_data()
            bot.send_message(message.chat.id, f"✅ কার্ড **`{removed_card['card']}`** সফলভাবে রিমুভ করা হয়েছে।", parse_mode="Markdown")
        else:
            msg = bot.send_message(message.chat.id, "❌ অবৈধ ক্রমিক সংখ্যা। দয়া করে সঠিক সংখ্যাটি লিখুন:")
            bot.register_next_step_handler(msg, process_remove_card)
            return
            
    except ValueError:
        msg = bot.send_message(message.chat.id, "❌ শুধুমাত্র ক্রমিক সংখ্যা লিখুন।")
        bot.register_next_step_handler(msg, process_remove_card)
        return

    admin_menu(message)

# --- ADMIN: BROADCAST SYSTEM ---

@bot.message_handler(commands=['broadcast'])
@admin_required
def broadcast_start(message):
    """Starts the broadcast command flow."""
    msg = bot.send_message(message.chat.id, 
                           "📣 আপনি যে মেসেজটি ব্রডকাস্ট করতে চান তা টেক্সট, ফটো বা ভিডিও সহ পাঠান।\n\n❌ ব্রডকাস্ট বাতিল করতে `cancel` লিখে পাঠান।", 
                           reply_markup=back_markup())
    bot.register_next_step_handler(msg, process_broadcast)

def process_broadcast(message):
    """Processes the broadcast message and sends it to all users."""
    if message.text and (message.text.lower() == "cancel" or message.text == "↩️ মেনুতে ফিরে যান"):
        bot.send_message(message.chat.id, "📣 ব্রডকাস্ট বাতিল করা হলো।")
        return admin_menu(message)
        
    all_user_ids = list(users.keys())
    sent_count = 0
    
    # Determine message type and send
    if message.text:
        send_func = bot.send_message
        args = (message.text,)
    elif message.photo:
        send_func = bot.send_photo
        args = (message.photo[-1].file_id, message.caption)
    elif message.video:
        send_func = bot.send_video
        args = (message.video.file_id, message.caption)
    else:
        bot.send_message(message.chat.id, "❌ আপনি কোনো টেক্সট, ছবি বা ভিডিও দেননি। আবার চেষ্টা করুন।")
        return admin_menu(message)

    for user_id in all_user_ids:
        try:
            # Prevent sending to Admin himself unless absolutely necessary
            if int(user_id) == ADMIN_ID:
                continue

            send_func(user_id, *args)
            sent_count += 1
            time.sleep(0.1) # Rate limit protection
        except Exception:
            # User blocked the bot, skip
            pass
        
    bot.send_message(message.chat.id, f"✅ সফলভাবে **{sent_count}** জন ব্যবহারকারীকে ব্রডকাস্ট করা হয়েছে।", parse_mode="Markdown")
    admin_menu(message)


# --- NEW FEATURE: PLAY POINT DELIVERY SYSTEM (Callback Handler) ---

@bot.callback_query_handler(func=lambda call: call.data.startswith('deliver_pp_'))
@admin_required
def deliver_play_point_order(call):
    """Handles the 'Deliver' inline button for Park On orders."""
    bot.answer_callback_query(call.id, "ডেলিভারি প্রসেস করা হচ্ছে...")
    
    order_id = call.data.split('_')[2]
    
    if order_id not in orders:
        bot.send_message(call.message.chat.id, f"❌ অর্ডার ID **{order_id}** খুঁজে পাওয়া যায়নি।")
        return

    order = orders[order_id]
    
    if order["status"] == "delivered":
        bot.edit_message_text(f"⚠️ অর্ডার ID `{order_id}` ইতিমধ্যেই ডেলিভার করা হয়েছে।", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        return
        
    # Admin is prompted to provide delivery details
    msg = bot.send_message(call.message.chat.id, 
                           f"ডেলিভারির তথ্য লিখুন Order ID **`{order_id}`** এর জন্য। এই মেসেজটি ব্যবহারকারীকে পাঠানো হবে।", 
                           reply_markup=back_markup(), parse_mode="Markdown")
    
    # Use lambda to pass the order_id and the original admin message ID to the next step
    bot.register_next_step_handler(msg, lambda m: finalize_delivery(m, order_id, call.message.message_id))


def finalize_delivery(message, order_id, original_message_id):
    """Finalizes the delivery, notifies the user, and updates the admin's message."""
    if message.text == "↩️ মেনুতে ফিরে যান":
        bot.send_message(message.chat.id, "ডেলিভারি বাতিল করা হলো।")
        return admin_menu(message)

    delivery_message = message.text
    
    if order_id not in orders:
        bot.send_message(message.chat.id, f"❌ অর্ডার ID **{order_id}** খুঁজে পাওয়া যায়নি।")
        return admin_menu(message)
    
    order = orders[order_id]
    user_id = order["user_id"]
    
    # 1. Update order status
    orders[order_id]["status"] = "delivered"
    orders[order_id]["delivery_message"] = delivery_message
    save_data()
    
    # 2. Notify the user
    user_msg = f"""
✅ **আপনার অর্ডার ডেলিভার করা হয়েছে!**

📦 Order ID: `{order_id}`
🎁 Service: {order["service"]}

***ডেলিভারির বিবরণ:***
{delivery_message}

সেবা নেওয়ার জন্য ধন্যবাদ! 🙏
"""
    try:
        bot.send_message(user_id, user_msg, parse_mode="Markdown")
    except Exception:
        bot.send_message(message.chat.id, f"⚠️ ব্যবহারকারী ({user_id}) বট ব্লক করে দিয়েছে।")
        
    # 3. Update the admin's original message
    admin_confirmation_text = f"""
✅ **DELIVERED** ✅
অর্ডার ID `{order_id}` সফলভাবে ডেলিভার করা হয়েছে।
👤 User ID: `{user_id}` | User: @{order.get('username', 'N/A')}
---
ডেলিভারির বিবরণ:
{delivery_message}
"""
    try:
        bot.edit_message_text(admin_confirmation_text, message.chat.id, original_message_id, parse_mode="Markdown")
    except Exception:
        # Ignore error if message is too old/modified
        pass

    bot.send_message(message.chat.id, "ডেলিভারি প্রক্রিয়া সম্পন্ন হয়েছে।")
    admin_menu(message)


# --- BOT POLLING ---

if __name__ == '__main__':
    print("Bot is starting...")
    # Optional: Log the admin URL for easy access (replace with your bot username)
    print(f"Admin, start your chat with /start and then use /admin.")
    
    # Make sure to handle potential network errors gracefully
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(15) # Wait before retrying to prevent rapid loop

