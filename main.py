import requests
import telebot
import sqlite3
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")


def getCodewars(user):
    url = f"https://www.codewars.com/api/v1/users/{user}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        return None

def firstLaunch():
    connection = sqlite3.connect('users.db')
    cursor = connection.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codewarsUsername TEXT NOT NULL UNIQUE,
        telegramID INTEGER NOT NULL UNIQUE,
        registrationHonor INTEGER NOT NULL,
        lastUpdated TEXT NOT NULL,
        lastHonor INTEGER NOT NULL,
        registrationDate TEXT NOT NULL
    )
    ''')
    connection.commit()
    connection.close()

def registerUser(userID, codewarsUsername, honor):
    current_time = datetime.now().strftime('%Y-%m-%d-%H-%M')
    connection = sqlite3.connect('users.db')
    cursor = connection.cursor()
    cursor.execute('''
    INSERT INTO users (codewarsUsername, telegramID, registrationHonor, lastUpdated, lastHonor, registrationDate) 
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (codewarsUsername, userID, honor, current_time, honor, current_time))
    connection.commit()
    connection.close()

def isUserRegistered(userID):
    connection = sqlite3.connect('users.db')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM users WHERE telegramID = ?', (userID,))
    row = cursor.fetchone()
    connection.close()
    return row is not None

def overwriteUser(userID, codewarsUsername):
    connection = sqlite3.connect('users.db')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM users WHERE telegramID = ?', (userID,))
    row = cursor.fetchone()
    if row:
        cursor.execute('UPDATE users SET codewarsUsername = ? WHERE telegramID = ?', (codewarsUsername, userID))
        connection.commit()
        connection.close()
        return True
    connection.close()
    return False

def getDefaultMessageData(message):
    userid = message.from_user.id
    if not message.text:
        return userid, None
    parts = message.text.split(maxsplit=1)
    return userid, parts[1] if len(parts) == 2 else None

def getAllUsers():
    connection = sqlite3.connect('users.db')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM users')
    rows = cursor.fetchall()
    connection.close()
    return rows

def updateUser(userID, lastHonor):
    current_time = datetime.now().strftime('%Y-%m-%d-%H-%M')
    connection = sqlite3.connect('users.db')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM users WHERE telegramID = ?', (userID,))
    row = cursor.fetchone()
    if not row:
        connection.close()
        return False
    cursor.execute('''
    UPDATE users 
    SET lastUpdated = ?, lastHonor = ? 
    WHERE telegramID = ?
    ''', (current_time, lastHonor, userID))
    connection.commit()
    connection.close()
    return True

def calculateHonorChange(initial_honor, new_honor):
    return new_honor - initial_honor

bot = telebot.TeleBot(bot_token)
@bot.message_handler(commands=['register'])
def register_handler(message):
    chat_id = message.chat.id

    userid, codewarsUsername = getDefaultMessageData(message)
    if not codewarsUsername:
        bot.send_message(
            chat_id,
            "❌ *Invalid Data*\n\nUsage: `/register <CodewarsUsername>`",
            parse_mode="Markdown"
        )
        return

    if isUserRegistered(userid):
        bot.send_message(
            chat_id,
            "⚠️ You are already registered! Use `/overwrite` if you want to update your username.",
            parse_mode="Markdown"
        )
        return

    codewarsUserRequest = getCodewars(codewarsUsername)
    if codewarsUserRequest and codewarsUserRequest.status_code == 200:
        codewarsData = codewarsUserRequest.json()
        registerUser(userid, codewarsUsername, codewarsData['honor'])
        bot.send_message(
            chat_id,
            f"✅ *Success!*\n\nYou are now registered as `{codewarsUsername}`!",
            parse_mode="Markdown"
        )
    else:
        bot.send_message(
            chat_id,
            "❌ Failed to fetch Codewars data. Please check the username.",
            parse_mode="Markdown"
        )

@bot.message_handler(commands=['profile'])
def profile_handler(message):
    chat_id = message.chat.id

    userid = message.from_user.id
    if not isUserRegistered(userid):
        bot.send_message(
            chat_id,
            "❌ You are not registered. Use `/register` to sign up first.",
            parse_mode="Markdown"
        )
        return

    connection = sqlite3.connect('users.db')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM users WHERE telegramID = ?', (userid,))
    row = cursor.fetchone()
    connection.close()

    if not row:
        bot.send_message(
            chat_id,
            "❌ You are not registered. Use `/register` to sign up first.",
            parse_mode="Markdown"
        )
        return

    registration_date = datetime.strptime(row[6], '%Y-%m-%d-%H-%M')
    last_updated = datetime.strptime(row[4], '%Y-%m-%d-%H-%M')
    time_since_last_update = datetime.now() - last_updated
    codewarsUsername = row[1]
    codewarsUserRequest = getCodewars(codewarsUsername)
    if codewarsUserRequest and codewarsUserRequest.status_code == 200:
        codewarsData = codewarsUserRequest.json()
        current_honor = codewarsData['honor']
        earned_24h = calculateHonorChange(row[5], current_honor) if time_since_last_update <= timedelta(days=1) else 0
        earned_7d = calculateHonorChange(row[5], current_honor) if time_since_last_update <= timedelta(days=7) else 0
        earned_month = calculateHonorChange(row[5], current_honor) if time_since_last_update <= timedelta(days=30) else 0
        profile_message = (
            f"👤 *Your Profile:*\n\n"
            f"🆔 *ID:* `{row[0]}`\n"
            f"📝 *Codewars Username:* `{row[1]}`\n"
            f"📅 *Registration Date:* {registration_date.strftime('%Y-%m-%d %H:%M')}\n"
            f"⏱️ *Last Updated:* {last_updated.strftime('%Y-%m-%d %H:%M')}\n"
            f"🏅 *Registration Honor:* `{row[3]}`\n"
            f"🔄 *Honor Earned (24h):* `{earned_24h}`\n"
            f"🔄 *Honor Earned (7d):* `{earned_7d}`\n"
            f"🔄 *Honor Earned (Month):* `{earned_month}`\n"
        )
        bot.send_message(chat_id, profile_message, parse_mode="Markdown")
    else:
        bot.send_message(
            chat_id,
            "❌ Failed to fetch Codewars data. Please check the username.",
            parse_mode="Markdown"
        )

@bot.message_handler(commands=['users'])
def users_handler(message):
    chat_id = message.chat.id

    rows = getAllUsers()
    if not rows:
        bot.send_message(chat_id, "❌ No users registered yet.", parse_mode="Markdown")
        return

    leaderboard_30d = []
    leaderboard_7d = []
    leaderboard_1d = []

    for row in rows:
        codewarsUsername = row[1]
        lastHonor = row[5]
        lastUpdated = datetime.strptime(row[4], '%Y-%m-%d-%H-%M')
        time_since_last_update = datetime.now() - lastUpdated

        codewarsUserRequest = getCodewars(codewarsUsername)
        if codewarsUserRequest and codewarsUserRequest.status_code == 200:
            codewarsData = codewarsUserRequest.json()
            currentHonor = codewarsData['honor']

            if time_since_last_update <= timedelta(days=30):
                honor_30d = calculateHonorChange(lastHonor, currentHonor)
                leaderboard_30d.append((codewarsUsername, honor_30d))

            if time_since_last_update <= timedelta(days=7):
                honor_7d = calculateHonorChange(lastHonor, currentHonor)
                leaderboard_7d.append((codewarsUsername, honor_7d))

            if time_since_last_update <= timedelta(days=1):
                honor_1d = calculateHonorChange(lastHonor, currentHonor)
                leaderboard_1d.append((codewarsUsername, honor_1d))

    leaderboard_30d = sorted(leaderboard_30d, key=lambda x: x[1], reverse=True)[:3]
    leaderboard_7d = sorted(leaderboard_7d, key=lambda x: x[1], reverse=True)[:3]
    leaderboard_1d = sorted(leaderboard_1d, key=lambda x: x[1], reverse=True)[:3]

    def format_leaderboard(title, leaderboard):
        message = f"🏆 *{title}*\n"
        for i, (username, honor) in enumerate(leaderboard, start=1):
            message += f"   {i}. `{username}` - {honor} honor\n"
        return message or f"   No data available.\n"

    leaderboard_message = (
        "📊 *Leaderboard:*\n\n"
        f"{format_leaderboard('30-Day Top 3', leaderboard_30d)}\n"
        f"{format_leaderboard('7-Day Top 3', leaderboard_7d)}\n"
        f"{format_leaderboard('1-Day Top 3', leaderboard_1d)}"
    )

    bot.send_message(chat_id, leaderboard_message, parse_mode="Markdown")

@bot.message_handler(commands=['update'])
def update_handler(message):
    chat_id = message.chat.id

    userid = message.from_user.id
    if not isUserRegistered(userid):
        bot.send_message(
            chat_id,
            "❌ You are not registered. Use `/register` to sign up first.",
            parse_mode="Markdown"
        )
        return

    connection = sqlite3.connect('users.db')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM users WHERE telegramID = ?', (userid,))
    row = cursor.fetchone()
    connection.close()

    if not row:
        bot.send_message(
            chat_id,
            "❌ You are not registered. Use `/register` to sign up first.",
            parse_mode="Markdown"
        )
        return

    codewarsUsername = row[1]
    lastHonor = row[5]

    codewarsUserRequest = getCodewars(codewarsUsername)
    if codewarsUserRequest and codewarsUserRequest.status_code == 200:
        codewarsData = codewarsUserRequest.json()
        currentHonor = codewarsData['honor']

        honorChange = calculateHonorChange(lastHonor, currentHonor)
        updateSuccess = updateUser(userid, currentHonor)

        if updateSuccess:
            bot.send_message(
                chat_id,
                (
                    f"✅ *Update Successful!*\n\n"
                    f"👤 *Codewars Username:* `{codewarsUsername}`\n"
                    f"🏅 *Previous Honor:* `{lastHonor}`\n"
                    f"🏅 *Current Honor:* `{currentHonor}`\n"
                    f"🔄 *Honor Change:* `{honorChange}`"
                ),
                parse_mode="Markdown"
            )
        else:
            bot.send_message(
                chat_id,
                "❌ Failed to update your honor in the database.",
                parse_mode="Markdown"
            )
    else:
        bot.send_message(
            chat_id,
            "❌ Failed to fetch Codewars data. Please check your username.",
            parse_mode="Markdown"
        )

@bot.message_handler(commands=['overwrite'])
def overwrite_handler(message):
    chat_id = message.chat.id

    userid, codewarsUsername = getDefaultMessageData(message)
    if not codewarsUsername:
        bot.send_message(
            chat_id,
            "❌ *Invalid Data*\n\nUsage: `/overwrite <newCodewarsUsername>`",
            parse_mode="Markdown"
        )
        return

    if not isUserRegistered(userid):
        bot.send_message(
            chat_id,
            "❌ You are not registered. Use `/register` to sign up first.",
            parse_mode="Markdown"
        )
        return

    codewarsUserRequest = getCodewars(codewarsUsername)
    if codewarsUserRequest and codewarsUserRequest.status_code == 200:
        success = overwriteUser(userid, codewarsUsername)
        if success:
            bot.send_message(
                chat_id,
                f"✅ *Success!*\n\nYour Codewars username has been updated to `{codewarsUsername}`!",
                parse_mode="Markdown"
            )
        else:
            bot.send_message(
                chat_id,
                "❌ Failed to update your username. Please try again.",
                parse_mode="Markdown"
            )
    else:
        bot.send_message(
            chat_id,
            "❌ Failed to fetch Codewars data. Please check the new username.",
            parse_mode="Markdown"
        )

if __name__ == "__main__":
    firstLaunch()
    bot.get_updates(offset=-1)
    bot.polling()

