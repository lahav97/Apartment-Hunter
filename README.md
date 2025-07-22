# 🏠 Apartment Hunter

**An intelligent apartment hunting bot for Israeli rental websites**

Automatically scrapes, filters, and notifies you about new apartments that match your exact criteria. Currently supports Yad2 with intelligent filtering and duplicate prevention.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 **What It Does**

**Apartment Hunter** is a smart scraping tool that:
- 🔍 **Searches Yad2** for rental apartments in your target neighborhoods  
- 📊 **Filters intelligently** by price, rooms, location, and keywords
- 💾 **Stores everything** in a local database with duplicate prevention
- 📱 **Sends notifications** when great apartments are found (Telegram support)
- 🧪 **Runs reliably** with comprehensive testing and error handling

**Perfect for:** Anyone hunting for apartments in Haifa who wants to automate the tedious process of constantly checking Yad2.

---

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.8 or higher
- Internet connection
- 10 minutes to set up

### **Installation**

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/apartment-hunter.git
cd apartment-hunter

# 2. Create and activate virtual environment
python -m venv venv

# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up database and configuration
python scripts/setup_db.py
cp config/filters.example.json config/filters.json
cp config/settings.example.json config/settings.json
```

### **First Run**

```bash
# Edit your search criteria (see Configuration section below)
# Then run a test scan:
python apartment_hunter.py scan
```

---

## ⚙️ **Configuration**

### **1. Set Your Search Criteria**

Edit `config/filters.json` with your apartment requirements:

```json
{
  "price_min": 2500,
  "price_max": 4000,
  "rooms_min": 2.5,
  "rooms_max": 3.5,
  "locations": ["בת גלים", "נווה שאנן", "רמות רמז", "רמות אלון"],
  "pets_allowed": true,
  "keywords_required": ["מרפסת"],
  "keywords_excluded": ["ללא חיות", "אסור חיות", "קומה גבוהה בלי מעלית"]
}
```

**Available neighborhoods for now:**
- בת גלים (Bat Galim)
- נווה שאנן (Neve Sha'anan)  
- רמות רמז (Ramot Remez)
- רמות אלון (Ramot Alon)

### **2. App Settings** 

Edit `config/settings.json`:

```json
{
  "interval_minutes": 30,
  "log_level": "INFO",
  "notify_limit": 5,
  "timeout_seconds": 10,
  "retry_attempts": 2
}
```

---

## 🖥️ **Usage**

### **Basic Commands**

```bash
# Run a single apartment scan
python apartment_hunter.py scan

# Test all components work correctly
python apartment_hunter.py test

# Run continuous hunting (scans every 30 minutes)
python apartment_hunter.py run

# Check database status and statistics
python apartment_hunter.py status
```

### **Alternative Entry Point**

```bash
# Using main.py (same as scan)
python main.py
```

### **Database Management**

```bash
# View current database status
python -c "from utils.database import quick_database_status; quick_database_status()"

# Clear all apartment data (fresh start)
python scripts/clear_db.py --clear-data --confirm

# Reset entire database
python scripts/setup_db.py --force
```

---

## 📊 **What You'll See**

### **Successful Scan Output:**
```
🔍 Starting apartment scan...
📡 Scraping Yad2...
🏠 Found 8 individual rental listings (filtered out projects/ads)
✅ Valid listing 1: 3 חדרים בבת גלים - ₪3,500 - 3.0 rooms
✅ Valid listing 2: דירה ברמות רמז - ₪2,800 - 2.5 rooms
💾 Database save results: {'inserted': 6, 'updated': 2, 'errors': 0}

📊 Results: 2 good apartments found!
```

### **Database Status:**
```
📊 Database Status: data/listings.db
==================================================
  📋 Total listings: 45
  📅 Added today: 8
  📈 Added this week: 23
  🔄 Scrape sessions: 12
  📊 By source: yad2: 45
  💰 Price range: ₪2,400 - ₪4,200
  📊 Average price: ₪3,250
==================================================
```

---

## 🧪 **Testing**

Make sure everything works correctly:

```bash
# Run all tests
python run_tests.py all

# Run specific test categories
python run_tests.py database    # Database operations
python run_tests.py scrapers    # Web scraping
python run_tests.py filters     # Filtering logic
```

**Expected result:**
```
🎯 Overall: 4/4 test suites passed
🎉 ALL TESTS PASSED! Your apartment hunter is ready! 🏠
```

---

## 📁 **Project Structure**

```
apartment-hunter/
├── 📂 config/                  # Your search settings
│   ├── filters.json            # Price, rooms, locations
│   ├── settings.json           # App configuration
│   └── neighborhoods.json      # Yad2 area mappings
├── 📂 data/                    # Database storage
│   └── listings.db             # Found apartments
├── 📂 scraper/                 # Web scraping logic
│   └── yad2_scraper.py         # Yad2 integration
├── 📂 filters/                 # Apartment filtering
│   └── rule_filter.py          # Your criteria matching
├── 📂 utils/                   # Core utilities
│   ├── database.py             # Data storage
│   └── logger.py               # Logging system
├── 📂 scripts/                 # Setup utilities
│   ├── setup_db.py             # Initialize database
│   └── clear_db.py             # Clean database
├── 📂 tests/                   # Test suite
├── apartment_hunter.py         # Main application
├── main.py                     # Simple entry point
└── requirements.txt           # Python dependencies
```

---

## 🔧 **How It Works**

### **1. Smart Scraping**
- Builds targeted search URLs for each neighborhood you want
- Handles Hebrew text extraction and price/room parsing
- Filters out project advertisements and keeps only real apartments

### **2. Intelligent Filtering**
- Only saves apartments matching your exact criteria
- Prevents duplicate listings using content-based hashing
- Validates data quality (realistic prices, proper room counts)
- Supports Hebrew keyword matching for descriptions

### **3. Reliable Storage**
- SQLite database stores all found apartments
- Tracks scraping sessions and performance statistics
- Supports complex searches across all saved listings
- Maintains data integrity with proper error handling

### **4. Notifications** (Optional)
- Telegram bot integration for instant alerts
- Only notifies about apartments passing ALL your filters
- Prevents duplicate notifications for same apartment

---

## 🐛 **Troubleshooting**

### **Common Issues**

**"No listings found"**
```bash
# Check if your criteria are too restrictive
python -c "
import json
with open('config/filters.json') as f: 
    print('Your filters:', json.load(f))
"

# Try broader price range or more neighborhoods temporarily
```

**"CAPTCHA detected" / No results**
```bash
# Yad2 is blocking requests - solutions:
# 1. Wait 30+ minutes before trying again
# 2. Reduce scraping frequency in settings.json
# 3. Check if your network/IP is temporarily blocked
```

**Import/Module errors**
```bash
# Make sure virtual environment is active
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

**Database errors**
```bash
# Reset database completely
python scripts/clear_db.py --clear-data --confirm
python scripts/setup_db.py
```

### **Getting Debug Information**

```bash
# Enable detailed logging
# Edit config/settings.json and change "log_level": "DEBUG"

# Check recent logs
tail -20 logs/apartment_hunter_*.log

# Run with test mode for detailed output
python apartment_hunter.py test
```

---

## ⚡ **Performance Tips**

### **Optimal Settings**
- **Scan frequency:** Every 30-60 minutes (avoid being blocked)
- **Price range:** Keep realistic (₪2000-₪6000 max)
- **Neighborhoods:** 2-4 areas work best
- **Keywords:** Use sparingly (2-3 max)

### **Resource Usage**
- **CPU:** Low (only during active scanning)  
- **Memory:** ~100MB typical usage
- **Storage:** ~50MB for 1000+ apartments
- **Network:** Minimal (respectful scraping)

---

## 🏠 **Start Your Apartment Hunt**

```bash
# Ready to find your dream apartment?
git clone https://github.com/yourusername/apartment-hunter.git
cd apartment-hunter
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python scripts/setup_db.py

# Edit config/filters.json with your criteria
# Then start hunting:
python apartment_hunter.py scan
```

**Good luck finding your perfect home! 🎉**