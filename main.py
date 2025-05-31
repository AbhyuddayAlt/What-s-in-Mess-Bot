from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from datetime import datetime, time, timedelta
import pytz
import os
import sys
import logging
from db import init_db, save_user, get_all_users, update_notification_settings, get_user_settings
import psutil

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "7265497857:AAFAfZEgGwMlA3GTR3xQv7G-ah0-hoA8jVQ"
# Track last notification sent to prevent duplicates
last_notification = {}

# Mess timetable
meal_schedule = {
    "Breakfast": (time(7, 30), time(8, 30)),
    "Lunch": (time(12, 20), time(14, 0)),
    "Snacks": (time(17, 0), time(18, 0)),
    "Dinner": (time(19, 30), time(21, 0))
}

# Boys Hostel Menu
boys_menu = {
    "Monday": {
        "Breakfast": "🍽️ Veg Fried Idli + Plain Idli + Sambhar + Coconut Chutney + Tea + Milk + Seasonal Fruits",
        "Lunch": "🍛 Mix Veg with Paneer + Rajma + Roti + Rice + Salad + Boondi Raita + Lemon 1/2",
        "Snacks": "🥔 Aloo Tikki / Papdi Chaat (5 pcs) + Matar + Curd + Sonth + Hari Chutney + Chaat Masala + Roohafza",
        "Dinner": "🍚 Arhar Daal + Bhindi + Rice + Roti + Suji Halwa + (Matar Mushroom (once in a month) / Moong Daal Halwa (once in a month)) + Onion Salad"
    },
    "Tuesday": {
        "Breakfast": "🍽️ Matar Kulche + Pickle + Tea + Milk + Seasonal Fruits",
        "Lunch": "🍛 Tahari + Aloo Tamatar Sabji + Roti + Salad + Curd + Lemon 1/2 + Hari Chutney",
        "Snacks": "🍝 Chowmein / Pasta + Tomato Sauce + Chilli Sauce + Shikanji",
        "Dinner": "🍚 Kali Masoor Daal + Kathal + Rice + Roti + Ice Cream (Mango / Butterscotch / Vanilla) + Onion Salad"
    },
    "Wednesday": {
        "Breakfast": "🍽️ Aloo Paratha + Pickle + Curd + Milk + Tea + Seasonal Fruits",
        "Lunch": "🍛 Kaabli Chhole (Small) + Kashifal + Roti + Jeera Rice + Mix Salad + Curd + Lemon 1/2",
        "Snacks": "🥟 Samosa + Chilli Sauce + Sonth + Tea",
        "Dinner": "🍚 (Mattar / Kadhi) Paneer + Aloo Began Tamatar Chokha + Puri + Pulav + Onion Salad"
    },
    "Thursday": {
        "Breakfast": "🍽️ Pav Bhaji + Tea + Milk + Butter + Seasonal Fruits",
        "Lunch": "🍛 Aloo Pyaaj + Kadhi + Rice + Roti + Salad + Fried Papad + Lemon 1/2",
        "Snacks": "🍞 Bread Pakoda / Rusk (5 pcs) + Sonath + Hari Chatney + Tea",
        "Dinner": "🍚 Chana Daal + Aloo Parval + Roti + Rice + Gulab Jamun + Masala Chaach"
    },
    "Friday": {
        "Breakfast": "🍽️ Aloo Paratha + Pickle + Curd + Tea + Milk + Seasonal Fruits",
        "Lunch": "🍛 Aloo Gobhi Mattar + Arhar Daal + Roti + Rice + Mix Salad + Boondi Raita + Lemon 1/2",
        "Snacks": "🥙 Patties + Tomato Sauce + Tea",
        "Dinner": "🍚 Arhar Daal + Aloo Soyabeen / Karela + Rice + Roti + Besan Ladoo + Masala Chaach"
    },
    "Saturday": {
        "Breakfast": "🍽️ Aloo Tamatar Sabji + Ajwain Poori + Fry Mirchi + Tea + Jalebi + Curd + Seasonal Fruits",
        "Lunch": "🍛 Louki Dry + Arhar Daal + Roti + Rice + Salad + Curd + Lemon 1/2",
        "Snacks": "🥔 Poha + Chilli Sauce + Tomato Sauce + Chaat Masala + Shikanji",
        "Dinner": "🍚 Rajma + Aloo Bhujia + Jeera Rice + Roti + Masala Chaach"
    },
    "Sunday": {
        "Breakfast": "🍽️ Roasted Bread + Aloo Sandwich + Tomato Sauce + Cornflakes + Milk + Tea + Seasonal Fruits",
        "Lunch": "🍛 Chole (Kabuli Chane Big) + Bhature + Fried Mirch + Sirka Pyaaj + Jeera Rice + Cold Drink + Pickle + Veg Raita",
        "Snacks": "🚫 OFF",
        "Dinner": "🍚 Mix Daal + Aloo / Kala Chana / Arbi + Roti + Rice + Kheer / Sewai + Onion Salad"
    }
}

# Girls Hostel Menu
girls_menu = {
    "Monday": {
        "Breakfast": "Matar with cucumber & onion + Kulcha + Tea ☕ + Milk + Fruit 🍎",
        "Lunch": "Arhar Daal + Mix veg with paneer + Boondi raita + Rice 🍚 + Chapati + Salad 🥗 + 1/2 Lemon 🍋",
        "Snacks": "Bread pakoda/Mix pakodi + Tomato sauce + Green chutni + Tea ☕ (Green elaichi)",
        "Dinner": "Butter masala/Matar paneer + Aloo chokha + Chapati + Rice + Bessan Laddu/Jalebi + Masala chaach 🍬"
    },
    "Tuesday": {
        "Breakfast": "Fried idli + Sambhar + Nariyal chutni + Tea ☕ + Milk + Fruit 🍌",
        "Lunch": "Rajma + French beans + Aloo tamatar + Rice 🍚 + Curd + Salad 🥗 + 1/2 Lemon 🍋",
        "Snacks": "Chowmein + Tomato & green chilli sauce + Tang 🥤",
        "Dinner": "Tamatar-Aloo-Paneer + Chapati + Rice 🍚 + Gulab jamun 🍩 + Chaach"
    },
    "Wednesday": {
        "Breakfast": "Bread + Amul butter + Jam + Cornflakes + Tea ☕ + Milk + Fruit 🍇",
        "Lunch": "Kadhi + Aloo jeera + Chapati + Rice 🍚 + Fried mirchi + Papad + Masala onion + Lemon 🍋",
        "Snacks": "Poha/Namkeen jave + Sauce + Roohafza 🥤",
        "Dinner": "Matar chhole + Aloo tikki + Curd + Rice 🍚 OR Dum aloo/Mix veg + Ice cream 🍨"
    },
    "Thursday": {
        "Breakfast": "Plain parantha + Aloo jeera + Tea ☕ + Milk + Fruit 🍊",
        "Lunch": "Arhar daal + Aloo baingan + Rice 🍚 + Salad 🥗 + Lemon 🍋",
        "Snacks": "Macaroni + Sauce + Roohafza 🥤",
        "Dinner": "Chhole + Aloo tamatar + Chapati + Rice 🍚 + Ice cream 🍨 + Salad"
    },
    "Friday": {
        "Breakfast": "Pav bhaji + Tea ☕ + Milk + Fruit 🍐",
        "Lunch": "Rajma + Aloo jeera + Meethi (pasaa) + Rice 🍚 + Curd + Salad 🥗",
        "Snacks": "Black chana chaat + Coffee ☕",
        "Dinner": "Lauki kofta + Masoor daal + Veg curry + Rice 🍚 + Chapati + Ice cream 🍨 OR Methi aloo + Salad"
    },
    "Saturday": {
        "Breakfast": "Aloo parantha + Green chutni + Tea ☕ + Milk + Pickle + Fruit 🍎",
        "Lunch": "Black chana + Lauki kofta + Chapati + Rice 🍚 + Veg raita + Salad 🥗 + Lemon 🍋",
        "Snacks": "Samosa + Saunth + Green chutni + Tea ☕",
        "Dinner": "Pulav + Dahi aloo + Salad 🥗 + Custard 🍮 + Masala chaach"
    },
    "Sunday": {
        "Breakfast": "Aloo tamatar sabji + Poori + Tea ☕ + Milk + Pickle + Fruit 🍌",
        "Lunch": "Chhole masala + Aloo pyaz + Chapati + Rice 🍚 + Boondi raita + Salad 🥗 + Lemon 🍋",
        "Snacks": "OFF ❌",
        "Dinner": "Lauki chana daal + Arbi + Chapati + Rice 🍚 + Fruit + Custard 🍮 + Masala chaach"
    }
}

# Check if bot is already running
def is_bot_running():
    current_process = psutil.Process()
    for process in psutil.process_iter(['pid', 'name', 'cmdline']):
        if process.pid != current_process.pid:  # Skip current process
            try:
                if 'python' in process.name().lower() and 'main.py' in ' '.join(process.cmdline()):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    return False

def get_current_or_next_meal():
    now = datetime.now(pytz.timezone("Asia/Kolkata")).time()
    # if within a meal window => that meal
    for meal,(start,end) in meal_schedule.items():
        if start <= now <= end:
            return meal
    # otherwise next upcoming
    for meal,(start,_) in meal_schedule.items():
        if now < start:
            return meal
    return "Breakfast"

# Store the current menu selection in user_data
def get_menu_for_user(user_id):
    return context.user_data.get('selected_hostel', 'boys')

def build_main_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Select Hostel", callback_data="select_hostel")],
        [InlineKeyboardButton("🍽️ Today's Menu", callback_data="next_meal")],
        [InlineKeyboardButton("📅 View Other Days", callback_data="choose_day")],
        [InlineKeyboardButton("🔔 Notifications", callback_data="notification_settings")]
    ])

def build_notification_buttons(user_id):
    settings = get_user_settings(user_id)
    is_enabled = settings[1] if settings else False
    status_emoji = "✅" if is_enabled else "❌"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{status_emoji} 15-min Notifications: {'ON' if is_enabled else 'OFF'}", callback_data="toggle_updates")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_main")]
    ])

def build_meal_buttons():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🥣 Breakfast", callback_data="Breakfast"),
            InlineKeyboardButton("🍛 Lunch", callback_data="Lunch")
        ],
        [
            InlineKeyboardButton("🍪 Snacks", callback_data="Snacks"),
            InlineKeyboardButton("🍽️ Dinner", callback_data="Dinner")
        ],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_main")]
    ])

def build_day_buttons():
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    kb = []
    for i in range(0, len(days), 2):
        row = [InlineKeyboardButton(days[i], callback_data=f"day_{days[i]}")]
        if i + 1 < len(days):
            row.append(InlineKeyboardButton(days[i + 1], callback_data=f"day_{days[i + 1]}"))
        kb.append(row)
    kb.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_main")])
    return InlineKeyboardMarkup(kb)

def build_time_buttons():
    times = ["5", "10", "15", "20", "30", "45", "60", "Custom"]
    kb = []
    for i in range(0, len(times), 3):
        row = [InlineKeyboardButton(f"{t} min", callback_data=f"time_{t}") for t in times[i:i+3]]
        kb.append(row)
    kb.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_main")])
    return InlineKeyboardMarkup(kb)

def build_hostel_buttons():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👨 Boys Hostel", callback_data="hostel_boys"),
            InlineKeyboardButton("👩 Girls Hostel", callback_data="hostel_girls")
        ],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_main")]
    ])

async def save_user_info(update: Update):
    """Save user information to database"""
    user = update.effective_user
    if user:
        save_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await save_user_info(update)
    await update.message.reply_text(
        "👋 Welcome to the Mess Bot!\n\n"
        "🍽️ Check today's menu or view other days\n"
        "🔔 Get notified 15 minutes before each meal\n\n"
        "What would you like to do?",
        reply_markup=build_main_buttons()
    )

async def send_meal_notification(context: ContextTypes.DEFAULT_TYPE):
    """Send notifications to users who have opted for auto-updates"""
    tz = pytz.timezone("Asia/Kolkata")
    now = datetime.now(tz)
    today = now.strftime("%A")
    next_meal = get_current_or_next_meal()
    
    # Get meal time and create timezone-aware datetime
    meal_time = meal_schedule[next_meal][0]
    notification_time = tz.localize(datetime.combine(now.date(), meal_time)) - timedelta(minutes=15)
    
    # Get all users with auto-updates enabled
    all_users = get_all_users()
    
    for user_id in all_users:
        settings = get_user_settings(user_id)
        if not settings or not settings[1]:  # settings[1] is auto_updates
            continue
            
        # Create a unique key for this notification
        notification_key = f"{user_id}_{today}_{next_meal}"
        
        # Only send if we're within 1 minute of the notification time and haven't sent this notification before
        if (abs((now - notification_time).total_seconds()) <= 60 and 
            notification_key not in last_notification):
            
            message = f"🔔 *Upcoming {next_meal} in 15 minutes!*\n\n🍽️ *{today}'s {next_meal} Menu:*\n\n{menu[today].get(next_meal,'No data')}"
            
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode="Markdown"
                )
                # Mark this notification as sent
                last_notification[notification_key] = now
            except Exception as e:
                logger.error(f"Failed to send notification to {user_id}: {e}")
    
    # Clean up old notification records
    last_notification.clear()

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id

    # Handle hostel selection
    if data == "select_hostel":
        await query.edit_message_text(
            "🏠 *Select your hostel:*",
            parse_mode="Markdown",
            reply_markup=build_hostel_buttons()
        )
        return

    if data.startswith("hostel_"):
        hostel = data.split("_")[1]
        context.user_data['selected_hostel'] = hostel
        await query.edit_message_text(
            f"✅ Selected {hostel.title()} Hostel!\n\nWhat would you like to do?",
            reply_markup=build_main_buttons()
        )
        return

    # Handle notification settings
    if data == "notification_settings":
        settings = get_user_settings(user_id)
        is_enabled = settings[1] if settings else False
        status_emoji = "✅" if is_enabled else "❌"
        await query.edit_message_text(
            "🔔 *Notification Settings*\n\n"
            "Get notified 15 minutes before each meal time.\n"
            "Toggle the button below to enable/disable notifications.",
            parse_mode="Markdown",
            reply_markup=build_notification_buttons(user_id)
        )
        return

    # Handle auto-update toggle
    if data == "toggle_updates":
        settings = get_user_settings(user_id)
        current_status = settings[1] if settings else False
        
        update_notification_settings(user_id, auto_updates=not current_status)
        status = "enabled" if not current_status else "disabled"
        
        await query.edit_message_text(
            f"🔔 *Notification Settings*\n\n"
            f"Notifications have been {status}!\n"
            f"You will receive notifications 15 minutes before each meal.",
            parse_mode="Markdown",
            reply_markup=build_notification_buttons(user_id)
        )
        return

    # clear selection if we go back
    if data == "back_to_main":
        context.user_data.pop("selected_day", None)
        await query.edit_message_text(
            "👋 Welcome back! What would you like to do?",
            reply_markup=build_main_buttons()
        )
        return

    # next_meal on main
    if data == "next_meal":
        context.user_data.pop("selected_day", None)
        meal = get_current_or_next_meal()
        today = datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%A")
        hostel = context.user_data.get('selected_hostel', 'boys')
        menu = boys_menu if hostel == 'boys' else girls_menu
        text = f"🍽️ *{today}'s {meal} Menu ({hostel.title()} Hostel):*\n\n{menu[today].get(meal,'No data')}"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=build_meal_buttons())
        return

    # choose day
    if data == "choose_day":
        await query.edit_message_text(
            "📅 *Choose a day to view its menu:*",
            parse_mode="Markdown",
            reply_markup=build_day_buttons()
        )
        return

    # day selected
    if data.startswith("day_"):
        day = data.split("_",1)[1]
        context.user_data["selected_day"] = day
        # show that day's current/next meal
        meal = get_current_or_next_meal()
        hostel = context.user_data.get('selected_hostel', 'boys')
        menu = boys_menu if hostel == 'boys' else girls_menu
        text = f"🍽️ *{day}'s {meal} Menu ({hostel.title()} Hostel):*\n\n{menu[day].get(meal,'No data')}"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=build_meal_buttons())
        return

    # meal button (Breakfast/Lunch/Snacks/Dinner)
    if data in meal_schedule:
        # if a day was chosen, use that, otherwise today
        day = context.user_data.get("selected_day") or datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%A")
        hostel = context.user_data.get('selected_hostel', 'boys')
        menu = boys_menu if hostel == 'boys' else girls_menu
        text = f"🍽️ *{day}'s {data} Menu ({hostel.title()} Hostel):*\n\n{menu[day].get(data,'No data')}"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=build_meal_buttons())
        return

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a broadcast message to all users"""
    if not context.args:
        await update.message.reply_text("Please provide a message to broadcast.")
        return
        
    message = " ".join(context.args)
    users = get_all_users()
    success = 0
    failed = 0
    
    for user_id in users:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"{message}",
                parse_mode="Markdown"
            )
            success += 1
        except Exception as e:
            logger.error(f"Failed to send broadcast to {user_id}: {e}")
            failed += 1
    
    await update.message.reply_text(
        f"Broadcast completed!\n✅ Successfully sent: {success}\n❌ Failed: {failed}"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom time input"""
    if context.user_data.get('waiting_for_custom_time'):
        try:
            minutes = int(update.message.text)
            if 1 <= minutes <= 1440:  # Allow up to 24 hours
                user_id = update.effective_user.id
                update_notification_settings(user_id, notification_time=minutes)
                await update.message.reply_text(
                    f"✅ Notification time set to {minutes} minutes before each meal!",
                    reply_markup=build_main_buttons()
                )
            else:
                await update.message.reply_text(
                    "Please enter a number between 1 and 1440 minutes.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Back", callback_data="set_notification_time")
                    ]])
                )
        except ValueError:
            await update.message.reply_text(
                "Please enter a valid number.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data="set_notification_time")
                ]])
            )
        context.user_data.pop('waiting_for_custom_time', None)
        return

async def get_user_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hidden command to get total number of users"""
    users = get_all_users()
    await update.message.reply_text(f"👥 Total users: {len(users)}")

if __name__ == "__main__":
    try:
        # Initialize database
        init_db()
        
        # Check if bot is already running
        if is_bot_running():
            print("Bot is already running! Exiting...")
            sys.exit(1)
            
        app = Application.builder().token(BOT_TOKEN).build()
        
        # Add job to check for notifications every minute
        try:
            job_queue = app.job_queue
            if job_queue is not None:
                job_queue.run_repeating(send_meal_notification, interval=60, first=10)
                logger.info("Job queue started successfully")
            else:
                logger.warning("Job queue is not available. Auto-updates will not work.")
        except Exception as e:
            logger.error(f"Failed to set up job queue: {e}")
            logger.warning("Auto-updates will not work. Please install python-telegram-bot[job-queue]")
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CallbackQueryHandler(button_handler))
        app.add_handler(CommandHandler("broadcast", broadcast))
        app.add_handler(CommandHandler("kitne", get_user_count))
        logger.info("Bot started")
        app.run_polling()
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        sys.exit(1)
