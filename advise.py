from datetime import date

# IMPORT EXISTING FILES
from seasonforecast import get_season_forecast
from crop_summary import get_crop_summary


def parse_forecast_signals(forecast_text: str):
    text = forecast_text.lower()
    signals = {}

    # Onset
    if "last week of november" in text:
        signals["onset_month"] = 11
    elif "mid-december" in text:
        signals["onset_month"] = 12

    # Cessation
    if "early april" in text:
        signals["cessation_month"] = 4
    elif "last week of march" in text:
        signals["cessation_month"] = 3

    # Monthly rainfall signals
    signals["jan_rain"] = "high" if "january" in text and "300" in text else "normal"
    signals["feb_dry_risk"] = "high" if "february" in text and "dry spells" in text else "normal"

    return signals


def parse_crop_signals(crop_paragraph: str):
    text = crop_paragraph.lower()
    signals = {}

    # Growth duration
    if "reaching harvest maturity within" in text:
        try:
            parts = text.split("reaching harvest maturity within")[1].split("days")[0].strip()
            min_days, max_days = map(float, parts.replace("–","-").split("-"))
            signals["min_days"] = int(min_days)
            signals["max_days"] = int(max_days)
        except:
            signals["min_days"] = 50
            signals["max_days"] = 180

    # Waterlogging tolerance
    signals["waterlogging"] = "low" if "does not tolerate" in text and "waterlogged" in text else "medium"

    # Dry spell tolerance (implied)
    signals["dry_spell"] = "medium" if "can survive" in text else "low"

    return signals


def generate_advice(crop_name: str, district: str):
    today = date.today()

    # --- Load data ---
    forecast_data = get_season_forecast(district)
    if forecast_data["status"] != "success":
        return forecast_data["message"]

    crop_paragraph = get_crop_summary(crop_name)
    if crop_paragraph.startswith("Crop not found"):
        return crop_paragraph

    forecast_text = forecast_data["forecast"]

    # --- Parse signals ---
    f = parse_forecast_signals(forecast_text)
    c = parse_crop_signals(crop_paragraph)

    onset = f.get("onset_month", 12)
    cessation = f.get("cessation_month", 3)

    # --- Season position ---
    in_season = onset <= today.month <= cessation

    # --- Remaining season vs crop growth ---
    remaining_days = max(0, (cessation - today.month) * 30)
    duration_ok = remaining_days >= c["min_days"]

    # --- Intended planting month (for advice clarity) ---
    intended_planting_month = onset
    intended_planting_text = date(today.year, intended_planting_month, 1).strftime("%B")

    # --- Establishment & mid-season ---
    establishment = (
        "management-sensitive"
        if f["jan_rain"] == "high" and c["waterlogging"] == "low"
        else "favorable"
    )

    midseason = (
        "conditional"
        if f["feb_dry_risk"] == "high" and c["dry_spell"] == "low"
        else "manageable"
    )

    # --- Harvest ---
    harvest_month = today.month + (c["min_days"] // 30)
    harvest_within_season = harvest_month <= cessation

    # --- Paragraphs ---
    paragraphs = []

    # Paragraph 1: Season start info
    if in_season:
        paragraphs.append(
            f"As of {today.strftime('%d %B %Y')}, {district.title()} District is within "
            f"the ongoing rainfall season, which was expected to start around {intended_planting_text}. "
            f"Farmers who have not yet planted may still attempt planting, but careful planning is required."
        )
    else:
        paragraphs.append(
            f"As of {today.strftime('%d %B %Y')}, the rainfall season in {district.title()} District does not "
            f"currently support rain-fed planting. Optimal planting would have started around {intended_planting_text}."
        )

    # Paragraph 2: Remaining season vs crop
    if duration_ok:
        paragraphs.append(
            f"The remaining length of the rainfall season is sufficient to support the "
            f"full growth cycle of {crop_name.title()}, provided planting is done without further delay."
        )
    else:
        paragraphs.append(
            f"The remaining rainfall season is too short to reliably support the full "
            f"growth cycle of {crop_name.title()}, making production under rain-fed conditions high risk."
        )

    # Paragraph 3: Establishment conditions
    if establishment == "management-sensitive":
        paragraphs.append(
            f"Current rainfall conditions favor early crop establishment but also increase "
            f"the risk of waterlogging. Successful production will depend on proper field "
            f"selection, good drainage, or the use of raised ridges."
        )
    else:
        paragraphs.append(
            f"Forecasted conditions during the establishment phase are generally favorable, "
            f"supporting rapid germination and early growth of {crop_name.title()}."
        )

    # Paragraph 4: Mid-season risk
    if midseason == "conditional":
        paragraphs.append(
            f"The seasonal forecast indicates a likelihood of dry spells during critical growth stages. "
            f"Crop performance will depend on early establishment, soil fertility, and moisture conservation practices."
        )
    else:
        paragraphs.append(
            f"Mid-season rainfall patterns are expected to adequately support vegetative growth and yield development "
            f"for {crop_name.title()}."
        )

    # Paragraph 5: Harvest
    if harvest_within_season:
        paragraphs.append(
            f"Harvesting is expected to occur within the active rainfall season, allowing the crop to mature under forecast-supported moisture conditions."
        )
    else:
        paragraphs.append(
            f"Harvesting is likely to extend beyond the end of the rainfall season, meaning that supplementary irrigation would be required to sustain production."
        )

    # Paragraph 6: Overall recommendation
    if in_season and duration_ok and harvest_within_season:
        paragraphs.append(
            f"Overall, the seasonal forecast supports the production of {crop_name.title()} in {district.title()} District "
            f"if planting is done promptly and good agronomic practices are followed."
        )
    else:
        paragraphs.append(
            f"Overall, production of {crop_name.title()} under the current seasonal conditions carries elevated risk "
            f"and should be carefully evaluated before proceeding."
        )

    return "\n\n".join(paragraphs)


# ----------------- LOCAL TEST -----------------
if __name__ == "__main__":
    print(generate_advice("maize", "zomba"))
