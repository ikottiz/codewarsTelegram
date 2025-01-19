# Codewars-Telegram Bot

A Telegram bot to track and manage Codewars profiles, including registration, updates, and leaderboards.

## Guide

### 1. Install Dependencies:

- Clone or download this repository to a directory of your choice.
- Install dependencies by running the following command:
  ```bash
  pip install -r requirements.txt
  ```
  Alternatively, install dependencies manually:
  ```bash
  pip install requests pyTelegramBotAPI python-dotenv
  ```

### 2. Getting Credentials:

#### Telegram:

1. Visit [Telegram Web](https://web.telegram.org) or use the Telegram app.
2. Use [@BotFather](https://t.me/botfather) to create a new bot and obtain the bot token.
   - Use the `/newbot` command and follow the instructions to get your bot token.
3. Copy the bot token and update it in the `.env` file:
   ```env
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   ```

### 3. Setting Up the Database

- The bot uses an SQLite database to store user data.
- Run the script once to create the `users.db` database and initialize the schema.

### 4. Launching

1. Run the bot using the following command:
   ```bash
   python bot.py
   ```
2. Voilà! Your bot is ready to use.

### 5. Usage

#### Commands:

- **`/register <CodewarsUsername>`**
  Register your Codewars username to track your progress.
  
- **`/profile`**
  View your Codewars profile with honor stats and achievements.
  
- **`/users`**
  View the leaderboard for top performers over different time periods.
  
- **`/update`**
  Update your Codewars stats manually.
  
- **`/overwrite <NewCodewarsUsername>`**
  Change your registered Codewars username.
