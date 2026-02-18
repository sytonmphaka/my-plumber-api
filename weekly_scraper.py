import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

def get_weekly_forecast(district: str):
    url = f"https://www.metmalawi.gov.mw/weather/daily-table/{district.lower()}/"
    response = requests.get(url, timeout=10)
    
    if response.status_code != 200:
        return {"error": f"Could not fetch data for {district}"}
    
    soup = BeautifulSoup(response.text, 'html.parser')
    tables = soup.find_all('table')
    
    if not tables:
        return {"error": "No forecast tables found"}
    
    weekly_forecast = []
    current_date = datetime.now()  # start from today
    
    for idx, table in enumerate(tables, start=1):
        headers = [th.text.strip() for th in table.find_all('th')]
        rows = table.find_all('tr')[1:]  # skip header
        
        table_rows = []
        for row in rows:
            cells = [td.text.strip() for td in row.find_all('td')]
            if len(cells) == len(headers):
                table_rows.append(dict(zip(headers, cells)))
        
        # assign date to this table
        table_date = current_date + timedelta(days=idx-1)
        formatted_date = table_date.strftime("%A %d %B")  # e.g., "Sunday 21 December"
        
        weekly_forecast.append({
            "date": formatted_date,
            "rows": table_rows
        })
    
    return weekly_forecast
