import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

def get_daily_forecast(district: str):
    """
    Returns a list of daily forecasts for the week.
    Each item: {"date": "Sunday 21 December", "rows": [...]}
    """
    url = f"https://www.metmalawi.gov.mw/weather/daily-table/{district.lower()}/"
    response = requests.get(url, timeout=10)
    if response.status_code != 200:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    tables = soup.find_all("table")
    if not tables:
        return []

    forecast_list = []
    today = datetime.now()

    for idx, table in enumerate(tables, start=1):
        headers = [th.text.strip() for th in table.find_all("th")]
        rows = table.find_all("tr")[1:]  # skip header

        table_rows = []
        for row in rows:
            cells = [td.text.strip() for td in row.find_all("td")]
            if len(cells) == len(headers):
                table_rows.append(dict(zip(headers, cells)))

        table_date = today + timedelta(days=idx-1)
        formatted_date = table_date.strftime("%A %d %B")

        forecast_list.append({
            "date": formatted_date,
            "rows": table_rows
        })

    return forecast_list
