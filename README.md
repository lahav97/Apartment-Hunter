# 🏠 Apartment Hunter

An automated Python script that runs 24/7 and searches for rental apartments in Haifa (or any area you define). It scrapes real estate websites like Yad2, filters listings based on your custom criteria (price, rooms, location, pet-friendliness, etc.), and sends real-time alerts via Telegram.

Designed to run on a Raspberry Pi with **zero cost** and minimal setup.

## 📦 Features

- 🔍 Scrapes listings from sites like **Yad2** or **homeless**
- 🎯 Filters apartments by:
  - Price range
  - Number of rooms
  - Location (you define it in `filters.json`)
  - Pet-friendliness (for cats or dogs 🐾)
  - Optional keywords (e.g. “balcony”, “sea view”)
- 🤖 Optionally uses **OpenAI GPT** to semantically evaluate listings
- 📲 Sends instant alerts via **Telegram bot**
- 💾 Keeps track of already-seen listings
- 🛠️ Runs 24/7 on your Raspberry Pi, laptop, or cloud server

## 📁 Project Structure

apartment-hunter/
├── config/ # Filters, settings, and .env file
├── scraper/ # Yad2 scraping modules
├── filters/ # Rule-based & GPT-based filters
├── notifier/ # Telegram notifier module
├── models/ # Listing dataclass
├── utils/ # Logger, database, validators
├── scripts/ # Setup scripts (e.g. DB)
├── tests/ # Unit tests
├── main.py # Entry point
└── requirements.txt # Python dependencies