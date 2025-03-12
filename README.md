# Ogiroid - The Most Handsome Discord Bot! 😎

---

![Ogiroid Logo](https://media.discordapp.net/attachments/985729550732394536/1002138392554897479/Ogiroid.png?width=1440&height=583)

---

## **📌 Introduction**
Ogiroid is a **multipurpose** Discord bot (who is very handsome 😋😋) developed for the YouTuber, [Lewis Menelaws](https://www.youtube.com/c/CodingwithLewis)' Discord server. The bot comes with various features, including **moderation, music, leveling, and fun commands** to enhance your Discord experience!

---

## **📖 Table of Contents**
1. [Bot Development Information](#-bot-development-information)
2. [Features](#-features)
3. [Installation Guide](#-installation-guide)
4. [Usage](#-usage)
5. [Contributing](#-contributing)
6. [Changelog](#-changelog)

---

## **🛠 Bot Development Information**
- **Based on**: [edoC](https://github.com/jasonlovesdoggo/edoc)
- **Written in**: Python 🐍
- **Made using**: [Disnake](https://disnake.dev/) (a fork of discord.py)
- **Python Version**: 3.8+
- **Current Release**: **v2.5**
- **License**: MIT

### **Main Contributors/Developers:**
- [HarryDaDev](https://github.com/ImmaHarry)
- [FreebieII](https://github.com/FreebieII)
- [JasonLovesDoggo](https://github.com/JasonLovesDoggo)
- [Levani Vashadze](https://github.com/LevaniVashadze)

---

## **🚀 Features**
✅ **Moderation** (Kick, Ban, Mute, Timeout, etc.)
✅ **Music Commands** (Play, Pause, Skip, Queue)
✅ **Leveling System** (XP tracking, leaderboard, level roles)
✅ **Custom Role Management** (Create & assign roles automatically)
✅ **Fun Commands** (8Ball, Memes, Jokes, and more!)
✅ **Economy System** (Work, Bank, Shop, and Gambling)
✅ **Integration with PostgreSQL & SQLAlchemy ORM**
✅ **Starboard System** (Track popular messages)
✅ **Dashboard** (Web-based bot management - *coming soon!*)

---

## **📥 Installation Guide**
### **1️⃣ Prerequisites**
Ensure you have the following installed:
- Python 3.8+
- `pip`
- PostgreSQL (if running locally)
- `ffmpeg` (for music functionality)

### **2️⃣ Clone the Repository**
```sh
$ git clone https://github.com/LewisProjects/Ogiroid.git
$ cd Ogiroid
```

### **3️⃣ Install Dependencies**
```sh
$ pip install -r requirements.txt
```

### **4️⃣ Configure the Bot**
Rename `.env.example` to `.env` and add your bot token & database credentials:
```env
BOT_TOKEN=your_token_here
DATABASE_URL=your_postgresql_connection_string
```

### **5️⃣ Run the Bot**
```sh
$ python main.py
```
---

## **📌 Usage**
**Basic Commands:**
```
/play [song_name] - Play music
/ban [user] - Ban a user
/meme - Get a random meme
/leaderboard - Show XP leaderboard
/xp [user] - Check XP of a user
```

Use `/help` for a full list of commands!

---

## **🌍 Contributing**
We welcome contributions from the community! If you'd like to help:
1. Fork the repository 🚀
2. Create a new branch (`git checkout -b feature-branch`)
3. Commit your changes (`git commit -m "Added a cool feature"`)
4. Push to your branch (`git push origin feature-branch`)
5. Open a [Pull Request](https://github.com/LewisProjects/Ogiroid/pulls)

Check out our [Contribution Guidelines](https://github.com/LewisProjects/Ogiroid/blob/development/CONTRIBUTING.md) for more details!

---

## **📜 Changelog**
### **📅 26-10-2024:**
- ✅ Custom role management through the bot
- ✅ Changed how levels are stored (Level + XP → total_xp)
- ✅ Added new commands to fix and assign level roles automatically
- ✅ Added `/xp` command

### **📅 29-12-2023:**
- 🔄 Migrated bot to PostgreSQL
- 🔄 Updated all SQL queries to use SQLAlchemy ORM
- 💰 Added Bitcoin command
- ⭐ Starboard fixes and enhancements
- 🛠 Lots of bug fixes
- 🖥 Started work on bot dashboard

---

## **💡 Contact & Support**
If you need help or have any questions, join our **Discord Support Server** (*link here*) or open an issue in the repository!

Happy coding! 🚀