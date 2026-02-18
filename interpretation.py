from datetime import datetime
import re

def parse_temperature(temp_str):
    try:
        return float(temp_str.replace("°C", "").strip())
    except:
        return None

def parse_rainfall(rain_str):
    try:
        return float(rain_str.replace("mm", "").strip())
    except:
        return 0.0

def parse_wind(wind_str):
    try:
        return float(wind_str.strip())
    except:
        return 0.0

# --- Monday rules ---
def temp_description(max_temp, min_temp):
    if max_temp >= 30:
        temp_desc = "very hot"
    elif max_temp >= 25:
        temp_desc = "hot"
    elif max_temp >= 20:
        temp_desc = "warm"
    else:
        temp_desc = "cool"
    return f"{temp_desc} with temperatures from {min_temp:.1f} to {max_temp:.1f}"

def rainfall_description(total_rain):
    if total_rain <= 0.3:
        return "almost no rainfall, making it suitable for fieldwork"
    elif total_rain <= 5:
        return "light rain in some hours, slightly wetting the soil"
    elif total_rain <= 10:
        return "moderate rain, soil will stay moist"
    else:
        return "heavy rain; fields may be waterlogged"

def wind_description(max_wind):
    if max_wind <= 5:
        return "very light winds"
    elif max_wind <= 15:
        return "moderate winds"
    else:
        return "strong winds; take precautions"

# Standard time blocks
time_blocks = {
    "Early morning": range(0, 6),
    "Morning": range(6, 12),
    "Noon": range(12, 15),
    "Afternoon": range(15, 18),
    "Evening": range(18, 21),
    "Night": range(21, 24)
}

def generate_daily_paragraph(day_data):
    date = day_data.get("date")
    rows = day_data.get("rows", [])
    paragraph = f"{date}:\n"  # removed ** for bold

    available_hours = []
    for r in rows:
        time_str = r.get("Time", "")
        if ":" in time_str:
            hour = int(time_str.split(":")[0])
            available_hours.append(hour)
    if not available_hours:
        return paragraph.strip()

    start_hour = min(available_hours)
    end_hour = max(available_hours)

    for block_name, hours in time_blocks.items():
        block_hours = [h for h in hours if start_hour <= h <= end_hour]
        if not block_hours:
            continue

        temps = []
        min_temps = []
        rainfalls = []
        winds = []

        for idx, r in enumerate(rows):
            time_str = r.get("Time", "")
            if ":" not in time_str:
                continue
            hour = int(time_str.split(":")[0])
            if hour in block_hours:
                t_max = parse_temperature(r.get("Max Temp",""))
                t_min = parse_temperature(r.get("Min Temp",""))
                rain = parse_rainfall(r.get("Rainfall",""))
                wind = parse_wind(r.get("Wind Speed",""))

                if t_max is not None:
                    temps.append(t_max)
                if t_min is not None:
                    min_temps.append(t_min)
                rainfalls.append(rain)
                winds.append(wind)

        if temps:
            max_temp_block = max(temps)
            min_temp_block = min(min_temps)
            total_rain = sum(rainfalls)
            max_wind_block = max(winds)

            temp_text = temp_description(max_temp_block, min_temp_block)
            rain_text = rainfall_description(total_rain)
            wind_text = wind_description(max_wind_block)

            if total_rain <= 0.3 and max_wind_block <= 5:
                advice = "Good day for fieldwork, planting, or crop maintenance."
            elif total_rain > 10 or max_wind_block > 15:
                advice = "Fieldwork may be difficult due to wet soil or strong winds. Delay activities."
            else:
                advice = "Plan field activities carefully; avoid spraying during rainy or windy periods."

            paragraph += f"{block_name}: {temp_text}, {rain_text}, {wind_text}. {advice}\n"

    return paragraph.strip()

def generate_weekly_summary(weekly_json):
    paragraphs = []
    for day in weekly_json.get("data", []):
        paragraphs.append(generate_daily_paragraph(day))
    summary = "\n\n".join(paragraphs)
    return clean_text(summary)  # remove all special characters

def clean_text(text):
    """
    Remove all special characters and extra spaces, keep letters, numbers, basic punctuation.
    """
    # Remove any Markdown-style formatting
    text = re.sub(r'[*_]+', '', text)
    # Remove degree symbols or other unwanted special chars
    text = re.sub(r'[^\w\s.,:;!?]', '', text)
    # Collapse multiple spaces/newlines into single space
    text = re.sub(r'\s+', ' ', text).strip()
    return text
