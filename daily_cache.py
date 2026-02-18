import os
import json
from datetime import datetime
from weekly_scraper import get_weekly_forecast  # use weekly scraper

# -------------------- CONFIG --------------------
CACHE_DIR = "cache/weekly_cache"
DISTRICTS_FILE = "cache/districts.json"
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DISTRICTS_FILE), exist_ok=True)


# -------------------- CACHE HANDLING --------------------
# -------------------- CACHE HANDLING --------------------
def cache_file_path(district: str):
    return os.path.join(CACHE_DIR, f"{district.lower()}_weekly.json")

def load_cache(district: str):
    path = cache_file_path(district)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_cache(district: str, data: dict):
    path = cache_file_path(district)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def clean_old_days(forecast_data):
    """Remove past days so the cache always starts from today."""
    today = datetime.now().date()
    new_data = []
    for table in forecast_data.get("data", []):
        table_date_str = table.get("date")
        if not table_date_str:
            continue
        try:
            table_date = datetime.strptime(table_date_str, "%A %d %B").replace(year=today.year).date()
        except:
            continue
        if table_date >= today:
            new_data.append(table)
    forecast_data["data"] = new_data
    return forecast_data



# -------------------- DISTRICT LIST HANDLING --------------------
def load_districts():
    if os.path.exists(DISTRICTS_FILE):
        with open(DISTRICTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_districts(districts):
    with open(DISTRICTS_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(set(districts)), f, indent=2)




# -------------------- FETCH DAILY FORECAST --------------------
def fetch_daily_forecast(district: str):
    """
    Fetch daily forecast for a district:
    - Return cache if exists
    - Otherwise fetch using weekly scraper, clean, save cache, then return
    """
    district_key = district.lower()

    # 🔴 ADD THIS BLOCK
    districts = load_districts()
    if district_key not in districts:
        districts.append(district_key)
        save_districts(districts)
    # 🔴 END ADD


    cache = load_cache(district_key)
    if cache:
        return cache

    try:
        # use weekly scraper for daily data
        forecast = get_weekly_forecast(district_key)
    except Exception:
        forecast = []

    if not forecast:
        return {"district": district.title(), "data": []}

    json_data = {
        "district": district.title(),
        "data": forecast
    }
    json_data = clean_old_days(json_data)
    save_cache(district_key, json_data)
    return json_data
