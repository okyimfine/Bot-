from telebot import TeleBot, apihelper
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from threading import Timer, Thread
from web_dashboard import start_web_dashboard
from database import db
import time
import random
import os
import fcntl
import sys
"""
This script implements a Telegram bot for managing giveaways. 

It uses the TeleBot library to handle bot interactions, and includes features for:
- Creating giveaways with specified titles, gifts, durations, locations, and additional information.
- Listing active giveaways.
- Allowing users to join giveaways.
- Ending giveaways automatically after a set time or manually via a command.
- Selecting a random winner from the participants.
- Integrating with a web dashboard (web_dashboard.py) for monitoring.
- Using a database (database.py) to store giveaway and participant information.
- Keeping the bot alive using an external service (keep_alive.py).

The bot utilizes several states to guide users through the giveaway creation process,
and stores active giveaways and participants in dictionaries. It also includes error handling
and logging for debugging and monitoring purposes.
"""

# Lock file to prevent multiple bot instances
LOCK_FILE = "/tmp/hackhub_bot.lock"

def acquire_lock():
    """Acquire exclusive lock to prevent multiple bot instances"""
    try:
        lock_fd = open(LOCK_FILE, 'w')
        fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_fd.write(str(os.getpid()))
        lock_fd.flush()
        print("🔒 Bot lock acquired successfully")
        return lock_fd
    except (IOError, OSError) as e:
        print(f"❌ Could not acquire bot lock: {e}")
        print("🚫 Another bot instance is already running!")
        sys.exit(1)

def release_lock(lock_fd):
    """Release the bot lock"""
    try:
        fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
        lock_fd.close()
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
        print("🔓 Bot lock released")
    except:
        pass

# Acquire lock before starting
lock_fd = acquire_lock()

# Enable middleware before initializing TeleBot
apihelper.ENABLE_MIDDLEWARE = True
# Telegram bots use tokens for secure authentication.
# The token acts as a password, allowing the bot to interact with the Telegram API.
# It's crucial to keep the token secret to prevent unauthorized access and control of the bot.
BOT_TOKEN = "7707841213:AAH627pVM_RJDrn9NYVhvc1FbGwddL5Kn8I"
bot = TeleBot(BOT_TOKEN)

user_states = {}

# Load active giveaways and participants from database on startup
def load_active_data():
    global active_giveaways, participants
    active_giveaways = {}
    participants = {}

    # Load from database
    db_active = db.data.get('active_giveaways', {})
    db_participants = db.data.get('participants', {})

    # Convert string keys to integers for active_giveaways
    for msg_id_str, giveaway_data in db_active.items():
        msg_id = int(msg_id_str)
        active_giveaways[msg_id] = giveaway_data

        # Convert participants list to set of user_ids for faster lookup
        if msg_id_str in db_participants:
            participants[msg_id] = set()
            for participant in db_participants[msg_id_str]:
                if isinstance(participant, dict) and 'user_id' in participant:
                    participants[msg_id].add(participant['user_id'])

    print(f"📊 Loaded {len(active_giveaways)} active giveaways and {sum(len(p) for p in participants.values())} participants from database")

# Load data on startup
load_active_data()

def delete_giveaway_message(chat_id, msg_id):
    try:
        bot.delete_message(chat_id=chat_id, message_id=msg_id)
        print(f"🗑️ Deleted giveaway message {msg_id}")
    except Exception as e:
        print(f"❌ Could not delete message {msg_id}: {e}")

def end_giveaway(msg_id, manual=False, expired_offline=False):
    ending_reason = "manual" if manual else ("expired offline" if expired_offline else "automatic")
    print(f"🏁 Ending giveaway {msg_id} ({ending_reason})")

    giveaway_data = None
    chat_id = None

    if msg_id in active_giveaways:
        giveaway_data = active_giveaways[msg_id].copy()
        giveaway_title = giveaway_data.get('title', 'Unknown')
        chat_id = giveaway_data.get('chat_id')
        del active_giveaways[msg_id]
        print(f"🗑️ Removed giveaway '{giveaway_title}' from active list")

    count = len(participants.get(msg_id, []))

    if count > 0:
        # Pick a random winner
        winner_id = random.choice(list(participants[msg_id]))

        # Try to get winner's name
        winner_display = f"User ID {winner_id}"
        try:
            if chat_id:
                winner_info = bot.get_chat_member(chat_id, winner_id)
                winner_name = winner_info.user.first_name
                if winner_info.user.last_name:
                    winner_name += f" {winner_info.user.last_name}"
                winner_display = f"{winner_name} (ID: {winner_id})"
        except Exception as e:
            print(f"⚠️ Could not get winner info: {e}")

        # Record winner in database
        if giveaway_data:
            db.record_winner(winner_id, giveaway_data.get('title', 'Unknown'))

        if expired_offline:
            text = f"🎊 *GIVEAWAY TAMAT!* ⏰ (Tamat semasa bot offline)\n\n🏆 *Pemenang:* {winner_display}\n👥 *Jumlah penyertaan:* {count} pengguna\n\n🎁 *Hadiah:* {giveaway_data.get('gift', 'N/A') if giveaway_data else 'N/A'}"
        else:
            text = f"🎊 *GIVEAWAY TAMAT!*\n\n🏆 *Pemenang:* {winner_display}\n👥 *Jumlah penyertaan:* {count} pengguna\n\n🎁 *Hadiah:* {giveaway_data.get('gift', 'N/A') if giveaway_data else 'N/A'}"

        print(f"🏆 Winner selected: {winner_display}")
    else:
        if expired_offline:
            text = f"🎊 *GIVEAWAY TAMAT!* ⏰ (Tamat semasa bot offline)\n\n😔 Tiada penyertaan untuk giveaway ini"
        else:
            text = f"🎊 *GIVEAWAY TAMAT!*\n\n😔 Tiada penyertaan untuk giveaway ini"

    print(f"📊 Giveaway {msg_id} ended with {count} participants")

    # Try to update the message
    try:
        if chat_id:
            bot.edit_message_text(text, chat_id=chat_id, message_id=msg_id, parse_mode="Markdown", reply_markup=None)
            print(f"✅ Updated giveaway message {msg_id} with winner information")

            # Delete the message after 60 seconds for offline expired ones (more time to see)
            delete_delay = 60 if expired_offline else 30
            Timer(delete_delay, delete_giveaway_message, args=[chat_id, msg_id]).start()
        else:
            print(f"❌ No chat_id found for giveaway {msg_id}")

    except Exception as e:
        print(f"❌ Error editing message {msg_id}: {e}")
        # If we can't edit the message, still process the giveaway completion

    # Clean up participants and update database
    if msg_id in participants:
        del participants[msg_id]
        print(f"🗑️ Cleaned up participants for giveaway {msg_id}")

    # Remove from database and save
    db.remove_giveaway(msg_id)
    print(f"💾 Giveaway {msg_id} data moved to completed giveaways")

# Restore timers for active giveaways
def restore_giveaway_timers():
    current_time = time.time()
    expired_giveaways = []

    for msg_id, giveaway_data in active_giveaways.items():
        end_time = giveaway_data.get('end_time')
        duration = giveaway_data.get('duration', 0)

        if duration > 0 and end_time:
            if current_time >= end_time:
                # Giveaway should have ended - end it immediately
                expired_giveaways.append(msg_id)
                print(f"⏰ Giveaway {msg_id} '{giveaway_data.get('title', 'Unknown')}' expired while bot was offline - ending now")
            else:
                # Set new timer for remaining time
                remaining_time = end_time - current_time
                Timer(remaining_time, end_giveaway, args=[msg_id]).start()
                print(f"⏰ Restored timer for giveaway {msg_id} '{giveaway_data.get('title', 'Unknown')}': {remaining_time:.0f} seconds remaining")
        elif duration == 0:
            print(f"♾️ Unlimited giveaway {msg_id} '{giveaway_data.get('title', 'Unknown')}' restored (no timer needed)")

    # End expired giveaways immediately
    for msg_id in expired_giveaways:
        print(f"🏁 Processing expired giveaway {msg_id}")
        end_giveaway(msg_id, manual=False, expired_offline=True)

# Restore timers after loading data
restore_giveaway_timers()
"""
These dictionaries store the state of the bot and the giveaways.
user_states: Stores the current state of each user in the giveaway creation process.
active_giveaways: Stores the data of active giveaways. The key is the message ID of the giveaway.
participants: Stores the participants of each giveaway. The key is the message ID of the giveaway.
"""
STATE_WAIT_TITLE = 1
STATE_WAIT_GIFT = 2
STATE_WAIT_DURATION = 3
STATE_WAIT_CUSTOM_DURATION = 6
STATE_WAIT_PLACE = 4
STATE_WAIT_INFO = 5
STATE_WAIT_KEY = 7

@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    if message.from_user.last_name:
        user_name += f" {message.from_user.last_name}"

    print(f"🚀 User {user_name} ({user_id}) started the bot")

    # Delete user's message for security
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

    # Check if user already has a valid key
    if db.validate_user_key(user_id):
        existing_key = db.get_user_key(user_id)
        sent_msg = bot.send_message(message.chat.id,
            f"✅ Selamat datang kembali ke Bot Giveaway HackHub!\n\n"
            f"🔑 **Kunci anda yang masih aktif:**\n"
            f"`{existing_key}`\n\n"
            f"⏰ Kunci ini akan tamat dalam 24 jam dari masa dijana.\n\n"
            f"📚 **Arahan penting:**\n"
            f"• /create – Buat giveaway baharu\n"
            f"• /templates – Gunakan template giveaway\n"
            f"• /list – Senarai giveaway aktif\n"
            f"• /listjoin – Senarai penyertaan giveaway\n"
            f"• /points – Semak mata anda\n"
            f"• /leaderboard – Papan pendahulu\n"
            f"• /end [message_id] – Tamatkan giveaway (jika unlimited)\n"
            f"• /mykey – Semak kunci semasa\n\n"
            f"🪙 **Sistem Mata:**\n"
            f"• +10 mata - Sertai giveaway\n"
            f"• +100 mata - Menang giveaway\n\n"
            f"💡 Gunakan /create untuk mula sekarang!",
            parse_mode="Markdown"
        )
    else:
        # Generate new key
        new_key = db.generate_user_key(user_id, user_name)
        sent_msg = bot.send_message(message.chat.id,
            f"🎉 Selamat datang ke Bot Giveaway HackHub!\n\n"
            f"🔑 **Kunci 24 jam anda:**\n"
            f"`{new_key}`\n\n"
            f"⚠️ **PENTING:** Simpan kunci ini dengan selamat!\n"
            f"• Kunci ini akan tamat dalam 24 jam\n"
            f"• Anda memerlukan kunci ini untuk menggunakan bot\n"
            f"• Kunci disimpan walaupun bot dimatikan\n\n"
            f"📚 **Arahan penting:**\n"
            f"• /create – Buat giveaway baharu\n"
            f"• /templates – Gunakan template giveaway\n"
            f"• /list – Senarai giveaway aktif\n"
            f"• /listjoin – Senarai penyertaan giveaway\n"
            f"• /points – Semak mata anda\n"
            f"• /leaderboard – Papan pendahulu\n"
            f"• /end [message_id] – Tamatkan giveaway (jika unlimited)\n"
            f"• /mykey – Semak kunci semasa\n\n"
            f"🪙 **Sistem Mata:**\n"
            f"• +10 mata - Sertai giveaway\n"
            f"• +100 mata - Menang giveaway\n\n"
            f"💡 Gunakan /create untuk mula sekarang!",
            parse_mode="Markdown"
        )

    # Delete this message after 30 seconds for security
    Timer(30, lambda: delete_message_safe(message.chat.id, sent_msg.message_id)).start()

@bot.message_handler(commands=['getkey'])
def handle_getkey(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    if message.from_user.last_name:
        user_name += f" {message.from_user.last_name}"

    print(f"🔑 User {user_name} ({user_id}) requested new key")

    # Delete user's message for security
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

    # Generate new key (overwrite existing one)
    new_key = db.generate_user_key(user_id, user_name)
    sent_msg = bot.send_message(message.chat.id,
        f"🔑 **Kunci baharu anda:**\n"
        f"`{new_key}`\n\n"
        f"⚠️ **PENTING:** Simpan kunci ini dengan selamat!\n"
        f"• Kunci ini akan tamat dalam 24 jam\n"
        f"• Anda memerlukan kunci ini untuk menggunakan bot\n"
        f"• Kunci lama (jika ada) telah diganti\n\n"
        f"📝 **Untuk menggunakan bot:** Hantar kunci anda kepada saya",
        parse_mode="Markdown"
    )

    # Delete this message after 30 seconds for security
    Timer(30, lambda: delete_message_safe(message.chat.id, sent_msg.message_id)).start()

def delete_message_safe(chat_id, message_id):
    try:
        bot.delete_message(chat_id, message_id)
    except:
        pass

@bot.message_handler(func=lambda message: message.text and not message.text.startswith('/') and message.from_user.id not in user_states and not db.validate_user_key(message.from_user.id))
def handle_key_verification(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    if message.from_user.last_name:
        user_name += f" {message.from_user.last_name}"

    provided_key = message.text.strip()

    # Delete user's message for security
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

    print(f"🔑 User {user_name} ({user_id}) trying to verify key")

    # Check if this key exists in database
    key_found = False
    for stored_user_id, key_data in db.data.get('user_keys', {}).items():
        if key_data.get('key') == provided_key and key_data.get('is_active', False):
            from datetime import datetime
            try:
                expiry_time = datetime.fromisoformat(key_data['expires_at'])
                if datetime.now() <= expiry_time:
                    # Valid key found, activate it for this user
                    if str(user_id) != stored_user_id:
                        # Transfer key to current user
                        db.data['user_keys'][str(user_id)] = key_data.copy()
                        db.data['user_keys'][str(user_id)]['user_name'] = user_name
                        # Deactivate old key
                        if stored_user_id in db.data['user_keys']:
                            del db.data['user_keys'][stored_user_id]
                        db.save_data()
                    key_found = True
                    break
            except:
                continue

    if key_found:
        sent_msg = bot.send_message(message.chat.id,
            f"✅ **Kunci berjaya disahkan!**\n\n"
            f"🎉 Selamat datang ke Bot Giveaway HackHub!\n\n"
            f"📚 **Arahan tersedia:**\n"
            f"• /create – Buat giveaway baharu\n"
            f"• /templates – Gunakan template giveaway\n"
            f"• /list – Senarai giveaway aktif\n"
            f"• /listjoin – Senarai penyertaan giveaway\n"
            f"• /points – Semak mata anda\n"
            f"• /leaderboard – Papan pendahulu\n"
            f"• /end [message_id] – Tamatkan giveaway (jika unlimited)\n"
            f"• /mykey – Semak kunci semasa\n\n"
            f"🪙 **Sistem Mata:**\n"
            f"• +10 mata - Sertai giveaway\n"
            f"• +100 mata - Menang giveaway\n\n"
            f"💡 Gunakan /create untuk mula sekarang!",
            parse_mode="Markdown"
        )
        print(f"✅ User {user_name} ({user_id}) successfully verified key")
    else:
        sent_msg = bot.send_message(message.chat.id,
            f"❌ **Kunci tidak sah atau telah tamat!**\n\n"
            f"🔄 Gunakan /getkey untuk mendapatkan kunci baharu.\n"
            f"⏰ Setiap kunci adalah sah selama 24 jam.\n\n"
            f"📝 **Untuk mendapatkan kunci:** Hantar /getkey",
            parse_mode="Markdown"
        )
        print(f"❌ User {user_name} ({user_id}) provided invalid key")

    # Delete this message after 10 seconds
    Timer(10, lambda: delete_message_safe(message.chat.id, sent_msg.message_id)).start()

@bot.message_handler(commands=['create'])
def handle_create(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    # Delete user's command for security
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

    # Check if user has valid key
    if not db.validate_user_key(user_id):
        sent_msg = bot.send_message(message.chat.id,
            "❌ **Kunci tidak sah atau telah tamat!**\n\n"
            "🔄 Gunakan /getkey untuk mendapatkan kunci baharu.\n"
            "⏰ Setiap kunci adalah sah selama 24 jam.\n\n"
            "📝 **Untuk mendapatkan kunci:** Hantar /getkey",
            parse_mode="Markdown"
        )
        Timer(10, lambda: delete_message_safe(message.chat.id, sent_msg.message_id)).start()
        return

    print(f"📝 User {user_name} ({user_id}) started creating giveaway")
    user_states[user_id] = {'step': STATE_WAIT_TITLE, 'data': {}}
    bot.send_message(message.chat.id, "📝 Masukkan tajuk giveaway:", parse_mode="Markdown")

@bot.message_handler(commands=['list'])
def handle_list(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    # Delete user's command for security
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

    # Check if user has valid key
    if not db.validate_user_key(user_id):
        sent_msg = bot.send_message(message.chat.id,
            "❌ **Kunci tidak sah atau telah tamat!**\n\n"
            "🔄 Gunakan /getkey untuk mendapatkan kunci baharu.\n"
            "⏰ Setiap kunci adalah sah selama 24 jam.\n\n"
            "📝 **Untuk mendapatkan kunci:** Hantar /getkey",
            parse_mode="Markdown"
        )
        Timer(10, lambda: delete_message_safe(message.chat.id, sent_msg.message_id)).start()
        return

    print(f"📋 User {user_name} ({user_id}) requested giveaway list")
    if not active_giveaways:
        bot.send_message(message.chat.id, "❌ Tiada giveaway aktif.")
        return

    text = "📋 *Senarai Giveaway Aktif:*\n\n"
    for mid, g in active_giveaways.items():
        title = g.get('title', 'Unknown')
        gift = g.get('gift', 'Unknown')
        if g.get('end_time'):
            remaining = max(0, int(g['end_time'] - time.time()))
            if remaining > 0:
                remaining_text = f"{remaining} saat"
            else:
                remaining_text = "⏰ Tamat"
        else:
            remaining_text = "♾️ Unlimited"
        text += f"• *{title}* – 🎁 {gift} – ⏳ {remaining_text}\n"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['listjoin'])
def handle_listjoin(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    # Delete user's command for security
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

    # Check if user has valid key
    if not db.validate_user_key(user_id):
        sent_msg = bot.send_message(message.chat.id,
            "❌ **Kunci tidak sah atau telah tamat!**\n\n"
            "🔄 Gunakan /getkey untuk mendapatkan kunci baharu.\n"
            "⏰ Setiap kunci adalah sah selama 24 jam.\n\n"
            "📝 **Untuk mendapatkan kunci:** Hantar /getkey",
            parse_mode="Markdown"
        )
        Timer(10, lambda: delete_message_safe(message.chat.id, sent_msg.message_id)).start()
        return

    print(f"👥 User {user_name} ({user_id}) requested participants list")
    if not active_giveaways:
        bot.send_message(message.chat.id, "❌ Tiada giveaway aktif.")
        return

    text = "👥 *Senarai Penyertaan Giveaway:*\n\n"
    for mid, g in active_giveaways.items():
        title = g.get('title', 'Unknown')
        participant_count = len(participants.get(mid, set()))
        text += f"• *{title}* – 👤 {participant_count} penyertaan\n"

    if len(text.strip()) == len("👥 *Senarai Penyertaan Giveaway:*"):
        text += "❌ Tiada penyertaan pada giveaway aktif."

    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['mykey'])
def handle_mykey(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    # Delete user's command for security
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

    print(f"🔑 User {user_name} ({user_id}) checking their key")

    if db.validate_user_key(user_id):
        user_key = db.get_user_key(user_id)
        key_data = db.data['user_keys'][str(user_id)]

        from datetime import datetime
        expiry_time = datetime.fromisoformat(key_data['expires_at'])
        generated_time = datetime.fromisoformat(key_data['generated_at'])

        time_remaining = expiry_time - datetime.now()
        hours_remaining = int(time_remaining.total_seconds() // 3600)
        minutes_remaining = int((time_remaining.total_seconds() % 3600) // 60)

        sent_msg = bot.send_message(message.chat.id,
            f"🔑 **Kunci anda yang aktif:**\n"
            f"`{user_key}`\n\n"
            f"📅 **Dijana pada:** {generated_time.strftime('%d/%m/%Y %H:%M:%S')}\n"
            f"⏰ **Masa tinggal:** {hours_remaining} jam {minutes_remaining} minit\n"
            f"🕐 **Tamat pada:** {expiry_time.strftime('%d/%m/%Y %H:%M:%S')}\n\n"
            f"✅ Kunci masih aktif dan boleh digunakan!",
            parse_mode="Markdown"
        )
        # Delete this message after 20 seconds for security
        Timer(20, lambda: delete_message_safe(message.chat.id, sent_msg.message_id)).start()
    else:
        sent_msg = bot.send_message(message.chat.id,
            "❌ **Tiada kunci aktif atau kunci telah tamat!**\n\n"
            "🔄 Gunakan /getkey untuk mendapatkan kunci baharu.\n"
            "⏰ Setiap kunci adalah sah selama 24 jam.\n\n"
            "📝 **Untuk mendapatkan kunci:** Hantar /getkey",
            parse_mode="Markdown"
        )
        Timer(10, lambda: delete_message_safe(message.chat.id, sent_msg.message_id)).start()

@bot.message_handler(commands=['end'])
def handle_end(message):
    print(f"🛑 User {message.from_user.first_name} ({message.from_user.id}) trying to end giveaway")
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Format salah. Guna: /end [message_id]")
            return

        msg_id = int(parts[1])
        if msg_id in active_giveaways:
            end_giveaway(msg_id, manual=True)
            bot.reply_to(message, f"✅ Giveaway {msg_id} ditamatkan.")
        else:
            bot.reply_to(message, f"❌ Giveaway {msg_id} tidak dijumpai.")
    except ValueError:
        bot.reply_to(message, "❌ Message ID mesti nombor. Guna: /end [message_id]")
    except Exception as e:
        print(f"❌ Error ending giveaway: {e}")
        bot.reply_to(message, "❌ Ralat berlaku semasa menamatkan giveaway.")

@bot.message_handler(func=lambda m: m.from_user.id in user_states)
def handle_state(message):
    uid = message.from_user.id
    state = user_states[uid]
    data = state['data']

    print(f"📝 Processing step {state['step']} for user {message.from_user.first_name}")

    if state['step'] == STATE_WAIT_TITLE:
        data['title'] = message.text
        state['step'] = STATE_WAIT_GIFT
        bot.send_message(message.chat.id, "🎁 Masukkan hadiah:")

    elif state['step'] == STATE_WAIT_GIFT:
        data['gift'] = message.text
        state['step'] = STATE_WAIT_DURATION
        markup = InlineKeyboardMarkup()
        durations = [1, 5, 10, 0, -1]  # -1 for custom
        for m in durations:
            if m == -1:
                label = "⏰ Custom Time"
            elif m == 0:
                label = "♾️ Unlimited"
            else:
                label = f"{m} minit"
            markup.add(InlineKeyboardButton(label, callback_data=f"duration:{m}"))
        bot.send_message(message.chat.id, "⏳ Pilih tempoh giveaway:", reply_markup=markup)

    elif state['step'] == STATE_WAIT_PLACE:
        data['place'] = message.text
        state['step'] = STATE_WAIT_INFO
        bot.send_message(message.chat.id, "📄 Masukkan info tambahan (atau '-' jika tiada):")

    elif state['step'] == STATE_WAIT_CUSTOM_DURATION:
        try:
            custom_minutes = int(message.text)
            if custom_minutes <= 0:
                bot.send_message(message.chat.id, "❌ Masukkan nombor yang lebih besar dari 0:")
                return
            data['duration'] = custom_minutes
            state['step'] = STATE_WAIT_PLACE
            bot.send_message(message.chat.id, f"✅ Tempoh ditetapkan: {custom_minutes} minit\n📍 Masukkan lokasi (atau '-' jika tiada):")
        except ValueError:
            bot.send_message(message.chat.id, "❌ Masukkan nombor sahaja (dalam minit):")
        return

    elif state['step'] == STATE_WAIT_INFO:
        data['info'] = message.text
        state['step'] = None

        # Store creator's message IDs to preserve them
        creator_id = message.from_user.id

        # Delete all bot messages and setup messages (but keep member messages)
        try:
            # Delete the current info message
            bot.delete_message(message.chat.id, message.message_id)

            # Delete previous messages in the creation flow (bot messages and user setup messages)
            for i in range(1, 10):  # Check more messages to be thorough
                try:
                    msg_to_check = message.message_id - i
                    # Try to delete - if it's a member's regular message, it might fail and that's OK
                    bot.delete_message(message.chat.id, msg_to_check)
                except:
                    # Message couldn't be deleted (might be member message or already deleted)
                    pass
        except Exception as e:
            print(f"⚠️ Could not delete some messages: {e}")

        send_giveaway(message.chat.id, data)
        del user_states[uid]
        print(f"🗑️ Deleted setup messages for giveaway creation (preserved member messages)")

@bot.callback_query_handler(func=lambda call: call.data.startswith("duration:"))
def handle_duration(call):
    uid = call.from_user.id
    print(f"⏰ User {call.from_user.first_name} selected duration")

    if uid not in user_states:
        bot.answer_callback_query(call.id, "❌ Session expired. Mulakan semula dengan /create")
        return

    try:
        duration = int(call.data.split(":")[1])
        if duration == -1:  # Custom duration
            user_states[uid]['step'] = STATE_WAIT_CUSTOM_DURATION
            bot.answer_callback_query(call.id, "✅ Custom time dipilih!")
            bot.send_message(call.message.chat.id, "⏰ Masukkan tempoh dalam minit (contoh: 30, 60, 120):")
        else:
            user_states[uid]['data']['duration'] = duration
            user_states[uid]['step'] = STATE_WAIT_PLACE
            bot.answer_callback_query(call.id, "✅ Tempoh dipilih!")
            bot.send_message(call.message.chat.id, "📍 Masukkan lokasi (atau '-' jika tiada):")
    except Exception as e:
        print(f"❌ Error handling duration: {e}")
        bot.answer_callback_query(call.id, "❌ Ralat berlaku.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("join:"))
def handle_join(call):
    print(f"🔄 User {call.from_user.first_name} ({call.from_user.id}) trying to join giveaway")

    try:
        msg_id_str = call.data.split(":")[1]
        msg_id = int(msg_id_str)
    except (ValueError, IndexError) as e:
        print(f"❌ Invalid callback data: {call.data}, error: {e}")
        bot.answer_callback_query(call.id, "❌ Data tidak sah.", show_alert=True)
        return

    if msg_id not in participants:
        participants[msg_id] = set()

    user = call.from_user
    if user.id in participants[msg_id]:
        print(f"❌ User {user.first_name} already joined giveaway {msg_id}")
        bot.answer_callback_query(call.id, "❗ Anda sudah sertai.", show_alert=True)
        return

    participants[msg_id].add(user.id)

    # Save to database immediately
    user_name = user.first_name
    if user.last_name:
        user_name += f" {user.last_name}"
    db.add_participant(msg_id, user.id, user_name)

    print(f"✅ User {user.first_name} successfully joined giveaway {msg_id}. Total participants: {len(participants[msg_id])}")
    bot.answer_callback_query(call.id, "✅ Anda telah sertai giveaway!")

    # Update the message to show current participant count
    try:
        current_count = len(participants[msg_id])
        giveaway_data = active_giveaways.get(msg_id, {})

        if giveaway_data:
            duration_text = "♾️ Unlimited" if giveaway_data.get('duration', 0) == 0 else f"{giveaway_data.get('duration', 0)} minit"
            updated_text = (
                f"🎉 *GIVEAWAY BERMULA!*\n\n"
                f"📌 *Tajuk:* {giveaway_data.get('title', 'N/A')}\n"
                f"🎁 *Hadiah:* {giveaway_data.get('gift', 'N/A')}\n"
                f"⏳ *Tempoh:* {duration_text}\n"
                f"📍 *Lokasi:* {giveaway_data.get('place', '-') or '-'}\n"
                f"📝 *Info:* {giveaway_data.get('info', '-') or '-'}\n"
                f"👥 *Penyertaan:* {current_count} orang\n\n"
                f"🔽 Tekan butang di bawah untuk JOIN!"
            )
            bot.edit_message_text(updated_text, call.message.chat.id, msg_id, parse_mode="Markdown", reply_markup=call.message.reply_markup)
    except Exception as e:
        print(f"❌ Error updating message: {e}")

def send_giveaway(chat_id, data):
    print(f"🚀 Creating giveaway: {data['title']}")

    duration_text = "♾️ Unlimited" if data['duration'] == 0 else f"{data['duration']} minit"

    msg = bot.send_message(chat_id, (
        f"🎉 *GIVEAWAY BERMULA!*\n\n"
        f"📌 *Tajuk:* {data['title']}\n"
        f"🎁 *Hadiah:* {data['gift']}\n"
        f"⏳ *Tempoh:* {duration_text}\n"
        f"📍 *Lokasi:* {data.get('place', '-') or '-'}\n"
        f"📝 *Info:* {data.get('info', '-') or '-'}\n"
        f"👥 *Penyertaan:* 0 orang\n\n"
        f"🔽 Tekan butang di bawah untuk JOIN!"
    ), parse_mode="Markdown")

    msg_id = msg.message_id

    # Create the button with correct callback data
    markup = InlineKeyboardMarkup()
    join_button = InlineKeyboardButton("✅ Saya Nak Join!", callback_data=f"join:{msg_id}")
    markup.add(join_button)

    # Update the message with the button
    bot.edit_message_reply_markup(chat_id, msg_id, reply_markup=markup)

    end_time = time.time() + data['duration'] * 60 if data['duration'] > 0 else None
    active_giveaways[msg_id] = data.copy()
    active_giveaways[msg_id]['end_time'] = end_time
    active_giveaways[msg_id]['chat_id'] = chat_id  # Store chat_id for later use
    participants[msg_id] = set()

    # Save to database immediately
    giveaway_data_to_save = active_giveaways[msg_id].copy()
    db.add_giveaway(msg_id, giveaway_data_to_save)

    print(f"📊 Giveaway {msg_id} created successfully. Duration: {data['duration']} minutes")

    if data['duration'] > 0:
        Timer(data['duration'] * 60, end_giveaway, args=[msg_id]).start()
        print(f"⏰ Timer set for {data['duration']} minutes for giveaway {msg_id}")



# Error handler
@bot.middleware_handler(update_types=['message'])
def modify_message(bot_instance, message):
    print(f"📨 Received message from {message.from_user.first_name}: {message.text[:50] if message.text else 'Non-text message'}")

print("🤖 Bot starting...")

# Start web dashboard with integrated keep alive functionality
web_thread = Thread(target=start_web_dashboard)
web_thread.daemon = True
web_thread.start()
print("🌐 Web dashboard started with integrated keep alive service")

# Add delay to ensure services are ready
time.sleep(2)

# Key system functionality integrated into web dashboard
print("🔑 Key system integrated into web dashboard")

# Cleanup expired keys on startup
db.cleanup_expired_keys()

# Schedule periodic cleanup of expired keys
def periodic_cleanup():
    while True:
        time.sleep(3600)  # Run every hour
        db.cleanup_expired_keys()

cleanup_thread = Thread(target=periodic_cleanup)
cleanup_thread.daemon = True
cleanup_thread.start()
print("🧹 Periodic key cleanup started")

import signal

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print(f"\n🛑 Received signal {signum}, shutting down bot gracefully...")
    release_lock(lock_fd)
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

try:
    print("🚀 Bot polling started successfully!")
    bot.polling(none_stop=True, interval=0, timeout=20)
except KeyboardInterrupt:
    print("\n🛑 Bot stopped by user")
except Exception as e:
    print(f"❌ Bot polling error: {e}")
    print("🔄 Attempting to restart bot...")
    time.sleep(5)
    try:
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e2:
        print(f"❌ Failed to restart bot: {e2}")
finally:
    release_lock(lock_fd)