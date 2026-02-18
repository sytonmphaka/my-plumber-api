import os

# Base directory where forecast files are stored
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FORECAST_DIR = os.path.join(BASE_DIR, "metmalawi_forecasts")


def get_season_forecast(district: str) -> dict:
    """
    Read and return the full seasonal forecast for a district
    """

    # Normalize district name (Zomba → ZOMBA.txt)
    filename = f"{district.upper()}.txt"
    file_path = os.path.join(FORECAST_DIR, filename)

    if not os.path.exists(file_path):
        return {
            "status": "error",
            "message": f"Seasonal forecast for '{district}' not found"
        }

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        return {
            "status": "success",
            "district": district.title(),
            "forecast": content
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
